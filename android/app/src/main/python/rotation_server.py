import os
import secrets


def start_server(data_directory):
    os.makedirs(data_directory, exist_ok=True)
    secret_path = os.path.join(data_directory, "rotation.secret")
    if not os.path.exists(secret_path):
        with open(secret_path, "w", encoding="utf-8") as secret_file:
            secret_file.write(secrets.token_hex(32))
    with open(secret_path, "r", encoding="utf-8") as secret_file:
        secret = secret_file.read().strip()

    os.environ["ROTATION_DATA_DIR"] = data_directory
    os.environ["ROTATION_SECRET"] = secret
    os.environ["ROTATION_COOKIE_SECURE"] = "0"

    import app as rotation_app

    rotation_app.DATA_DIR = data_directory
    rotation_app.DB = os.path.join(data_directory, "rotation.db")
    rotation_app.UPLOAD_DIR = os.path.join(data_directory, "uploads", "residents")
    rotation_app.app.config.update(
        SECRET_KEY=secret,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    rotation_app.app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True,
    )
