# -*- coding: utf-8 -*-
"""ResiManage desktop launcher: persistent per-user data + local WebView window."""
import os
import secrets
import socket
import threading
from pathlib import Path

from werkzeug.serving import make_server


def _prepare_user_data():
    # Keep the database, photos, and signing secret outside the install directory:
    # an application upgrade must never replace user records.
    root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    data_dir = root / "ResiManage" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    secret_path = data_dir / ".rotation_secret"
    if not secret_path.exists():
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
    os.environ["ROTATION_SECRET"] = secret
    return data_dir


def _available_local_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


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
    port = _available_local_port()
    server = make_server("127.0.0.1", port, resimanage.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"

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
