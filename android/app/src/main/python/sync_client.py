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
import app as resimanage


class SyncError(RuntimeError):
    pass


def _api(base_url, token, path, body=None):
    url = base_url.rstrip("/") + path
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
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


def _apply_remote_batch(conn, changes):
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


def _bootstrap_empty_device(conn, base_url, token, server_cursor):
    # Independent integer-ID databases cannot be safely merged yet; first pairing requires no resident data.
    for table in ("residents", "assignments", "history", "exam_records", "leave_entries", "external_rotations"):
        if conn.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0]:
            raise SyncError("Initial pairing requires an empty device database to avoid ID collisions. Back up/export this device first.")
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
                _apply_remote_batch(conn, changes)
                after_id = int(page.get("next_id", after_id))
            if not page.get("has_more"):
                break
    _set_setting(conn, "resimanage_sync_remote_cursor", server_cursor)
    _set_setting(conn, "resimanage_sync_outbox_cursor",
                 conn.execute("SELECT COALESCE(MAX(seq),0) FROM sync_change_log").fetchone()[0])
    conn.commit()


def _pull_all(conn, base_url, token, cursor):
    total = 0
    while True:
        query = urllib.parse.urlencode({"after_seq": cursor, "limit": 300})
        page = _api(base_url, token, "/api/sync/v1/pull?" + query)
        changes = page.get("changes", [])
        if not changes:
            break
        _apply_remote_batch(conn, changes)
        cursor = int(page.get("next_seq", cursor))
        _set_setting(conn, "resimanage_sync_remote_cursor", cursor)
        conn.commit()
        total += len(changes)
        if not page.get("has_more"):
            break
    return cursor, total


def _push_local_changes(conn, base_url, token, device_id, remote_cursor):
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
    for row in latest.values():
        local_seq = int(row["seq"])
        op_id = hashlib.sha256((device_id + ":" + str(local_seq)).encode("utf-8")).hexdigest()[:40]
        operations.append({
            "op_id": op_id, "entity": row["entity"], "entity_id": str(row["entity_id"]),
            "operation": row["operation"], "base_seq": int(row["base_seq"] or 0),
            "payload": json.loads(row["payload_json"]) if row["operation"] == "upsert" else None,
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
                conn.execute(
                    "INSERT INTO sync_row_versions(entity,entity_id,server_seq) VALUES(?,?,?) "
                    "ON CONFLICT(entity,entity_id) DO UPDATE SET server_seq=excluded.server_seq",
                    (original["entity"], original["entity_id"], int(item.get("server_seq", remote_cursor))),
                )
    _set_setting(conn, "resimanage_sync_outbox_cursor", int(rows[-1]["seq"]))
    conn.commit()
    return {"pushed": pushed, "skipped_entities": sorted(skipped)}


def sync_once(data_directory, base_url, token):
    """Run one manual sync and return a JSON result string to the native Android bridge."""
    conn = None
    try:
        base_url, token = _validate_config(base_url, token)
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
            _bootstrap_empty_device(conn, base_url, token, cursor)
            pulled = 0
        else:
            cursor, pulled = _pull_all(conn, base_url, token, int(saved_cursor))
        push_result = {"pushed": 0, "skipped_entities": []}
        if status.get("push_enabled"):
            push_result = _push_local_changes(conn, base_url, token, device_id, cursor)
        return json.dumps({
            "ok": True, "device_id": device_id, "pulled": pulled,
            "pushed": push_result["pushed"], "skipped_entities": push_result["skipped_entities"],
            "remote_cursor": cursor,
            "message": "Sync finished." if not push_result["skipped_entities"] else
                "Sync finished; some entity types are not yet push-enabled: " + ", ".join(push_result["skipped_entities"]),
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        if conn is not None:
            conn.close()
