import requests
import os
from dotenv_loader import load_env

load_env()
key = os.getenv("GEMINI_API_KEY")

models = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-pro"
]

for m in models:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": "Hi"}]}]}, timeout=8)
        print(f"{m} -> {r.status_code}")
        if r.status_code == 200:
            print("Response:", r.json()["candidates"][0]["content"]["parts"][0]["text"].strip())
            break
        else:
            print("Error:", r.text[:120])
    except Exception as e:
        print(f"{m} -> err {e}")
