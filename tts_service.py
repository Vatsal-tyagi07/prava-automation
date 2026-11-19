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
    Injects natural micro-pauses for conversational rhythm.
    """
    text = raw_text
    # Extract clean narration section if present
    if "## 3. CLEAN SPOKEN NARRATION" in text:
        text = text.split("## 3. CLEAN SPOKEN NARRATION")[1].split("##")[0]
    elif "## 1. SPOKEN SCRIPT" in text:
        text = text.split("## 1. SPOKEN SCRIPT")[1].split("## 2.")[0]
        
    # Strip bracketed cues like [0:00 - 0:02 | Hook: ...]
    text = re.sub(r"\[.*?\]", "", text)
    # Strip markdown headers, asterisks, bullets
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"\*\*|\*", "", text)
    text = re.sub(r"__|_", "", text)
    text = re.sub(r"`.*?`", "", text)
    
    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = " ".join(lines)
    
    # Brand phonetic correction so speech engines never mispronounce 'Prava' as 'Brava'
    cleaned = re.sub(r"\bPrava\b", "Prah-va", cleaned)
    cleaned = re.sub(r"\bprava\b", "prah-va", cleaned)
    
    # Ensure natural conversational cadence with micro-pauses
    cleaned = re.sub(r"\s*—\s*", "... ", cleaned)
    cleaned = re.sub(r"\s*\.\.\.\s*", "... ", cleaned)
    cleaned = re.sub(r"\s+([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"([.,!?;:])\s*", r"\1 ", cleaned).strip()
    
    return cleaned

def synthesize_with_gemini_tts(text, output_mp3_path, voice_name="Aoede"):
    """
    Synthesizes speech using Gemini Studio TTS (Aoede or Kore).
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
            print(f"[TTS] Requesting conversational studio voice ({voice_name}) via {model}...")
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

async def synthesize_fallback_edge_tts(text, output_mp3_path, voice="hi-IN-MadhurNeural"):
    """
    Natural conversational Hinglish voiceover via Edge-TTS (hi-IN-MadhurNeural or hi-IN-SwaraNeural).
    """
    print(f"[TTS] Synthesizing conversational voiceover with Edge-TTS ({voice})...")
    communicate = edge_tts.Communicate(text, voice, rate="+2%", pitch="-1Hz")
    await communicate.save(output_mp3_path)
    print(f"[TTS] Edge-TTS voiceover saved to: {output_mp3_path}")
    return True

def generate_voiceover(raw_text, output_mp3_path, voice_name="Aoede"):
    clean_text = clean_script_for_tts(raw_text)
    print(f"[TTS] Cleaned spoken narration length: {len(clean_text)} characters.")
    
    # 1. Try Gemini HD Studio Voice first
    success = False
    if API_KEY:
        success = synthesize_with_gemini_tts(clean_text, output_mp3_path, voice_name=voice_name)
        
    # 2. High-fidelity Hinglish conversational fallback
    if not success:
        print("[TTS] Falling back to conversational Hinglish voice (hi-IN-MadhurNeural)...")
        try:
            asyncio.run(synthesize_fallback_edge_tts(clean_text, output_mp3_path, voice="hi-IN-MadhurNeural"))
            success = True
        except Exception as e:
            print(f"[TTS] Edge-TTS Madhur failed: {e}. Trying SwaraNeural...")
            try:
                asyncio.run(synthesize_fallback_edge_tts(clean_text, output_mp3_path, voice="hi-IN-SwaraNeural"))
                success = True
            except Exception as e2:
                print(f"[TTS] Edge-TTS Swara failed: {e2}. Trying en-IN-PrabhatNeural...")
                asyncio.run(synthesize_fallback_edge_tts(clean_text, output_mp3_path, voice="en-IN-PrabhatNeural"))
                success = True
                
    return clean_text
