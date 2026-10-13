# rotation-app

Resident rotation management app for CHU Nedir Mohamed — Flask/SQLite with an Android WebView wrapper.

## Documentation

- [Instructions en arabe pour Termux, sauvegardes et usage](README_AR.txt)
- [Android build and installation guide](android/README.md)
- [Resident and documented-stage import template](docs/resident_import_template.md)

## Development checks

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check --select E9,F63,F7,F82 app.py tests
python -m pytest -q
```

The automated tests use temporary SQLite databases. Do not commit `rotation.db`, database backups, resident photos, passwords, tokens, or environment secrets.

## Android APK

The GitHub Actions workflow **Android APK build** builds a debug APK and uploads the `rotation-app-debug-apk` artifact. The APK includes 64-bit ARM (`arm64-v8a`) and x86_64 libraries. The CI build succeeds, but emulator startup was not reliably confirmed and the APK has not yet been tested on a physical phone. It is not a Play Store release.

## Security and data

- New databases prompt the administrator to create a password of at least 12 characters.
- Existing legacy SHA-256 password hashes are upgraded after successful login.
- POST forms require CSRF tokens.
- Set `ROTATION_SECRET` through the runtime environment for a stable secret key outside the Android wrapper; never commit it.
- The database, backups, and `uploads/` are excluded from Git.
- Review the official curriculum and test backup restoration before using real resident records.
