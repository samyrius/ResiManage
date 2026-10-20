# -*- coding: utf-8 -*-
"""ResiManage desktop launcher: persistent per-user data + local WebView window."""
import os
import ipaddress
import secrets
import shutil
import socket
import sqlite3
import sys
import threading
from pathlib import Path

from werkzeug.serving import make_server


def _migrate_legacy_data(data_dir, legacy_root):
    """Copy old portable/install data once, without deleting the original."""
    if not legacy_root:
        return
    legacy_root = Path(legacy_root)
    target_db = data_dir / "rotation.db"
    legacy_db = legacy_root / "rotation.db"
    if not target_db.exists() and legacy_db.is_file():
        source = sqlite3.connect(str(legacy_db))
        target = sqlite3.connect(str(target_db))
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()

    legacy_photos = legacy_root / "resident_photos"
    target_photos = data_dir / "resident_photos"
    if legacy_photos.is_dir():
        for source_photo in legacy_photos.rglob("*"):
            if not source_photo.is_file():
                continue
            target_photo = target_photos / source_photo.relative_to(legacy_photos)
            if not target_photo.exists():
                target_photo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_photo, target_photo)


def _prepare_user_data():
    # Keep the database, photos, and signing secret outside the install directory:
    # an application upgrade must never replace user records.
    root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    data_dir = root / "ResiManage" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    legacy_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else None
    secret_path = data_dir / ".rotation_secret"
    if not secret_path.exists():
        legacy_secret = legacy_root / ".rotation_secret" if legacy_root else None
        if legacy_secret and legacy_secret.is_file():
            shutil.copy2(legacy_secret, secret_path)
        else:
            value = secrets.token_hex(32)
            try:
                fd = os.open(str(secret_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="ascii") as handle:
                    handle.write(value)
            except FileExistsError:
                pass
    secret = secret_path.read_text(encoding="ascii").strip()
    if len(secret) < 32:
        raise RuntimeError("ResiManage secret file is invalid; restore it from a trusted backup.")
    _migrate_legacy_data(data_dir, legacy_root)
    os.environ["ROTATION_SECRET"] = secret
    return data_dir


def _available_local_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _server_settings():
    """Resolve a safe bind target; remote/VPN listeners require explicit TLS."""
    host = os.environ.get("RESIMANAGE_BIND", "127.0.0.1").strip()
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise RuntimeError("RESIMANAGE_BIND must be an explicit IP address (use the VPN interface IP).") from exc
    if address.is_unspecified:
        raise RuntimeError("Wildcard binds (0.0.0.0/::) are disabled; bind only to the exact VPN IP.")

    cert = os.environ.get("RESIMANAGE_TLS_CERT", "").strip()
    key = os.environ.get("RESIMANAGE_TLS_KEY", "").strip()
    if bool(cert) != bool(key):
        raise RuntimeError("Configure both RESIMANAGE_TLS_CERT and RESIMANAGE_TLS_KEY.")
    ssl_context = (cert, key) if cert and key else None
    if not address.is_loopback and ssl_context is None:
        raise RuntimeError("A non-loopback ResiManage listener requires TLS certificate/key and a private VPN IP.")

    port_text = os.environ.get("RESIMANAGE_PORT", "").strip()
    if port_text:
        try:
            port = int(port_text)
        except ValueError as exc:
            raise RuntimeError("RESIMANAGE_PORT must be an integer.") from exc
        if not 1 <= port <= 65535:
            raise RuntimeError("RESIMANAGE_PORT must be between 1 and 65535.")
    else:
        port = 0 if address.is_loopback else 5000
    return host, port, ssl_context


def main():
    data_dir = _prepare_user_data()
    import app as resimanage

    resimanage.DB = str(data_dir / "rotation.db")
    resimanage.app.config.update(
        SECRET_KEY=os.environ["ROTATION_SECRET"],
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    resimanage.init()
    host, port, ssl_context = _server_settings()
    if port == 0:
        port = _available_local_port()
    server = make_server(host, port, resimanage.app, threaded=True, ssl_context=ssl_context)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    scheme = "https" if ssl_context else "http"
    url = f"{scheme}://{host}:{server.server_port}"

    try:
        import webview
        window = webview.create_window("ResiManage", url, width=1280, height=820, min_size=(900, 600))
        window.events.closed += lambda: server.shutdown()
        webview.start()
    except ImportError:
        import webbrowser
        webbrowser.open(url)
        thread.join()
    finally:
        if thread.is_alive():
            server.shutdown()


if __name__ == "__main__":
    main()
