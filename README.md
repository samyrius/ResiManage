# ResiManage

ResiManage is the resident rotation management application (formerly titled Rotation App in parts of the codebase). The interface supports Arabic, French, and English, with right-to-left layout for Arabic. The current 3D doctor/stethoscope image is `static/resimanage-3d-icon.jpg` and is used for the in-app brand and browser favicon; the Android launcher uses the same artwork.

Flask application for managing resident rotations, with Arabic/French/English UI and Arabic RTL.

## Local setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in the browser. On a new empty database, create the first administrator password on the login page. Existing `rotation.db` files and their histories must be preserved; do not delete or replace them when updating code.

## Try ResiManage 2 in a browser (GitHub Codespaces)

For a disposable test environment, open [Create a Codespace on resimanage-2-work](https://github.com/codespaces/new?repo=samyrius/ResiManage&ref=resimanage-2-work). Codespaces may ask you to sign in and confirm available quota/billing before creating the environment. The devcontainer installs the Python requirements and starts the Flask app on port 5000.

This Codespace creates its own ignored `rotation.db` and `.rotation_secret`; it does not copy your phone's database or modify ResiManage 1. On first open, create a test administrator password. Use only fictional test residents in this environment. To view startup errors, inspect `/tmp/resimanage-demo.log` in the Codespace terminal. Do not enable public port access for real resident data.

## Current development branch

**Active source of truth for ResiManage 2: `resimanage-2-work`.** Apply current corrections to this branch. Treat the older ResiManage copy as a backup and do not move work to `main` or another branch unless explicitly requested. The earlier changes from `prototype/verification-2026-10-13` were merged into `main` through PR #8 (merge commit `52127b58aa1bcc7f86f320c34f7de35f0c63922e`); that is historical context, not the active working baseline. The application includes 19 seeded terrains, capacity and assignment rules, individual roles, resident profiles, exam progression, objectives, DEMS archive, validated resident-list import, CSV export, and backup/restore with a pre-restore safety copy.

The import preview supports CSV, XLS/XLSX, DOC/DOCX and text-based PDF. Legacy `.doc` files require `antiword` or LibreOffice. Scanned PDFs without extractable text need OCR before import. Imported lists never fabricate previous rotations.

Keep the local secret key, database, backups, uploaded resident photos, and personal data out of Git. Python regression checks use isolated temporary databases. Android APK build and emulator verification workflows are manual-only until all directives are implemented; do not claim a successful build or test without a recorded run result.

## ملاحظة بالعربية

الفرع النشط للعمل على ResiManage 2 هو `resimanage-2-work`؛ لا تعدّل `main` أو النسخة الاحتياطية بدلًا منه. لا تحذف قاعدة البيانات `rotation.db` عند تحديث الكود. نتيجة الاختبارات القديمة على `main` معلومة تاريخية ولا تعني أن التعديلات الحالية قد اختُبرت. قبل استرجاع نسخة احتياطية، ينشئ التطبيق نسخة من قاعدة البيانات الحالية.
## Windows data safety

ResiManage 2 keeps its Windows database, resident photos, and session-signing secret in `%LOCALAPPDATA%\\ResiManage\\data`, separately from the installed executable. Updating or reinstalling the program should therefore not replace the data folder. On first launch after this change, the launcher copies a legacy `rotation.db`, resident-photo folder, and existing secret from the old executable directory when present; it keeps the originals and never overwrites an existing new data folder. Before testing with real records, use the in-app backup feature and keep a copy of that backup outside the computer. The Windows installer and portable build are test packages until their build and launch checks have been reviewed.

## E-mail verification and synchronization status

Email-code registration requires SMTP configuration; see [email verification setup](docs/EMAIL_VERIFICATION_SETUP.md). Do not add SMTP secrets to the repository or APK.

PC ↔ Android offline synchronization is not yet implemented. The security design and acceptance criteria are recorded in [the synchronization architecture](docs/SYNC_ARCHITECTURE_RESIMANAGE2.md). Do not expose the local Flask service publicly or use real resident data in a test environment before the security and recovery checks are complete.
