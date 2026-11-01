"""Android-side manual sync client for the authenticated ResiManage API.
The bearer token is supplied by the native bridge and is never persisted here.
"""
import hashlib
import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import ssl
import certifi
import app as resimanage


class SyncError(RuntimeError):
    pass


_SYNC_CA_FILE = None


def _ssl_context():
    context = ssl.create_default_context(cafile=certifi.where())
    if _SYNC_CA_FILE:
        context.load_verify_locations(cafile=_SYNC_CA_FILE)
    return context


def _configure_ca(data_directory, ca_certificate_pem):
    global _SYNC_CA_FILE
    pem = str(ca_certificate_pem or "").strip()
    if not pem:
        _SYNC_CA_FILE = None
        return None
    if len(pem) > 65536 or "-----BEGIN CERTIFICATE-----" not in pem or "-----END CERTIFICATE-----" not in pem:
        raise SyncError("Private CA certificate must be PEM encoded and no larger than 64 KB.")
    os.makedirs(data_directory, exist_ok=True)
    path = os.path.join(data_directory, "resimanage_sync_ca.pem")
    temporary = path + ".tmp"
    try:
        with open(temporary, "w", encoding="ascii", newline="\n") as handle:
            handle.write(pem + "\n")
        context = ssl.create_default_context(cafile=certifi.where())
        context.load_verify_locations(cafile=temporary)
        os.replace(temporary, path)
    except Exception as exc:
        for candidate in (temporary, path):
            try:
                os.remove(candidate)
            except OSError:
                pass
        raise SyncError("Invalid private CA certificate PEM: " + str(exc)) from exc
    _SYNC_CA_FILE = path
    return path


def _api(base_url, token, path, body=None):
    url = base_url.rstrip("/") + path
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise SyncError("Sync response exceeded the 2 MB safety limit.")
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", "replace")
        try:
            detail = json.loads(detail)
        except Exception:
            pass
        raise SyncError("Sync server returned HTTP %s: %s" % (exc.code, detail)) from exc
    except urllib.error.URLError as exc:
        raise SyncError("Cannot reach sync server. Check VPN, address and trusted TLS certificate: %s" % exc.reason) from exc


def _validate_config(base_url, token):
    parsed = urllib.parse.urlparse(str(base_url or "").strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SyncError("Use the HTTPS origin of the central ResiManage server.")
    if parsed.path not in ("", "/"):
        raise SyncError("Enter only the server origin, e.g. https://vpn-ip:5000.")
    token = str(token or "").strip()
    if len(token) < 32 or len(token) > 256:
        raise SyncError("The bearer token is missing or has an invalid length.")
    return parsed.geturl().rstrip("/"), token


def _set_setting(conn, key, value):
    conn.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def _setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default



def _api_bytes(base_url, token, path):
    req = urllib.request.Request(base_url.rstrip("/") + path,
        headers={"Accept": "image/*", "Authorization": "Bearer " + token}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
            if not raw or len(raw) > 4 * 1024 * 1024:
                raise SyncError("Synced photo is empty or exceeds 4 MB.")
            return raw, response.headers.get_content_type()
    except urllib.error.HTTPError as exc:
        raise SyncError("Photo download failed (HTTP %s): %s" % (exc.code, exc.read(2048).decode("utf-8", "replace"))) from exc
    except urllib.error.URLError as exc:
        raise SyncError("Cannot download resident photo: %s" % exc.reason) from exc


def _api_put_bytes(base_url, token, path, raw, content_type):
    req = urllib.request.Request(base_url.rstrip("/") + path, data=raw,
        headers={"Authorization": "Bearer " + token, "Content-Type": content_type, "Accept": "application/json"},
        method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as response:
            return json.loads(response.read(65536).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SyncError("Photo upload failed (HTTP %s): %s" % (exc.code, exc.read(4096).decode("utf-8", "replace"))) from exc
    except urllib.error.URLError as exc:
        raise SyncError("Cannot upload resident photo: %s" % exc.reason) from exc

def _apply_remote_batch(conn, changes, base_url, token, data_directory):
    # Download photos before taking the SQLite write lock, then map the path to local storage.
    photo_dir = os.path.join(data_directory, "resident_photos")
    for change in changes:
        if change.get("entity") == "residents" and change.get("operation") == "upsert":
            payload = change.get("payload") or {}
            if payload.get("photo_path"):
                raw, mime = _api_bytes(base_url, token, "/api/sync/v1/photo/" + str(change["entity_id"]))
                ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(mime)
                if not ext:
                    raise SyncError("Unsupported central photo MIME type: " + str(mime))
                os.makedirs(photo_dir, exist_ok=True)
                filename = "resident_" + str(change["entity_id"]) + "_sync_" + str(change["seq"]) + ext
                with open(os.path.join(photo_dir, filename), "wb") as handle:
                    handle.write(raw)
                payload = dict(payload)
                payload["photo_path"] = "/photos/" + filename
                change["payload"] = payload

    # Lock writes while suppressing journal triggers so pulled rows do not echo back as local edits.
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("UPDATE sync_control SET suppress_log=1 WHERE id=1")
        for change in changes:
            entity = change["entity"]
            entity_id = str(change["entity_id"])
            if entity not in resimanage._SYNC_ENTITY_FIELDS:
                raise SyncError("Server sent unsupported entity: " + str(entity))
            if change["operation"] == "delete":
                conn.execute('DELETE FROM "' + entity + '" WHERE id=?', (int(entity_id),))
            elif change["operation"] == "upsert":
                payload = change.get("payload")
                fields = resimanage._SYNC_ENTITY_FIELDS[entity]
                if not isinstance(payload, dict) or set(payload) != set(fields) or str(payload.get("id")) != entity_id:
                    raise SyncError("Malformed server row for %s/%s." % (entity, entity_id))
                columns = ", ".join('"' + field + '"' for field in fields)
                marks = ", ".join("?" for _ in fields)
                conn.execute(
                    'INSERT OR REPLACE INTO "' + entity + '" (' + columns + ") VALUES (" + marks + ")",
                    tuple(payload[field] for field in fields),
                )
            else:
                raise SyncError("Unknown sync operation: " + str(change["operation"]))
            conn.execute(
                "INSERT INTO sync_row_versions(entity,entity_id,server_seq) VALUES(?,?,?) "
                "ON CONFLICT(entity,entity_id) DO UPDATE SET server_seq=excluded.server_seq",
                (entity, entity_id, int(change["seq"])),
            )
        conn.execute("UPDATE sync_control SET suppress_log=0 WHERE id=1")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _bootstrap_empty_device(conn, base_url, token, server_cursor, data_directory):
    # Independent integer-ID databases cannot be safely merged yet; first pairing requires no resident data.
    # These entities may contain local user-entered data even when no resident rows
    # exist. Bootstrap uses central integer IDs and upserts rows, so silently applying
    # it over any of these tables could overwrite local capacities, objectives, votes,
    # decisions, archive records, leave entitlements or audit history.
    protected_tables = (
        "residents", "assignments", "history", "exam_records",
        "leave_entries", "external_rotations", "capacities", "objectives",
        "decisions", "dems_archive", "promotion_votes", "dems_votes",
        "leave_years", "audit",
    )
    for table in protected_tables:
        if conn.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0]:
            raise SyncError(
                "Initial pairing requires an empty device data database (except seeded "
                "terrains/periods and account/settings tables) to avoid overwriting local "
                "records. Back up/export this device first."
            )
    for entity in sorted(resimanage._SYNC_ENTITY_FIELDS):
        after_id = 0
        while True:
            query = urllib.parse.urlencode({"entity": entity, "after_id": after_id, "limit": 300})
            page = _api(base_url, token, "/api/sync/v1/bootstrap?" + query)
            rows = page.get("rows", [])
            if rows:
                changes = [{
                    "seq": int(server_cursor), "entity": entity, "entity_id": str(row["id"]),
                    "operation": "upsert", "payload": row,
                } for row in rows]
                _apply_remote_batch(conn, changes, base_url, token, data_directory)
                after_id = int(page.get("next_id", after_id))
            if not page.get("has_more"):
                break
    _set_setting(conn, "resimanage_sync_remote_cursor", server_cursor)
    _set_setting(conn, "resimanage_sync_outbox_cursor",
                 conn.execute("SELECT COALESCE(MAX(seq),0) FROM sync_change_log").fetchone()[0])
    conn.commit()


def _pull_all(conn, base_url, token, cursor, data_directory):
    total = 0
    while True:
        query = urllib.parse.urlencode({"after_seq": cursor, "limit": 300})
        page = _api(base_url, token, "/api/sync/v1/pull?" + query)
        changes = page.get("changes", [])
        if not changes:
            break
        _apply_remote_batch(conn, changes, base_url, token, data_directory)
        cursor = int(page.get("next_seq", cursor))
        _set_setting(conn, "resimanage_sync_remote_cursor", cursor)
        conn.commit()
        total += len(changes)
        if not page.get("has_more"):
            break
    return cursor, total


def _push_local_changes(conn, base_url, token, device_id, remote_cursor, data_directory):
    outbox_cursor = int(_setting(conn, "resimanage_sync_outbox_cursor", "0") or 0)
    rows = conn.execute(
        "SELECT seq,entity,entity_id,operation,payload_json,base_seq FROM sync_change_log WHERE seq>? ORDER BY seq",
        (outbox_cursor,),
    ).fetchall()
    if not rows:
        return {"pushed": 0, "skipped_entities": []}
    # Coalesce each row to its latest local state, preserving the base version captured by its trigger.
    latest = {}
    skipped = set()
    for row in rows:
        key = (row["entity"], row["entity_id"])
        if row["entity"] not in resimanage._SYNC_PUSH_ENTITIES:
            skipped.add(row["entity"])
            continue
        latest[key] = row
    operations = []
    photo_uploads = {}
    skipped_photos = []
    for row in latest.values():
        local_seq = int(row["seq"])
        op_id = hashlib.sha256((device_id + ":" + str(local_seq)).encode("utf-8")).hexdigest()[:40]
        payload = json.loads(row["payload_json"]) if row["operation"] == "upsert" else None
        if row["entity"] == "residents" and isinstance(payload, dict) and payload.get("photo_path"):
            filename = os.path.basename(str(payload["photo_path"]))
            ext = os.path.splitext(filename)[1].lower()
            local_photo = os.path.join(data_directory, "resident_photos", filename)
            if filename.startswith("resident_") and ext in (".png", ".jpg", ".jpeg", ".webp") and os.path.isfile(local_photo):
                photo_uploads[op_id] = (local_photo, ext)
                payload["photo_path"] = ""
            elif int(row["base_seq"] or 0) == 0:
                payload["photo_path"] = ""
                skipped_photos.append(str(row["entity_id"]))
        operations.append({
            "op_id": op_id, "entity": row["entity"], "entity_id": str(row["entity_id"]),
            "operation": row["operation"], "base_seq": int(row["base_seq"] or 0),
            "payload": payload,
        })
    pushed = 0
    for offset in range(0, len(operations), 80):
        result = _api(base_url, token, "/api/sync/v1/push", {"operations": operations[offset:offset + 80]})
        outcomes = result.get("results", [])
        conflicts = [item for item in outcomes if item.get("status") == "conflict"]
        rejected = [item for item in outcomes if item.get("status") == "rejected"]
        if conflicts or rejected:
            raise SyncError(json.dumps({
                "message": "Some local changes need conflict/rejection review and remain queued.",
                "conflicts": conflicts, "rejected": rejected, "skipped_entities": sorted(skipped),
            }, ensure_ascii=False))
        for item in outcomes:
            if item.get("status") != "applied" and not item.get("replayed"):
                raise SyncError("Unexpected sync push response: " + json.dumps(item))
            pushed += 1
            original = next((op for op in operations if op["op_id"] == item.get("op_id")), None)
            if original:
                entity_seq = int(item.get("server_seq", remote_cursor))
                conn.execute(
                    "INSERT INTO sync_row_versions(entity,entity_id,server_seq) VALUES(?,?,?) "
                    "ON CONFLICT(entity,entity_id) DO UPDATE SET server_seq=excluded.server_seq",
                    (original["entity"], original["entity_id"], entity_seq),
                )
                if item.get("status") == "applied" and item["op_id"] in photo_uploads:
                    # Close the row-version transaction before network I/O.
                    # The photo update is saved in a separate short transaction below.
                    conn.commit()
                    local_photo, ext = photo_uploads[item["op_id"]]
                    mime = {".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"}[ext]
                    with open(local_photo, "rb") as photo_handle:
                        photo_result = _api_put_bytes(
                            base_url, token,
                            "/api/sync/v1/photo/" + original["entity_id"] + "?base_seq=" + str(entity_seq),
                            photo_handle.read(4 * 1024 * 1024 + 1), mime,
                        )
                    if not photo_result.get("ok"):
                        raise SyncError("Central server did not accept resident photo " + original["entity_id"])
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute("UPDATE sync_control SET suppress_log=1 WHERE id=1")
                    conn.execute("UPDATE residents SET photo_path=? WHERE id=?",
                                 ("/photos/" + os.path.basename(local_photo), int(original["entity_id"])))
                    conn.execute("INSERT INTO sync_row_versions(entity,entity_id,server_seq) VALUES('residents',?,?) "
                                 "ON CONFLICT(entity,entity_id) DO UPDATE SET server_seq=excluded.server_seq",
                                 (original["entity_id"], int(photo_result["server_seq"])))
                    conn.execute("UPDATE sync_control SET suppress_log=0 WHERE id=1")
                    conn.commit()
    _set_setting(conn, "resimanage_sync_outbox_cursor", int(rows[-1]["seq"]))
    conn.commit()
    return {"pushed": pushed, "skipped_entities": sorted(skipped), "skipped_photos": sorted(set(skipped_photos))}


def sync_once(data_directory, base_url, token, ca_certificate_pem=""):
    """Run one manual sync and return a JSON result string to the native Android bridge."""
    conn = None
    try:
        base_url, token = _validate_config(base_url, token)
        _configure_ca(data_directory, ca_certificate_pem)
        conn = sqlite3.connect(os.path.join(data_directory, "rotation.db"), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("SELECT seq,base_seq FROM sync_change_log LIMIT 1").fetchall()
        conn.execute("SELECT server_seq FROM sync_row_versions LIMIT 1").fetchall()
        status = _api(base_url, token, "/api/sync/v1/status")
        if int(status.get("api_version", 0)) != 1:
            raise SyncError("Unsupported sync API version.")
        device_id = status["device_id"]
        saved_cursor = _setting(conn, "resimanage_sync_remote_cursor")
        if saved_cursor is None:
            cursor = int(status.get("server_cursor", 0))
            _bootstrap_empty_device(conn, base_url, token, cursor, data_directory)
            # Catch server changes committed while the paged snapshot was being downloaded.
            cursor, pulled = _pull_all(conn, base_url, token, cursor, data_directory)
        else:
            cursor, pulled = _pull_all(conn, base_url, token, int(saved_cursor), data_directory)
        push_result = {"pushed": 0, "skipped_entities": [], "skipped_photos": []}
        if status.get("push_enabled"):
            push_result = _push_local_changes(conn, base_url, token, device_id, cursor, data_directory)
        warnings = []
        if push_result["skipped_entities"]:
            warnings.append("Not yet push-enabled: " + ", ".join(push_result["skipped_entities"]))
        if push_result.get("skipped_photos"):
            warnings.append("Local photo files missing for resident IDs: " + ", ".join(push_result["skipped_photos"]))
        return json.dumps({
            "ok": True, "device_id": device_id, "pulled": pulled,
            "pushed": push_result["pushed"], "skipped_entities": push_result["skipped_entities"],
            "skipped_photos": push_result.get("skipped_photos", []), "remote_cursor": cursor,
            "message": "Sync finished." if not warnings else "Sync finished with warnings: " + "; ".join(warnings),
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        if conn is not None:
            conn.close()
