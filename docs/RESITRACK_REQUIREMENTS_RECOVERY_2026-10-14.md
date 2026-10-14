# ResiTrack — Requirements Recovery & Release Checklist
Date: 2026-10-14
Branch: feature/resitrack-leave-external-rotation
Base: main (PR #11 merge commit 8f72bd00e946e40d4c3cb668aca3df86cfc62be2)

This file records recovered requirements and release checks. A requirement written here is NOT proof of implementation. Do not mark an item complete without code inspection and test evidence.

## User-approved product identity and visual requirements
- Official name everywhere: **ResiTrack** (not Resistage).
- Launcher icon and all branding must contain NO cross symbol. Use a dimensional/futuristic ECG or heartbeat emblem; verify the Android launcher icon itself, not only the web favicon.
- First screen: polished, futuristic, animated/flash-like medical atmosphere in 3D, communicating medicine generally and anaesthesia/intensive care specifically; avoid a static generic icon as the only visual.
- Interior: cohesive futuristic, elegant styling, depth, readable cards and functional icons, restrained glow and responsive/mobile layout.
- Simplify navigation: group resident-related actions under one Residents control/dropdown; preserve access to resident management, objectives, imports, exams/promotion and DEMS archive. Group administrative actions under Settings.
- Arabic, French and English; Arabic RTL; language selector on login and inside the app.
- Show the agreed centered copyright in all three languages: “Tous droits réservés · Dr Dris”, “All rights reserved · Dr Dris”, “جميع الحقوق محفوظة · Dr Dris”.
- Do not use cross symbols in the icon/branding. Review all icon assets and Android launcher resources for this exclusion.

## Email registration and verification
- User registers with username, email and password; account must not be created/activated until a verification code delivered to that email is entered.
- Six-digit code, expires in 10 minutes, maximum five incorrect attempts; store a hash of the code, not plaintext.
- SMTP configuration must come from environment/secrets and must not be committed.
- Verify actual configured email delivery separately from mocked unit tests. A passing mocked test does not prove email can be delivered.

## Annual leave accounting — newly recovered requirement
- Each resident earns 30 calendar days of leave for each year.
- Unused earned leave carries forward and is added to the following year's available balance; it must not silently expire or be reset.
- Record each leave period with start date, end date, duration, academic/calendar year, and administrative actor/time. Prevent invalid/overlapping leave entries and prevent a balance from going negative unless an authorized override with reason is audited.
- Display earned, used, carried-forward and remaining days, including the calculation history. Define year boundaries consistently in the UI and tests; do not alter resident rotation history while adding leave support.
- Add tests for full use, partial use, no use and carry-forward across multiple years, date calculations, overlapping entries, and authorized overrides.

## External rotations — newly recovered requirement
- Record the resident, responsible employee/supervisor, destination/location, hospital name, country, rotation type and start/end dates; validate required fields and date order.
- During the external rotation, the resident must be excluded from the internal assignment/placement candidate list and must not receive a local assignment in any overlapping period.
- Automatically make the resident eligible again after the recorded return/end date, without deleting their profile, stage history, prior assignments or audit records.
- Show current external rotations and upcoming/returned records. Log creation, editing, cancellation and override actions.
- Add tests for exclusion during an active external rotation, date-boundary behavior, return to eligibility, and preservation of past history.

## Existing core requirements to preserve
- Four rotation periods: 01 Feb–30 Apr; 01 May–30 Jul; 01 Aug–30 Oct; 01 Nov–30 Jan.
- Assignment priority: year 4, then 3, 2, 1; one assignment per resident per period; enforce capacity.
- Optional terrains only: Sédation (7), Maxillo-faciale (8), Chirurgie cardiaque (11), Brûlés (18), CAC DBK (19). Gynécologie is not optional. Complete mandatory/core terrains before allowing a repeat; optional terrains are not prerequisites.
- Pr Benhocine and Dr Dris are Super Admins. Dr Dris has full administrative control and may override rules with a recorded reason. Audit sensitive changes.
- Preserve profiles, exam rules, objectives, stage history, import preview/validation, DEMS success archive, CSV export, backup/restore and the existing database. Never fabricate past stages.
- Never commit databases, real resident records, photos, backups, passwords, SMTP credentials or tokens.

## Branch / PR recovery notes
- Branch search returned: feature/profiles-admin-accounts, feature/resitrack-branding, feature/resitrack-vibrant-login, main, prototype/verification-2026-10-13, release/resitrack-beautification-test, release/rotation-app-candidate, release/rotation-app-final, release/rotation-app-ready, release/rotation-app-tested, release/rotation-app-verified, security/harden-authentication.
- PR #11 is merged into main (merge commit 8f72bd00e946e40d4c3cb668aca3df86cfc62be2); it describes the Android WebView wrapper, visual refresh, email-code flow and ECG icon. The PR explicitly says SMTP needs real configuration and physical-phone verification remains necessary.
- The current main archive has a branding entry describing a dimensional SVG with a medical cross. That conflicts with the user's explicit NO-CROSS instruction and must be corrected in the actual web and Android assets, not just in documentation.
- feature/resitrack-vibrant-login is an ancestor of the PR #11 merge and is two commits behind main; it has no unique commits ahead of main according to compare.
- feature/resitrack-branding has 4 commits ahead and 17 behind main; it must be reviewed selectively, not blindly merged.
- release/rotation-app-final has 58 commits ahead and 91 behind main; it is divergent and must not be blindly merged. Inspect individual diffs and recover only unique useful work.
- Other release branches are candidates for comparison. Inspect diffs against main before cherry-picking or merging. Preserve existing data and use isolated test databases.

## Acceptance / release gates
- [ ] Compare all remaining branch candidates with main and recover useful unique changes selectively.
- [ ] Fix no-cross launcher icon and confirm app name ResiTrack.
- [ ] Confirm animated first-screen visual and interior navigation/style on narrow Android screen.
- [ ] Confirm email registration and SMTP delivery with a real test mailbox after secrets are configured.
- [ ] Implement and test leave accrual/carry-forward.
- [ ] Implement and test external rotations and assignment exclusion/return.
- [ ] Run full automated suite and review security/code scanning.
- [ ] Build APK from the reviewed final branch and verify artifact URL, package name, installability and launch.
- [ ] Install on user's phone and test login, import preview, resident lists, leave, external rotation, backup/restore. Back up before risky operations.
- [ ] Do not call this release complete or provide a claimed verified APK until all gates above have evidence.

## Additional branch audit — 2026-10-14
- Inspected `release/rotation-app-verified`: its older `app.py` contains a `resident_leave` table and a `foreign_training` table embedded in the resident-record workflow. The older leave logic limits a single year to 31 days and does not implement unused-day carry-forward. The older foreign-training record stores country, host hospital and dates, but not the required responsible employee, destination/location, or rotation type; its assignment guard only checks whether an approved training overlaps today's date rather than the selected rotation period. These partial older changes were not blindly merged because the branch is 91 commits behind main and has a divergent schema/auth model.
- Compared all discovered branches against main. The old `feature/profiles-admin-accounts`, `security/harden-authentication`, and release candidates contain divergent older versions of `app.py` and test suites; `release/rotation-app-verified` also contains the earlier Android wrapper and import template. The newer PR #11 Android wrapper and current main implementation were retained; only relevant requirements were selectively reimplemented on this feature branch.
- Current PR #12 includes additive `leave_years`, `leave_entries`, and `external_rotations` tables, separate management screens, audit entries, overlap validation, an assignment-period overlap guard, and a layered ECG shield Android launcher icon with no cross. CI must pass on the latest commit before considering merge.
