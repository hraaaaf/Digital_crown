import uvicorn
import multiprocessing
import threading
import time
import webbrowser
import sys
import os
from backend.main import app

def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8005")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    if getattr(sys, 'frozen', False):
        threading.Thread(target=open_browser, daemon=True).start()
        
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="info")
