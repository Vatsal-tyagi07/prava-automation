import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv_loader import load_env

load_env()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_telegram_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def send_message(text, parse_mode="HTML"):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }
    session = get_telegram_session()
    try:
        resp = session.post(url, json=payload, timeout=30)
        resp_json = resp.json()
        if not resp_json.get("ok"):
            payload.pop("parse_mode", None)
            resp = session.post(url, json=payload, timeout=30)
            return resp.json()
        return resp_json
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
        return {"ok": False, "error": str(e)}

def send_document(file_path, caption=None, mime_type=None):
    url = f"{BASE_URL}/sendDocument"
    if not os.path.exists(file_path):
        print(f"[Telegram] File not found: {file_path}")
        return {"ok": False, "error": "file_not_found"}
    data = {"chat_id": CHAT_ID}
    if caption:
        data["caption"] = caption[:1024]
        
    filename = os.path.basename(file_path)
    if not mime_type:
        if filename.endswith(".csv"):
            mime_type = "text/csv"
        elif filename.endswith(".pdf"):
            mime_type = "application/pdf"
        elif filename.endswith(".txt") or filename.endswith(".md"):
            mime_type = "text/plain"
        else:
            mime_type = "application/octet-stream"
            
    session = get_telegram_session()
    for attempt in range(1, 4):
        try:
            with open(file_path, "rb") as f:
                files = {"document": (filename, f, mime_type)}
                resp = session.post(url, data=data, files=files, timeout=120)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"[Telegram] Document send attempt {attempt} error: {e}")
            time.sleep(2)
            
    return {"ok": False, "error": "all_document_retries_failed"}

def send_audio(file_path, caption=None, title=None, performer=None):
    url = f"{BASE_URL}/sendAudio"
    if not os.path.exists(file_path):
        print(f"[Telegram] File not found: {file_path}")
        return {"ok": False, "error": "file_not_found"}
    data = {"chat_id": CHAT_ID}
    if caption:
        data["caption"] = caption[:1024]
    if title:
        data["title"] = title
    if performer:
        data["performer"] = performer
        
    filename = os.path.basename(file_path)
    session = get_telegram_session()
    for attempt in range(1, 4):
        try:
            with open(file_path, "rb") as f:
                files = {"audio": (filename, f, "audio/mpeg")}
                resp = session.post(url, data=data, files=files, timeout=120)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"[Telegram] Audio send attempt {attempt} error: {e}")
            time.sleep(2)
            
    return {"ok": False, "error": "all_audio_retries_failed"}

def send_video(file_path, caption=None):
    url = f"{BASE_URL}/sendVideo"
    if not os.path.exists(file_path):
        print(f"[Telegram] File not found: {file_path}")
        return {"ok": False, "error": "file_not_found"}
    data = {"chat_id": CHAT_ID}
    if caption:
        data["caption"] = caption[:1024]
    filename = os.path.basename(file_path)
    
    session = get_telegram_session()
    for attempt in range(1, 5):
        try:
            with open(file_path, "rb") as f:
                files = {"video": (filename, f, "video/mp4")}
                resp = session.post(url, data=data, files=files, timeout=180)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    print(f"[Telegram] Video send attempt {attempt} status {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"[Telegram] Video send attempt {attempt} error: {e}")
            time.sleep(2)
            
    return {"ok": False, "error": "all_video_retries_failed"}
