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
- Resident import supports CSV, XLS/XLSX, DOCX, and text-based PDFs with preview/validation; legacy DOC needs antiword and scanned PDFs need OCR.
- Separate super-admin/operator accounts, resident profiles/photos/exams, two-official promotion decisions, and the DEMS archive are implemented on the candidate branch and covered by regression tests.
