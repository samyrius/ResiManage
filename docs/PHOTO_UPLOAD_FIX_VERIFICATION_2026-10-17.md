# ResiManage photo upload + profile UX verification log — 2026-10-17

## User instruction / sequencing
Implement the resident-photo/profile UX repair on an isolated ResiManage 1 candidate first, verify it with automated tests, then port the same fix to ResiManage 2 so both branches stay aligned. Keep this record in the project archive. Do not alter the protected `resimanage-1-backup` ref, real resident databases, or photos. Do not build an APK or claim Android/WebView picker behavior has been tested without an explicit later phone test.

## Scope implemented
- Replace byte-signature-only checks with Pillow image decode/verify for PNG/JPEG/WEBP, extension/format consistency, EXIF orientation normalization and max 1200×1200 resize; reject empty/corrupt/oversized (over 4 MiB) uploads.
- Preserve an existing profile photo when no replacement is selected; remove the manually editable photo-path field.
- Store replacement images under collision-resistant names using atomic file replacement.
- Improve the resident profile presentation: responsive profile/avatar header and form, clear file picker/help, client-side preview/feedback, visible focus and mobile ergonomics.
- Add regression coverage for a valid upload/served-image round trip, corrupt-image rejection without overwriting the current photo, and profile save retaining an existing photo.
- Benchmark document: `docs/UX_BENCHMARK.md` describes 10 comparable platforms and 14 relevant websites and distills practical design patterns. This is a profile-focused first pass, not a claim that every screen has undergone a full redesign.

## Automated verification evidence
- ResiManage 1 candidate PR #71, branch `resimanage-1-photo-ui-candidate`: Python application checks succeeded on head `8e8a74442a4d2ed95ef3f539878b942eb185cca3`, run `39037112652`.
- ResiManage 2 port PR #72, branch `resimanage-2-photo-ui-port`: Python application checks succeeded on head `1939d141260b7f8bd5a0bbb3dbad5e503cdcfbbd`, run `39037076374`.
- These runs are evidence for the then-current code/test heads. A documentation-only archive update creates new heads, so re-check CI against those exact final SHAs before saying the PR heads remain green.

## Remaining manual verification / boundaries
- Android/WebView file chooser and photo upload in the actual phone app remain untested; no APK was built and no phone experiment was started.
- Candidate PR #71 is not merged into `resimanage-1-backup`; keep the backup ref unchanged. PR #72 is an isolated port targeting `resimanage-2-work`, not `main`.
- Merge/port decisions should be based on the final PR head, successful CI, and a later supervised phone test; no real database/photo data was used in CI.
