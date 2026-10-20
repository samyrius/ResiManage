package com.samyrius.rotationapp;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.URLUtil;
import android.webkit.JavascriptInterface;
import android.widget.TextView;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONObject;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URI;
import java.security.KeyStore;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String HOME_URL = "http://127.0.0.1:5000/login";
    private static final int FILE_CHOOSER_REQUEST = 1201;
    private WebView webView;
    private String dataDirectory;
    private SyncBridge syncBridge;
    private ValueCallback<Uri[]> fileChooserCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(22, 78, 131));
        getWindow().setNavigationBarColor(Color.rgb(22, 78, 131));

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        webView.setWebViewClient(new WebViewClient());
        dataDirectory = getFilesDir().getAbsolutePath();
        syncBridge = new SyncBridge(dataDirectory);
        webView.addJavascriptInterface(syncBridge, "ResiManageSync");
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (fileChooserCallback != null) {
                    fileChooserCallback.onReceiveValue(null);
                }
                fileChooserCallback = callback;
                try {
                    // ACTION_OPEN_DOCUMENT is more reliable than WebView's default picker intent
                    // on Android when selecting CSV files from Downloads or document providers.
                    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("*/*");
                    intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
                        // Resident profile photos must be selectable in the same Android picker.
                        "image/*",
                        "image/png",
                        "image/jpeg",
                        "image/webp",
                        "text/csv",
                        "application/csv",
                        "text/comma-separated-values",
                        "application/vnd.ms-excel",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "application/msword",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/pdf",
                        "text/plain",
                        "application/octet-stream"
                    });
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                    return true;
                } catch (ActivityNotFoundException ex) {
                    fileChooserCallback = null;
                    return false;
                }
            }
        });
        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            try {
                String filename = URLUtil.guessFileName(url, contentDisposition, mimeType);
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                request.setTitle(filename);
                request.setDescription("Resident rotation backup");
                request.setMimeType(mimeType);
                request.setNotificationVisibility(
                    DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename);
                request.setAllowedOverMetered(true);
                String cookies = CookieManager.getInstance().getCookie(url);
                if (cookies != null) request.addRequestHeader("Cookie", cookies);
                DownloadManager manager = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
                manager.enqueue(request);
            } catch (Exception ex) {
                showStartupError("Could not start download: " + ex.getMessage());
            }
        });
        setContentView(webView);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        Python python = Python.getInstance();
        new Thread(() -> {
            try {
                python.getModule("rotation_server").callAttr("start_server", dataDirectory);
            } catch (Throwable error) {
                showStartupError("The local server could not start: " + error.getMessage());
            }
        }, "rotation-python-server").start();

        new Thread(this::waitForServer, "rotation-server-check").start();
    }

    private void waitForServer() {
        for (int attempt = 0; attempt < 80; attempt++) {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(HOME_URL).openConnection();
                connection.setConnectTimeout(400);
                connection.setReadTimeout(400);
                int status = connection.getResponseCode();
                if (status == 200 || status == 302) {
                    runOnUiThread(() -> webView.loadUrl(HOME_URL));
                    return;
                }
            } catch (Exception ignored) {
                // The embedded Flask server may still be starting.
            } finally {
                if (connection != null) connection.disconnect();
            }
            try {
                Thread.sleep(250);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
                return;
            }
        }
        showStartupError("The local server did not respond. Close and reopen the app.");
    }


    /** Android Keystore-backed config for the manual remote sync client. */
    private final class SyncBridge {
        private static final String KEY_ALIAS = "ResiManageSyncConfigKey";
        private static final String PREFS = "resimanage_sync_secure";
        private final String appDataDirectory;
        private final SharedPreferences preferences;
        private final ExecutorService executor = Executors.newSingleThreadExecutor();
        private volatile boolean running = false;

        SyncBridge(String dataDirectory) {
            appDataDirectory = dataDirectory;
            preferences = getSharedPreferences(PREFS, MODE_PRIVATE);
        }

        private SecretKey getOrCreateKey() throws Exception {
            KeyStore store = KeyStore.getInstance("AndroidKeyStore");
            store.load(null);
            if (store.containsAlias(KEY_ALIAS)) {
                return (SecretKey) store.getKey(KEY_ALIAS, null);
            }
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(
                    KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setRandomizedEncryptionRequired(true)
                    .build());
            return generator.generateKey();
        }

        private String encrypt(String plainText) throws Exception {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
            byte[] encrypted = cipher.doFinal(plainText.getBytes("UTF-8"));
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            output.write(cipher.getIV());
            output.write(encrypted);
            return Base64.encodeToString(output.toByteArray(), Base64.NO_WRAP);
        }

        private String decrypt(String encoded) throws Exception {
            byte[] packed = Base64.decode(encoded, Base64.NO_WRAP);
            if (packed.length < 13) throw new IllegalArgumentException("Encrypted sync settings are corrupt.");
            byte[] iv = new byte[12];
            System.arraycopy(packed, 0, iv, 0, iv.length);
            byte[] ciphertext = new byte[packed.length - iv.length];
            System.arraycopy(packed, iv.length, ciphertext, 0, ciphertext.length);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(128, iv));
            return new String(cipher.doFinal(ciphertext), "UTF-8");
        }

        @JavascriptInterface
        public String saveConfig(String serverUrl, String bearerToken) {
            try {
                URI uri = new URI(serverUrl == null ? "" : serverUrl.trim());
                if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null
                        || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null
                        || (uri.getPath() != null && !uri.getPath().isEmpty() && !"/".equals(uri.getPath()))) {
                    return new JSONObject().put("ok", false).put("message",
                            "Enter the HTTPS server origin only (for example https://vpn-ip:5000).").toString();
                }
                String token = bearerToken == null ? "" : bearerToken.trim();
                if (token.length() < 32 || token.length() > 256) {
                    return new JSONObject().put("ok", false).put("message", "The bearer token is missing or invalid.").toString();
                }
                JSONObject config = new JSONObject();
                config.put("serverUrl", uri.toString().replaceAll("/+$", ""));
                config.put("token", token);
                preferences.edit().putString("encrypted_config", encrypt(config.toString())).apply();
                return new JSONObject().put("ok", true).put("message", "Sync settings saved encrypted in Android Keystore-backed storage.").toString();
            } catch (Exception ex) {
                try { return new JSONObject().put("ok", false).put("message", ex.getMessage()).toString(); }
                catch (Exception ignored) { return "{\"ok\":false,\"message\":\"Could not save sync settings.\"}"; }
            }
        }

        @JavascriptInterface
        public boolean isConfigured() {
            return preferences.contains("encrypted_config");
        }

        @JavascriptInterface
        public boolean clearConfig() {
            preferences.edit().remove("encrypted_config").apply();
            return true;
        }

        @JavascriptInterface
        public boolean runSync() {
            if (running) return false;
            String encrypted = preferences.getString("encrypted_config", null);
            if (encrypted == null) {
                notifyPage("{\"ok\":false,\"message\":\"Configure the central HTTPS server and device token first.\"}");
                return false;
            }
            running = true;
            executor.execute(() -> {
                String result;
                try {
                    JSONObject config = new JSONObject(decrypt(encrypted));
                    Python python = Python.getInstance();
                    result = python.getModule("sync_client").callAttr(
                            "sync_once", appDataDirectory,
                            config.getString("serverUrl"), config.getString("token")).toString();
                } catch (Throwable ex) {
                    try { result = new JSONObject().put("ok", false).put("message", ex.getMessage()).toString(); }
                    catch (Exception ignored) { result = "{\"ok\":false,\"message\":\"Sync failed.\"}"; }
                } finally {
                    running = false;
                }
                notifyPage(result);
            });
            return true;
        }

        private void notifyPage(String result) {
            final String quoted = JSONObject.quote(result);
            runOnUiThread(() -> {
                if (webView != null) webView.evaluateJavascript(
                        "window.resimanageSyncFinished && window.resimanageSyncFinished(" + quoted + ");", null);
            });
        }
    }

    private void showStartupError(String message) {
        runOnUiThread(() -> {
            TextView error = new TextView(this);
            error.setText(message);
            error.setTextColor(Color.rgb(120, 20, 20));
            error.setPadding(32, 32, 32, 32);
            setContentView(error);
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST) {
            if (fileChooserCallback != null) {
                Uri[] results = null;
                if (resultCode == RESULT_OK && data != null) {
                    if (data.getClipData() != null && data.getClipData().getItemCount() > 0) {
                        int count = data.getClipData().getItemCount();
                        results = new Uri[count];
                        for (int i = 0; i < count; i++) {
                            results[i] = data.getClipData().getItemAt(i).getUri();
                        }
                    } else if (data.getData() != null) {
                        results = new Uri[]{data.getData()};
                    }
                }
                fileChooserCallback.onReceiveValue(results);
                fileChooserCallback = null;
            }
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
