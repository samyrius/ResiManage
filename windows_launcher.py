# -*- coding: utf-8 -*-
"""Windows launcher for the ResiManage local Flask app."""
import os
import threading
import time
import webbrowser
from werkzeug.serving import make_server
import app as resimanage

def main():
    resimanage.init()
    port = int(os.environ.get("PORT", "5000"))
    server = make_server("127.0.0.1", port, resimanage.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"
    print("ResiManage is running locally. Keep this window open.")
    print(f"Open: {url}")
    time.sleep(1)
    webbrowser.open(url)
    try:
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        print("\nStopping ResiManage...")
        server.shutdown()

if __name__ == "__main__":
    main()
