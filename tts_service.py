import os
import re
import json
import base64
import subprocess
import requests
import asyncio
import edge_tts
from dotenv_loader import load_env

load_env()

API_KEY = os.getenv("GEMINI_API_KEY")

def clean_script_for_tts(raw_text):
    """
    Strips all bracketed timestamps, staging notes, physical body delivery cues,
    and markdown artifacts so only pure, natural human spoken words are sent to TTS.
    """
    text = raw_text
    # If the text has sections, extract clean narration section if present
    if "## 3. CLEAN SPOKEN NARRATION" in text:
        text = text.split("## 3. CLEAN SPOKEN NARRATION")[1].split("##")[0]
    elif "## 1. SPOKEN SCRIPT" in text:
        text = text.split("## 1. SPOKEN SCRIPT")[1].split("## 2.")[0]
        
    # Strip bracketed cues like [0:00 - 0:02 | Hook: Intense direct eye contact]
    text = re.sub(r"\[.*?\]", "", text)
    # Strip markdown headers, asterisks, bullets
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"\*\*|\*", "", text)
    text = re.sub(r"__|_", "", text)
    # Normalize whitespaces and linebreaks
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = " ".join(lines)
    # Ensure natural micro-pauses by cleaning punctuation spacing
    cleaned = re.sub(r"\s+([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"([.,!?;:])\s*", r"\1 ", cleaned).strip()
    # Brand phonetic correction so TTS never pronounces 'Prava' as 'Brava'
    cleaned = re.sub(r"\bPrava\b", "Prah-va", cleaned)
    cleaned = re.sub(r"\bprava\b", "prah-va", cleaned)
    return cleaned

def synthesize_with_gemini_tts(text, output_mp3_path, voice_name="Aoede"):
    """
    Synthesizes speech using Gemini Studio TTS (gemini-3.8-flash-tts or gemini-2.5-flash-preview-tts).
    Converts PCM/WAV output into high-definition MP3 using FFmpeg.
    """
    models = ["gemini-3.8-flash-tts", "gemini-2.5-flash-preview-tts"]
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_name
                        }
                    }
                }
            }
        }
        try:
            print(f"[TTS] Requesting high-definition voice ({voice_name}) via {model}...")
            resp = requests.post(url, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                part = data["candidates"][0]["content"]["parts"][0]
                inline_data = part.get("inlineData", {})
                b64_audio = inline_data.get("data")
                if b64_audio:
                    raw_audio_bytes = base64.b64decode(b64_audio)
                    temp_wav = output_mp3_path + ".temp.wav"
                    with open(temp_wav, "wb") as f:
                        f.write(raw_audio_bytes)
                    
                    # Convert to 192k MP3 via FFmpeg
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", temp_wav,
                        "-c:a", "libmp3lame",
                        "-b:a", "192k",
                        output_mp3_path
                    ]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)
                    print(f"[TTS] Successfully generated HD audio with {model} ({voice_name}) at {output_mp3_path}")
                    return True
            else:
                print(f"[TTS] {model} returned status {resp.status_code}: {resp.text[:150]}")
        except Exception as e:
            print(f"[TTS] Error calling {model}: {e}")
            
    return False

async def synthesize_fallback_edge_tts(text, output_mp3_path):
    """
    High-fidelity neural fallback voice (ChristopherNeural - warm, intellectual science narrator).
    """
    print("[TTS] Utilizing high-fidelity neural narrator voice (ChristopherNeural)...")
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+1%", pitch="-1Hz")
    await communicate.save(output_mp3_path)
    return True

def generate_voiceover(raw_text, output_mp3_path, voice_name="Aoede"):
    clean_text = clean_script_for_tts(raw_text)
    print(f"[TTS] Cleaned spoken narration length: {len(clean_text)} characters.")
    
    # Try Gemini HD Studio Voice first
    success = synthesize_with_gemini_tts(clean_text, output_mp3_path, voice_name=voice_name)
    if not success:
        print("[TTS] Falling back to neural science narrator voice...")
        asyncio.run(synthesize_fallback_edge_tts(clean_text, output_mp3_path))
        
    return clean_text
