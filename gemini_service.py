import os
import requests
import json
from dotenv_loader import load_env

load_env()

API_KEY = os.getenv("GEMINI_API_KEY")
# gemini-3-flash-preview is confirmed working and fast
MODELS_TO_TRY = [
    "models/gemini-3-flash-preview"
]

def generate_text(prompt, system_instruction=None, temperature=0.8, seed=None):
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
        generation_config = {
            "temperature": temperature
        }
        if seed is not None:
            generation_config["seed"] = int(seed)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                print(f"[Gemini] Error with {model}: {resp.status_code}")
        except Exception as e:
            print(f"[Gemini] Exception with {model}: {e}")
            continue
    return None

def generate_with_grounding(query, system_instruction=None):
    """Generates content with Google Search grounding."""
    for model in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": query}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0.3
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
        except Exception as e:
            print(f"[Gemini Grounding] Exception with {model}: {e}")
    # Fallback without grounding
    return generate_text(query, system_instruction)
