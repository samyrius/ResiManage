# Rotation App — Project Continuity Archive

Last updated: 2026-10-13

## Purpose and working rule
This file is the durable project handover log for `samyrius/rotation-app`. Read it before continuing work. Update it when requirements, implementation, tests, or decisions change. Do not restart completed setup steps or ask the user to repeat information already recorded.

## Confirmed by the user
- GitHub repository read/write access was resolved earlier. Do not revisit it unless a new, specific failure occurs.
- A prototype has already been built, installed on the user's phone, and launched successfully. Do not restart the prototype-creation phase from scratch.
- The user has additional observations and changes to discuss later. Do not request or start that critique phase yet; finish the original agreed requirements first.
- Work autonomously through implementation and testing. Ask only when a genuinely indispensable permission, secret, or decision is missing.
- Protect local and real data: back up before risky operations; preserve `rotation.db`, resident and stage histories, backups, and DEMS archive; never commit/upload database files, backups, passwords, or tokens. Do not overwrite or delete real data without explicit permission.
- Never report a task as complete without a verifiable result.

## Product requirements to finish before the critique phase

### Core workflow
- Flask-based resident rotation manager, with Arabic/French/English UI and RTL for Arabic.
- Manage residents, departments/terrains, periods, capacity, assignments, history, yearly summary, CSV export, and downloadable database backup.
- Four periods per academic year: 01 Feb–30 Apr; 01 May–30 Jul; 01 Aug–30 Oct; 01 Nov–30 Jan.
- Assignment priority: 4th year, then 3rd, 2nd, 1st.
- Enforce one assignment per resident per period and enforce capacity for each terrain/period.
- Prevent repeating a terrain until all mandatory/core terrains are completed; optional terrains are not prerequisites for repeat eligibility.
- Mismatched mandatory-year assignments must require an authorized decision with a recorded reason/audit trail.

### Terrain classification
- Optional: Sédation (7), Maxillo-faciale (8), Chirurgie cardiaque (11), Brûlés (18), CAC DBK (19).
- Gynécologie is NOT optional.
- Core/mandatory terrains include the other required departments already specified by the user, including Réanimation chirurgicale, Réanimation polyvalente, Chirurgie générale, Urologie, Orthopédie, Neurochirurgie, CCI, Obstétrique, PU Médecine, PU Chirurgie, ORL, Ophtalmologie, and Chirurgie thoracique.
- Verify seeded count is 19 and check exact category assignments. Do not infer or fabricate resident rotation history.

### Administrators and audit
- Pr Benhocine and Dr Dris are both Super Admins.
- Dr Dris has full control, including add/edit/delete, settings, assignments, archives, and authorized overrides. Benhocine is also Super Admin and department head.
- Normal users must be restricted according to role.
- Record administrative changes and override decisions in an audit log.

### Profiles, exams, archives
- Resident profiles should support surname, first name, birth details, phone, photo, exam scores by year, and complete past-stage history.
- Show completed terrains in red and not-yet-completed terrains in green; include objectives per terrain and per study year.
- First-year advancement after exams only if the overall average is at least 10/20 and no theory/practical component of any module is below 10/20.
- Advancement in years 2–4 is decided by Dr Dris and Pr Benhocine.
- After four years, DEMS success moves the resident and history to a graduation archive, not deletion.
- Support importing real DOC/DOCX/PDF/XLS lists with preview and validation, grouped by academic year. Do not invent past stages; record only documented history from the start of specialty.

### Security, data, delivery
- Remove insecure hard-coded/default credentials and ensure secret configuration is safe before any shared/production deployment. Never expose passwords in public UI, source, logs, or archive.
- Verify backup and restore procedure before any operation that could affect real data.
- Preserve `rotation.db` and all backups/history; database files are excluded from Git.
- Run automated tests for authentication, assignment duplicates, capacity limits, repeat eligibility, priority, mandatory-year decisions/audit, periods, terrain seed, CSV export, backup/restore, permissions, and archive flows.
- Verify mobile usability and provide the appropriate build/run instructions for the already established prototype. Do not claim a new APK or hosted demo exists unless its artifact/link has been verified.

## Resolved — do not repeat
- GitHub repository read/write access setup.
- Initial prototype creation, installation on the user's phone, and successful launch (confirmed by user).
- User-side pairing/token/setup walkthroughs.

## Current engineering state (verified 2026-10-13)
- Main branch baseline noted previously at commit `97ca43634f09a9506f929f7405595d09b8439306`.
- Isolated working branch: `prototype/verification-2026-10-13`.
- Pull request #8: https://github.com/samyrius/rotation-app/pull/8
- PR #8 merged into `main` in merge commit `52127b58aa1bcc7f86f320c34f7de35f0c63922e`. The changes include GitHub Actions CI, smoke/regression tests, the corrected CAC DBK seed and terrain classification, and this continuity archive.
- First CI attempt failed during collection because pytest could not import `app`; the test import path was fixed in commit `c5d80651051ed254308b8177ea72c8730372086d`.
- Historical baseline run for commit `c8774e679fcd34b4287026f1dc6d67a461bd588a` passed 7 initial tests. This has been superseded by the expanded verification recorded below.
- Do not merge this branch until the tests pass and changes are reviewed. No database files or real resident data were committed.

## Next steps (continue without asking the user to repeat context)
1. Continue adding isolated tests for mandatory-year overrides/audit, and role permissions.
2. Inspect admin authorization and replace insecure shared/default credential behavior with a safe migration path that does not lock out the existing phone prototype or touch real database files.
3. Implement/verify profile, exam progression, DEMS archive/import, objectives, audit log, and backup/restore requirements that are still absent.
4. Validate priority ordering, four-period rollover, and annual advancement rules.
5. Keep this archive current with commits, test evidence, remaining gaps, and completed tasks.
6. Only after the original requirements are addressed, invite the user to provide the critique and adjustments they have intentionally deferred.

## Expanded implementation and verification update (2026-10-13)

- Latest verified code/test commit: `49924478a7ee81a5a0a81de6c4768dfa75b597e6`. GitHub Actions run `38454544015` completed successfully: **25 tests passed in 8.38 seconds**. Tests use isolated temporary databases; no resident database or real resident records were committed.
- Implemented on the isolated branch:
  - PBKDF2 password hashing, migration of legacy SHA-256 hashes after a successful login, no default password displayed in the login page, first-run administrator password setup, and a locally generated Flask secret stored in ignored `.rotation_secret` unless `ROTATION_SECRET` is configured.
  - Individual user accounts with Super Admin/standard roles; sensitive pages are restricted; accounts can be deactivated safely while preventing deactivation of the current account or the last active Super Admin.
  - Add/edit/deactivate terrains without deleting history; deactivated terrains are excluded from new assignment/capacity/history/objective selectors.
  - Audited assignment cancellation rather than physical deletion, so the record remains available for audit/history.
  - Resident profiles with editable identity/contact/birth fields, photo upload validation (PNG/JPG/WEBP, 4 MB maximum), history, assignment status, terrain completion colors, exam marks, and objectives.
  - First-year exam progression rule: calculated average at least 10/20 and no theory/practical component below 10/20. The evaluation screen requires confirmation that all module marks have been entered. Years 2–3 progression requires a Super Admin decision; exam records can be corrected without creating duplicate module rows.
  - DEMS success archive stores the resident profile, stage history, assignments and exam snapshot, while preserving the original resident/history records.
  - Import preview/validation for CSV, XLS/XLSX, DOC/DOCX and text-based PDF; imported rows are grouped/sorted by study year and name. Import does not fabricate prior stages. Legacy .doc conversion requires antiword or LibreOffice; scanned PDFs without extractable text need OCR outside the app.
  - CSV export includes residents, terrains, periods, capacities, assignments, history, decisions, exams, objectives, DEMS archive and audit data, but excludes user credential hashes.
  - SQLite-consistent backup and validated restore. Restore checks SQLite integrity and required tables and creates a separate pre-restore backup before replacement.
  - Academic-year format validation, four-period creation with previous periods retained, year-priority ordering, exact five optional terrain classification, audit records for key administrative changes, and French/Arabic/English navigation labels for the added workflows.
- Updated `README.md` with local launch instructions, import limitations, backup/restore safety and branch status.
- The reviewed work was merged from `prototype/verification-2026-10-13` through PR #8. The user-confirmed existing phone prototype and local database were not accessed or modified by these repository changes.
- The CI test suite now covers the main rules, profile/objective workflows, first-year progression, DEMS archive, user roles, backup/restore, CSV/XLSX/DOCX import preview, CSV export, mandatory-year override/audit, priority, academic-year periods, photo upload, terrain deactivation, assignment cancellation, user deactivation, first-run setup and legacy password migration.

## Remaining real-world verification (do not claim complete until checked)
1. Perform a mobile smoke test of this updated branch against a copy of the existing prototype database. Back up first; never overwrite the user's actual database without explicit approval. This remote repository workflow cannot inspect or operate the user's phone database.
2. In the running app, create separate accounts for Pr Benhocine and Dr Dris in **Users**, assign both Super Admin, and set private passwords individually. The repository does not contain their passwords and must not.
3. Confirm the expected module list and enter the actual objectives for each terrain/year; the app provides data-entry forms but no official module/objective list was supplied to seed.
4. Test real DOC/XLS/PDF examples in the target Termux environment. Legacy DOC needs antiword or LibreOffice, and scanned PDF OCR is not included.
5. Review the final diff and CI status before deciding whether to merge PR #8. No new APK or hosted demo has been built or verified in this branch.
6. Only after these original requirements and checks are addressed should the user's deferred critique/adjustments be discussed.

## Post-merge status (2026-10-13)

- PR #8 is merged into `main`; merge commit: `52127b58aa1bcc7f86f320c34f7de35f0c63922e`.
- Before merge, the reviewed code commit `49924478a7ee81a5a0a81de6c4768dfa75b597e6` passed **25 automated tests in 8.38 seconds**. The archive-only branch commit also passed 25 tests in 6.93 seconds. Post-merge CI for merge commit `52127b58aa1bcc7f86f320c34f7de35f0c63922e` passed **25 tests in 6.76 seconds**. The subsequent documentation-only commit `37e585471d3444fedb8a9f4a601724a907374259` also passed **25 tests in 5.54 seconds**.
- No database, real resident records, backups, uploaded photos, passwords, or tokens were committed. Existing phone installation/data were not modified.
- Remaining external checks are unchanged: test the merged code against a copy of the existing phone database after backing it up; create the two named Super Admin accounts with private passwords in the app; validate real input files and populate the official module/objective data; and do not claim a new APK or hosted demo until one is actually built and tested.

## Archive limitation
This repository log captures durable project decisions and progress; it is not a verbatim recording of every voice call or every conversation. Do not store credentials, access tokens, personal secrets, or real resident records here.


## Bug log — 2026-10-14

### BUG-UI-001: Mobile layout overflows screen (reported from phone screenshot)
- **Observed:** content/header appear clipped horizontally; navigation and labels crowd/overlap; page does not adapt cleanly to a narrow phone viewport.
- **Action taken:** updated the shared CSS in `app.py` on `main` at commit `a7833ab582a84b9d4828742a58d35006d8408bbf`. Added global box sizing and horizontal overflow protection, responsive padding and grid sizing, wrapping for labels/buttons, scroll containment for wide tables, image sizing, and RTL navigation handling.
- **Status:** code change committed; **not yet runtime-verified on the user's phone**. Treat as pending verification, not confirmed fixed. Next: run automated tests/CI, inspect all rendered pages at narrow viewport widths, then install/build a test package only after the remaining recorded defects are addressed.
- **Process rule confirmed by user:** every newly discovered defect must be added to this Resistage project log with a unique ID, observed behavior, fix, test evidence, and status. Do not declare a defect fixed until it has been tested. Do not produce a new app build for the user until all logged defects have been corrected and the required tests pass.


## Navigation simplification — 2026-10-14

### UX-NAV-001: Too many top-level navigation buttons
- **Request:** keep Home, Departments/Services, Capacity/Seats, Assignments/Distribution, History, Decisions, and Resident Summary as primary navigation items. Group resident-related actions under a Residents dropdown: manage/add residents, objectives, import residents, promotion/exam decisions, and DEMS-success graduates. Group app/admin actions under Settings: app settings, admin accounts, audit log, database backup, CSV export, restore, and logout.
- **Implementation:** updated the shared navigation in `app.py` at commit `093e075051b4cee2c25fa87904880be8456d153e`. Added native expandable `<details>/<summary>` menus and Arabic/French/English labels. Existing route URLs were retained; only navigation grouping/labels/styles changed.
- **Design detail:** submenu entries are shown only after opening the corresponding dropdown, reducing top-level clutter. Mobile sizing and menu scroll limits are included; Arabic RTL is inherited from the page shell.
- **Status:** implementation committed; automated tests and rendered/mobile viewport checks are **pending**. Do not call this verified until tests and smoke checks pass.

### UX-NAV-001 test checklist
- [ ] Run the complete automated test suite / inspect latest CI status.
- [ ] Check authenticated navigation contains only the agreed primary buttons plus Residents and Settings dropdowns.
- [ ] Open both dropdowns and verify all requested links preserve their original routes.
- [ ] Verify Arabic RTL, French, and English labels.
- [ ] Inspect narrow mobile viewport for clipping, overlap, and submenu reachability.


## ResiTrack branding — 2026-10-14

### BRAND-001: Consistent application name and medical icon
- **Request:** use the chosen name ResiTrack and give the application a polished, clearly dimensional medical identity focused on resident rotations, medicine, and anaesthesia/intensive care.
- **Implementation:** added a scalable SVG icon at `static/resitrack-icon.svg` with a dimensional shield, medical cross, ECG line, gradient, and depth shadow; wired it as the browser favicon and the shared page-header icon. Updated the application name across Arabic, French, and English labels and added a localized descriptive tagline. Existing route names, database paths, and stored data are untouched.
- **Verification:** GitHub Actions and browser/mobile rendering checks must be confirmed on this branch before the change is called verified. This is a web-app branding change, not an Android APK build.
- **Status:** implementation submitted for automated checks; visual/runtime verification pending.

## Continuity update — 2026-10-17

- Confirmed current working baseline was `main` at `2e737efe` before the no-cross icon change.
- PR #17 merged as `ef02c485647aca35a273f8d58320390554b272c3`: updated the Android launcher vector and `static/resitrack-icon.svg` with the ResiManage name and clinician/ICU-monitor/ECG design without a cross. No database or resident-history files changed.
- GitHub's Android APK workflow ran automatically on that merge and succeeded, even though no manual build was requested. To respect the standing instruction, `.github/workflows/android-apk.yml` was changed in commit `81a242c757f61192fb028537825fc94c6105e71d` to `workflow_dispatch` only. Future APK builds must be explicitly started by the user; ordinary pushes and PRs no longer trigger that workflow.
- Annual leave and external rotation functionality was ported from the stale PR #12 branch onto a fresh branch based on current main, without copying its obsolete icon assets or old UI styles. It adds tables only (no existing rows are deleted), 30-day annual leave tracking with carry-forward and overlap checks, external-rotation records, server-side blocking of overlapping local assignments, dashboard shortcuts, and regression tests.
- PR #18: `https://github.com/samyrius/ResiManage/pull/18`. Python GitHub Actions test suite passed on the current PR head before this archive update; recheck the latest run before merge.
- Outstanding validation: test the new leave/external-rotation screens on a phone; visually verify the launcher icon on-device. Do not claim the APK was manually built or installed. Continue preserving `rotation.db`, resident and stage histories, DEMS archive, photos and backups; never commit personal data or secrets.
