# Android build and install

This project wraps the Flask/SQLite application in an Android WebView and starts Flask on the device's loopback interface. The database, secret key, resident photos, and backup ZIP are stored in the app's private files directory; they are not part of the APK.

## Build

The Android build workflows are currently **manual-only** by user request while the remaining directives are implemented. Do not start the APK build or emulator smoke test until the final review. At that point, run the relevant workflow manually from GitHub Actions; the main validation workflow runs Python tests, builds the APK, and performs an emulator smoke test. To build locally, install JDK 17, Android SDK platform 35/build-tools 35, and Gradle 8.13, then run:

```bash
cd android
gradle --no-daemon assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

## Install

1. After the final review and manual workflow run, download the `resimanage2-debug-apk` artifact from that successful GitHub Actions run.
2. Extract `app-debug.apk` from the ZIP.
3. Install it on a 64-bit ARM Android device (the APK includes `arm64-v8a` and `x86_64` libraries; x86_64 is included for emulator testing).
4. Open the app and create the first administrator password when prompted.
5. Open **Administrator accounts** and create usernames `benhocine` and `drdris`, both with the **Super administrator** role and separate strong passwords.

This will be a debug-signed test build, not a Play Store release. The latest source changes have not yet been rebuilt or checked on an emulator, and the APK has not been confirmed on a physical phone. Back up the data from inside the app before uninstalling it: Android removes private app data on uninstall.

## Import and backup notes

- CSV, XLS/XLSX, DOCX, and text-based PDF import are supported. Legacy DOC requires the external `antiword` program, which is not bundled in the APK; convert old DOC files to DOCX or CSV. Scanned PDFs need OCR first.
- The **Backup** action downloads a ZIP containing `rotation.db` and resident photos to the device's Downloads folder.
- The embedded server listens only on `127.0.0.1:5000`; it is not exposed to the local network.
