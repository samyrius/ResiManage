package com.samyrius.rotationapp;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.URLUtil;
import android.widget.TextView;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {
    private static final String HOME_URL = "http://127.0.0.1:5000/login";
    private static final int FILE_CHOOSER_REQUEST = 1201;
    private WebView webView;
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
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (fileChooserCallback != null) {
                    fileChooserCallback.onReceiveValue(null);
                }
                fileChooserCallback = callback;
                try {
                    Intent intent = params.createIntent();
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
        String dataDirectory = getFilesDir().getAbsolutePath();
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
                Uri[] results = (resultCode == RESULT_OK && data != null && data.getData() != null)
                    ? new Uri[]{data.getData()} : null;
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
