# Rotation App

Flask application for managing resident rotations, with Arabic/French/English UI and Arabic RTL.

## Local setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in the browser. On a new empty database, create the first administrator password on the login page. Existing `rotation.db` files and their histories must be preserved; do not delete or replace them when updating code.

## Current development branch

The prototype and automated tests are being developed on `prototype/verification-2026-10-13`; changes are not yet merged into `main`. Features in this branch include 19 seeded terrains, capacity and assignment rules, individual roles, resident profiles, exam progression, objectives, DEMS archive, validated resident-list import, CSV export, and backup/restore with a pre-restore safety copy.

The import preview supports CSV, XLS/XLSX, DOC/DOCX and text-based PDF. Legacy `.doc` files require `antiword` or LibreOffice. Scanned PDFs without extractable text need OCR before import. Imported lists never fabricate previous rotations.

Keep the local secret key, database, backups, uploaded resident photos, and personal data out of Git. GitHub Actions runs the automated test suite against isolated temporary databases.

## ملاحظة بالعربية

لا تحذف قاعدة البيانات `rotation.db` عند تحديث الكود. التطبيق ما زال في فرع التجربة ولم يُدمج بعد في `main`. قبل استرجاع نسخة احتياطية، ينشئ التطبيق نسخة من قاعدة البيانات الحالية.