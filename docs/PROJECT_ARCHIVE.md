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

## Continuity / defect log update — 2026-10-17

### BRAND-002: Login and registration still showed the retired ResiTrack name
- **Observed:** the shared header, Android label, and SVG used ResiManage, but the login/register/verification hero markup still rendered `Resi<span>Track</span>`; login hero used a warm pink/orange palette that no longer matched the approved navy/electric-blue/cyan/teal identity.
- **Fix applied on branch:** replace the remaining hero wordmark with ResiManage; align hero lighting, orbit glow, wordmark gradient, motto accent and footer separators with navy/cyan/teal; include ResiManage in the trilingual copyright line. Existing reduced-motion handling is retained.
- **Test:** add `test_login_branding_uses_resimanage_and_navy_cyan_identity` covering rendered login branding, no retired name, navy/cyan/teal color markers, reduced-motion CSS, trilingual rights line and absence of the cross-like `✚` glyph in login output.
- **Status:** awaiting CI on the new branch; not yet merged at time of this entry.

### VERIFIED-001: Current main regression suite
- **Evidence:** GitHub Actions Python application checks passed on commit `0287366dead0586867345dfb260f21b9f932be37`; the run covered the 29 current tests, including resident import/profile, promotion, DEMS archive, backup/restore, admin access, leave and external-rotation checks.
- **Limit:** passing automated tests do not verify physical Android installation, icon rendering on the launcher, real SMTP delivery, or visual layout on the user's phone.

### Remaining release gates (not falsely marked complete)
- [ ] Add deeper leave tests for multiple-year carry-forward, overlap rejection, and exact balance boundaries; review the meaning of the balance year (calendar vs academic year) with the written requirement.
- [ ] Verify external-rotation boundary dates and that assignment choices exclude a resident during an overlapping period (not just server-side rejection).
- [ ] Inspect/close obsolete PRs #12, #13 and #14 after confirming their useful changes have been recovered; review PR #7 selectively, never merge its divergent branch wholesale.
- [ ] Confirm real SMTP delivery only after authorized SMTP settings/test mailbox are available.
- [ ] Validate icon/UI on a physical phone and confirm Android package installability only after the user explicitly authorizes a build. Do not build an APK without that authorization.
- [ ] Keep all real databases, resident photos, backups, credentials and tokens out of Git.

### LEAVE-001 / EXT-001: Deeper leave accounting and external-rotation controls
- **Observed:** prior tests checked only one leave entry and a single active external rotation. The external assignment guard considered only status 'active', so a rotation marked 'returned' could fail to block an assignment entered later for the historical period it covered. The assignment dropdown also showed all residents even where a selected period overlapped an external rotation. External rotation records had no edit/cancel controls.
- **Fix applied on branch:** overlap checks now include active and returned external rotations and ignore only cancelled records; the assignment form marks conflicting resident options disabled based on the selected period; external rotation edit and cancel actions validate dates/required fields, preserve records, and write audit events. Added regression tests for multi-year leave carry-forward/overdraw, overlapping leave entries, returned-rotation period conflicts, assignment dropdown filtering, and audited edit/cancel.
- **Status:** awaiting CI on the feature branch; not merged until checks pass.

### CI-LEAVE-001: Refactor recovery and regression follow-up — 2026-10-17
- The first CI run for PR #21 exposed a source-refactor boundary error: the annual-leave route's final response template had been truncated while replacing the following external-rotation route. This was caught before merge; no changes reached main.
- Restored the complete annual-leave route verbatim from the current main baseline, then rechecked the boundary between the leave and external-rotation routes. The latest branch head is `097ed46032323368b82d5ab650ee785af02c0164`.
- **Status:** a fresh CI run on this corrected head is still required. Do not merge based on the earlier failed runs.

### SEC-001: CSRF protection and official administrator safeguards
- **Observed:** current main had no CSRF validation on state-changing POST requests, and the user-management route allowed the official accounts named `benhocine` and `drdris` to be created with a normal-user role or deactivated.
- **Fix applied on branch:** add session-bound CSRF tokens to POST forms at render time, validate tokens before POST handlers, and reject missing/invalid tokens. Require official accounts to be created as Super Admins and prevent deactivation. Test client now obtains a real rendered token for ordinary form submissions; a separate test explicitly submits without a token.
- **Status:** awaiting CI; no merge until the full suite passes. No APK build started.

### GOV-001: Dual-official decisions for progression and DEMS
- **Observed:** the current exams route advanced year-2/year-3 residents immediately after a single Super Admin click, and the DEMS route archived a year-4 resident after one administrator action. This did not meet the requirement that Pr Benhocine and Dr Dris jointly decide progression/final graduation.
- **Fix applied on branch:** added additive vote tables; restrict progression and DEMS votes to active Super Admin sessions for the exact official usernames `benhocine` and `drdris`; require a reason; keep the first vote pending; apply year advancement or DEMS-success archive only after both officials approve; if either rejects, do not advance/archive; log every vote and final decision to audit/decision records. Pending votes are visible on the corresponding pages.
- **Status:** awaiting CI. DEMS archive remains a copy of profile/history/exams; the active resident is marked graduated only after dual approval.

### BACKUP-001 / EXPORT-001: Include all new records and resident photos
- **Observed:** CSV export did not include the new leave/external-rotation/official-vote tables. The database backup did not package resident photos, so restoring it on another device could leave profile photo paths broken.
- **Fix applied on branch:** CSV export includes leave balances, leave entries, external rotations, and pending/final official vote tables while continuing to exclude user password records. The backup is now a ZIP containing a consistent SQLite snapshot and all files in `resident_photos/`; restore accepts both this ZIP and legacy .db/.sqlite backups, validates archive paths and database integrity, creates a pre-restore full ZIP and DB copy, and restores photos only when the ZIP includes the photo folder. Added tests for database and photo restoration, and expanded export coverage.
- **Status:** awaiting CI. This does not build an APK or touch real resident data in the repository.


### RESI-1 CANDIDATE / PHOTO-UPLOAD-UX-001 — 2026-10-17

- **Safety boundary:** work is isolated on `resimanage-1-photo-ui-candidate`, branched from `resimanage-1-backup`. The backup branch itself is unchanged; this candidate is not merged.
- **Finding:** the profile form exposed a manually editable photo path, and the upload check only inspected a few file-signature bytes. A truncated or corrupt file could be stored as if it were a real image. Upload names could also collide within the same second.
- **Proposed fix:** preserve the existing photo unless a valid replacement is uploaded; decode/verify and normalize PNG/JPG/WEBP images with Pillow; cap uploads at 4 MB and resize to 1200×1200; use unique names and atomic file writes.
- **UI changes:** structured profile header/avatar, responsive identity fields, clearer photo picker/help text, live preview before save, visible existing-photo preservation behavior, and improved keyboard focus/mobile styling.
- **Regression tests added:** valid real image uploads and is served as an image; corrupt image is rejected without replacing the existing photo; profile saves without a new upload preserve the photo path.
- **Validation status:** pending GitHub Actions on the exact candidate PR head. No APK build, phone experiment, database changes, resident data, or secrets were touched.
- **Porting rule:** after CI passes, port the tested code and regression tests to `resimanage-2-work` on a separate branch; do not merge this candidate into the backup branch.


### BRAND-3D-ICON-002 — 2026-10-17 — User-requested launcher/icon image integration

- **User request:** integrate the previously supplied glossy 3D medical/ICU badge image into the app now and record the work in this archive.
- **Source asset recovered:** the user's Library image "3500.png" (glossy blue/cyan clinician + ICU monitor + ECG badge, no cross). An optimized 128×128 JPEG derivative is stored at `static/resimanage-3d-icon.jpg` and as the Android drawable `android/app/src/main/res/drawable-nodpi/resimanage_3d_launcher.jpg`; the original image in Library remains unmodified.
- **Integration:** shared in-app brand/header image and Android launcher icon point to the recovered artwork; Android launcher label remains `ResiManage`. The prior vector launcher asset is retained, not deleted.
- **Branding caveat:** the supplied artwork has the embedded wordmark "ResiTrack" while the application/launcher label is ResiManage. This commit preserves the supplied image rather than silently editing its logo lettering.
- **Safety:** isolated on `resimanage-1-photo-ui-candidate`, not the protected `resimanage-1-backup`; no DB/resident data/secrets touched. No APK build or phone test.
- **Regression check:** confirms the static image is served as JPEG and referenced by the rendered app header; manifest points at the bitmap drawable.
- **Verification:** CI pending on this exact commit. If it passes, port the same icon integration to the isolated ResiManage 2 work candidate; do not merge into `main` or the protected backup as part of this task.


## User-confirmed execution order and pending validation — 2026-10-17

- **User instruction (recorded):** implement the requested improvements on the isolated ResiManage 1 candidate first; test and verify them; only after verification port the same verified changes to ResiManage 2 so both remain at the same progress level. Preserve the ResiManage 1 backup branch; do not edit it directly.
- **Photo upload bug is a priority:** previous profile photo selection/upload reportedly failed in the user's phone test. Candidate repair now validates decoded PNG/JPEG/WEBP images with Pillow, applies EXIF orientation, enforces a 4 MiB limit and 1200 px maximum, writes uniquely and atomically, keeps the old photo on invalid/no replacement, and adds regression tests. Python CI is evidence for backend handling only; actual Android/WebView picker behavior still requires a later user-authorized phone check.
- **Interior UI request:** modern, elegant, future-facing, organized and ergonomic; Arabic RTL plus French/English; responsive mobile controls, accessible focus/reduced motion, useful resident profile/avatar and status/progress cues. The benchmark document records 10 comparable platforms and 14 relevant websites and summarizes patterns. This candidate is a profile/navigation foundation, not yet a complete redesign of every screen.
- **Candidate links/status:** ResiManage 1 PR #71 (candidate, not merged): https://github.com/samyrius/ResiManage/pull/71 . Its current archive-update head `298c68135dd0fcf9099f9b430377813bf1c6cbed` has a successful Python application check (Actions run `39043216236`). ResiManage 2 port PR #72 (not merged): https://github.com/samyrius/ResiManage/pull/72 . The documented passing ResiManage 2 SHA `88d59c36b02a8becd051ccf5f303977c0e84b605` is earlier than the latest PR head `84ccdf25669705253c254d5123326bd623e7c064` (archive update); no matching workflow run was returned for that latest head, so **the port is not yet verified at its latest SHA**.
- **No APK build, phone test, real resident database, real resident records, or secrets were used.** Do not merge either candidate or claim photo upload works on-device until the exact candidate CI passes and the later supervised device check is completed.
