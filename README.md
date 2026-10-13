# rotation-app

Gestion des stages des médecins résidents — Flask / SQLite.

## Documentation

- Instructions en arabe pour Termux et la sauvegarde des données : [README_AR.txt](README_AR.txt)
- The app is still under active development; review and test the rules before using it for official resident allocation.

## Development checks

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check --select E9,F63,F7,F82 app.py tests
python -m pytest -q
```

The automated tests use temporary SQLite databases. Do not commit `rotation.db`, database backups, passwords, tokens, or environment secrets.

## Security notes

- New databases prompt the administrator to create a password of at least 12 characters.
- Existing legacy SHA-256 password hashes are upgraded after successful login.
- POST forms require CSRF tokens.
- Set `ROTATION_SECRET` through the runtime environment for a stable secret key; never commit it.
- The current app still needs further implementation and validation for separate administrator accounts, resident profiles/photos/exams, bulk import, and the DEMS archive.
