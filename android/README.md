# Android build and install

This project wraps the Flask/SQLite application in an Android WebView and starts Flask on the device's loopback interface. The database, secret key, resident photos, and backup ZIP are stored in the app's private files directory; they are not part of the APK.

## Build

The GitHub Actions workflow **Android APK build** runs Gradle and uploads the artifact `rotation-app-debug-apk`. To build locally, install JDK 17, Android SDK platform 35/build-tools 35, and Gradle 8.13, then run:

```bash
cd android
gradle --no-daemon assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

## Install

1. Download the `rotation-app-debug-apk` artifact from a successful GitHub Actions run.
2. Extract `app-debug.apk` from the ZIP.
3. Install it on a 64-bit ARM Android device (the build currently targets `arm64-v8a`).
4. Open the app and create the first administrator password when prompted.
5. Open **Administrator accounts** and create usernames `benhocine` and `drdris`, both with the **Super administrator** role and separate strong passwords.

This is a debug-signed test build, not a Play Store release. It has been built in CI, but has not yet been installed and tested on a physical device. Back up the data from inside the app before uninstalling it: Android removes private app data on uninstall.

## Import and backup notes

- CSV, XLS/XLSX, DOCX, and text-based PDF import are supported. Legacy DOC requires the external `antiword` program, which is not bundled in the APK; convert old DOC files to DOCX or CSV. Scanned PDFs need OCR first.
- The **Backup** action downloads a ZIP containing `rotation.db` and resident photos to the device's Downloads folder.
- The embedded server listens only on `127.0.0.1:5000`; it is not exposed to the local network.
