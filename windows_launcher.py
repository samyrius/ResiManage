# -*- coding: utf-8 -*-
"""ResiManage desktop launcher: local Flask backend + native WebView window."""
import os
import threading
from werkzeug.serving import make_server
import app as resimanage

def main():
    resimanage.init()
    port = int(os.environ.get("PORT", "5000"))
    server = make_server("127.0.0.1", port, resimanage.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"

    try:
        import webview
        window = webview.create_window("ResiManage", url, width=1280, height=820, min_size=(900, 600))
        window.events.closed += lambda: server.shutdown()
        webview.start()
    except ImportError:
        import webbrowser
        webbrowser.open(url)
        thread.join()
    finally:
        if thread.is_alive():
            server.shutdown()

if __name__ == "__main__":
    main()
