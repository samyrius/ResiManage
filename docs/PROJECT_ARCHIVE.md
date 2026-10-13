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
- This branch adds GitHub Actions CI and smoke tests, corrects the seed to include CAC DBK and the five optional terrains, and has a durable requirements/continuity archive at `docs/PROJECT_ARCHIVE.md`. It has not been merged into main.
- First CI attempt failed during collection because pytest could not import `app`; the test import path was fixed in commit `c5d80651051ed254308b8177ea72c8730372086d`.
- Latest verified GitHub Actions run for commit `431637a3b9807dc739299f9bd4047694efeac3d2` passed: **6 tests passed in 0.42 seconds**. Coverage currently includes login/protected route, resident creation in an isolated temporary database, 19 seeded terrains/four periods/optional classification, capacity required, same-period duplicate prevention, and capacity limit.
- Do not merge this branch until the tests pass and changes are reviewed. No database files or real resident data were committed.

## Next steps (continue without asking the user to repeat context)
1. Continue adding isolated tests for repeat eligibility, mandatory-year overrides/audit, and role permissions.
2. Inspect admin authorization and replace insecure shared/default credential behavior with a safe migration path that does not lock out the existing phone prototype or touch real database files.
3. Implement/verify profile, exam progression, DEMS archive/import, objectives, audit log, and backup/restore requirements that are still absent.
4. Validate priority ordering, four-period rollover, and annual advancement rules.
5. Keep this archive current with commits, test evidence, remaining gaps, and completed tasks.
6. Only after the original requirements are addressed, invite the user to provide the critique and adjustments they have intentionally deferred.

## Archive limitation
This repository log captures durable project decisions and progress; it is not a verbatim recording of every voice call or every conversation. Do not store credentials, access tokens, personal secrets, or real resident records here.
