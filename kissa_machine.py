import os
import json
import re
from datetime import datetime
from dotenv_loader import load_env
import gemini_service
import telegram_service
import video_engine
import tts_service
import db

load_env()

BASE_DIR = os.path.dirname(__file__)
PIPELINE_STATE_FILE = os.path.join(BASE_DIR, "pipeline_state.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "episodes")

SEQUENTIAL_TOPICS = {
    22: "The Attention Mechanism (Query, Key, Value & The Context Spotlight)",
    23: "Self-Attention & Mutual Word Resonance (How Words Talk to Each Other)",
    24: "Multi-Head Attention (Parallel Perspectives)",
    25: "The Transformer Architecture (Encoder-Decoder Fusion)",
    26: "Positional Encoding (Teaching Math the Order of Words)",
    27: "Feed-Forward Layers & Long-Term Memory Storage",
    28: "Layer Normalization & Residual Connections (Preventing Gradient Vanishing)",
    29: "Softmax & Temperature in LLMs (Controlling Creativity vs Precision)",
    30: "Byte Pair Encoding & Tokenization (How Models Read Raw Text)",
    31: "KV Cache Optimization (Why Inference Speed Drops Over Long Chats)",
    32: "Rotary Position Embeddings / RoPE (Relative Geometry in Modern LLMs)",
    33: "Mixture of Experts / MoE (Activating Only Sparse Brain Sectors)",
    34: "RLHF & DPO (Aligning Raw Probability with Human Intent)",
    35: "Quantization & FP8/INT4 (Running Trillion-Parameter Models on Edge)"
}

# Master Anti-Repetition Registry: Blacklists tropes used in earlier runs
PAST_METAPHORS_BLACKLIST = [
    "Indian wedding hall / noisy dhol / Biryani shoutout",
    "Dining table / brainstorming room yelling context clues",
    "Cricket / sports broadcast 8-camera crew / bowler wrist spin",
    "2-star Michelin kitchen relay / prep sous-chef / plating chef",
    "Detective clue board / red yarn on corkboard",
    "Static radial geometric webs / circular star nodes",
    "Airport luggage carousel / baggage conveyor belt",
    "Traffic police / traffic intersection signal",
    "Library card catalog / librarian with flashlight"
]

def load_pipeline_state():
    if not os.path.exists(PIPELINE_STATE_FILE):
        state = {
            "current_episode": 26,
            "last_topic": "The Transformer Architecture (Encoder-Decoder Fusion)",
            "next_topic": SEQUENTIAL_TOPICS[26],
            "sequence": {str(k): v for k, v in SEQUENTIAL_TOPICS.items()},
            "history": []
        }
        with open(PIPELINE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        return state
    with open(PIPELINE_STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_pipeline_state(state):
    with open(PIPELINE_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def sanitize_narration(text):
    """
    Guarantees pure plain text narration:
    Strips markdown, asterisks, headers, stage directions, and bracketed cues.
    """
    if not text:
        return ""
    # Strip markdown headers (e.g. #, ## 1. etc)
    text = re.sub(r"#+\s*.*?\n", "\n", text)
    # Strip bracketed cues, timestamps, or stage directions e.g. [0:00 - 0:03], [Smiling], [Cut to...]
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    # Strip markdown bold/italic/code syntax
    text = re.sub(r"\*\*|\*", "", text)
    text = re.sub(r"__|_", "", text)
    text = re.sub(r"`.*?`", "", text)
    # Strip bullet marks or list numbering
    text = re.sub(r"^\s*[-*•\d\.]+\s*", "", text, flags=re.MULTILINE)
    # Normalize brand pronunciation
    text = re.sub(r"\bPrava\b", "Prah-va", text)
    text = re.sub(r"\bprava\b", "prah-va", text)
    # Clean whitespace and punctuation
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = " ".join(lines)
    cleaned = re.sub(r"\s+([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"([.,!?;:])\s*", r"\1 ", cleaned).strip()
    return cleaned

def get_locked_standalone_script(episode_num, topic):
    """
    Dynamic fallback narration script tailored to the requested topic.
    Guarantees 100% plain text narration, conversational Hinglish, zero markdown,
    zero bracketed cues, and authentic peer-to-peer chai-time tone.
    """
    topic_clean = topic.split("(")[0].strip()
    return (
        f"Kabhi socha hai ki jab ek AI model {topic_clean} execute karta hai, toh background mein actual mein kya ho raha hota hai? "
        f"Textbook math isko bohot complex banati hai, lekin simple shabdon mein samjho toh yeh poora khel ek smart filter jaisa hai. "
        f"Socho jaise ek busy railway dispatch room jahan hazaron trains ek saath track par aati hain. "
        f"Bina kisi delay ke har token ko exact direction aur mathematical weight diya jata hai taaki context kabhi lost na ho. "
        f"Yeh choti si architectural trick pure inference ko super fast aur reliable bana deti hai. "
        f"Follow Prah-va, and keep questioning the machine."
    )

def generate_stage_1_script(episode_num, topic, past_analogies=None):
    """
    STAGE 1: SCRIPT GENERATION (Fresh, Conversational, Non-Repetitive)
    - 100% Standalone: Zero callbacks ("Yesterday we learned...", "In the previous episode...").
    - Authentic, conversational Hinglish (Roman script, everyday spoken Hindi mixed naturally with English tech terms).
    - Tone: Intriguing, natural peer-to-peer explanation (like discussing an AI topic over chai).
    - Eliminate robotic documentary phrasing and repetitive intros ("Kya aapko pata hai?").
    - Output: Plain text narration only—no markdown, asterisks (**), stage directions, or bracketed cues.
    - Set LLM temperature to 0.8 and pass a dynamic seed (e.g. current date/timestamp) so output varies daily.
    """
    now = datetime.now()
    dynamic_seed = int(now.timestamp()) % 2147483647
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Dynamic anti-repetition blacklist from past episodes and history
    state = load_pipeline_state()
    history_blacklist = []
    for item in state.get("history", []):
        if item.get("analogy_used"):
            history_blacklist.append(item["analogy_used"])
        if item.get("topic"):
            history_blacklist.append(f"Previous topic: {item['topic']}")
            
    combined_blacklist = list(set(PAST_METAPHORS_BLACKLIST + history_blacklist + (past_analogies or [])))
    blacklist_str = "\n".join(f"- {b}" for b in combined_blacklist)

    system_instruction = (
        "You are the creator and voice of 'Kissa-e-Machine'—an engaging tech reel series explaining core AI architecture breakthroughs.\n\n"
        "CORE VOICE & TONE:\n"
        "- Voice: Intriguing, energetic, natural peer-to-peer explanation—like two senior engineers discussing deep AI internals over chai.\n"
        "- Language: Authentic, conversational Hinglish written purely in Roman script (everyday spoken Hindi naturally interwoven with English tech terms like 'weights', 'loss function', 'attention', 'tokens', 'vectors', 'layers', 'cache', 'GPU', 'parameters').\n"
        "- STRICTLY NO Devanagari script. Use Roman letters only.\n\n"
        "STRICT CARDINAL RULES:\n"
        "1. BAN CLICHÉ REPETITIVE INTROS: Never start with 'Kya aapko pata hai?', 'Ever wondered?', 'Dosto...', 'Aaj hum baat karenge...', or 'Have you ever noticed...'. Start directly with an intriguing problem, engineering paradox, or sharp question.\n"
        "2. ELIMINATE DOCUMENTARY PHRASING: Strictly ban sterile, robotic documentary lines (e.g. 'In the vast realm of computing', 'Let us examine how the system computes', 'It is fascinating to observe'). Speak with casual authority and relatable punchlines (e.g., 'socho agar...', 'par asli twist yeh hai...', 'simple shabdon mein...', 'asli game yahan shuru hota hai').\n"
        "3. ZERO SERIALIZATION: Strictly ban all episode callbacks ('Yesterday we learned...', 'In our previous episode...', 'Kal humne dekha tha...', 'Continuing our journey...'). Every episode must be 100% self-contained for a first-time viewer.\n"
        "4. ANTI-REPETITION METAPHOR ENGINE: You must NOT use any of these blacklisted analogies:\n"
        f"{blacklist_str}\n"
        "For every run, invent a brand-new, vivid, physical real-world metaphor (e.g. soundboard audio mixer, subway track switching, fast-food assembly line, mechanical typewriter hammer, pocket radio tuning) to explain how the AI mechanism works.\n"
        "5. PLAIN TEXT NARRATION ONLY: Output strictly pure spoken voiceover narration in plain text. Absolutely NO markdown headers (# or ##), no asterisks (**), no bold/italic markers, no stage directions, no camera angles, no delivery cues, and no bracketed timestamps ([0:00 - 0:03]). Do not include greetings or intro/outro meta text like 'Here is your script:'.\n"
        "6. BRAND PRONUNCIATION & SIGN-OFF: Always write the brand phonetically as 'Prah-va' so speech synthesis engines pronounce it accurately. Always finish the narration with the exact sign-off line: 'Follow Prah-va, and keep questioning the machine.'\n"
        "7. DURATION: Spoken duration of 45 to 55 seconds (~115 to 135 words)."
    )

    prompt = f"""
Create an original, fresh narration script for Episode {episode_num} of "Kissa-e-Machine".
Topic: "{topic}"
Run Date/Time: {date_str} (Dynamic Seed: {dynamic_seed})

Narrative Structure:
1. Hook (First 1-2 sentences): A gripping, problem-first statement or paradox in street Hinglish that exposes a technical puzzle about "{topic}".
2. Fresh Analogy (Next 2-3 sentences): A brand-new, intuitive physical metaphor (avoiding all blacklisted analogies) that makes the concept click instantly.
3. The Engineering Insight (Next 2-3 sentences): How modern AI architectures actually solve this problem with elegance.
4. Takeaway & Outro: A sharp one-liner takeaway followed by "Follow Prah-va, and keep questioning the machine."

OUTPUT REQUIREMENT:
Provide plain text narration only. No markdown, no asterisks, no stage directions, no bracketed cues.
"""

    response_text = gemini_service.generate_text(
        prompt,
        system_instruction,
        temperature=0.8,
        seed=dynamic_seed
    )

    # Check for banned serial callbacks
    banned_callbacks = ["yesterday we", "in the last episode", "previously on", "in our last video", "continuing from", "kal humne", "pichle episode"]
    if response_text and any(bc in response_text.lower() for bc in banned_callbacks):
        print("[KissaMachine] Generated text contained serial callbacks. Enforcing fresh standalone script.")
        response_text = None

    if not response_text:
        response_text = get_locked_standalone_script(episode_num, topic)

    # Sanitize to guarantee 100% plain text narration without markdown or cues
    response_text = sanitize_narration(response_text)
    return response_text

def generate_stage_2_storyboard(script_text, episode_num, topic):
    """
    STAGE 2: DYNAMIC TOPIC-DRIVEN VISUAL STORYBOARDING
    Prompts the LLM to output 4 distinct, custom visual scenes directly mapped
    to the script's timestamps and unique physical metaphor.
    """
    system_instruction = (
        "You are an expert motion graphics director at Kurzgesagt / Vox. "
        "Read the provided script and output a JSON list of 4 distinct sequential visual scenes. "
        "Strictly ban static radial nodes, generic spinning rings, or repetitive star graphs. "
        "Map visuals directly to the physical objects in the script (e.g. luggage belts, gears, wave oscillators, vector fusions). "
        "Return ONLY a valid JSON array of objects with keys: "
        "'mode' (must be one of: 'order_chaos', 'conveyor_flow', 'harmonic_oscillator', 'vector_fusion', 'synchronized_lattice'), "
        "'title' (string), 'subtitle' (string), 'start_sec' (float), 'end_sec' (float)."
    )
    prompt = f"""
SCRIPT FOR EPISODE {episode_num}:
{script_text}

Generate the 4 distinct visual scenes for this script. Return ONLY a valid JSON array.
"""
    scenes = None
    try:
        raw_json = gemini_service.generate_text(prompt, system_instruction, temperature=0.4)
        if raw_json:
            clean_json = re.search(r"\[.*\]", raw_json, re.DOTALL)
            if clean_json:
                scenes = json.loads(clean_json.group(0))
    except Exception as e:
        print(f"[KissaMachine] Error generating storyboard via LLM: {e}")
        
    if not scenes or len(scenes) < 3:
        # Handcrafted procedural storyboard tailored to Episode 26
        scenes = [
            {
                "mode": "order_chaos",
                "title": "THE BAG OF WORDS TRAP",
                "subtitle": "Order Blindness: 'Dog Bites Man' vs 'Man Bites Dog'",
                "start_sec": 0.0,
                "end_sec": 12.0
            },
            {
                "mode": "conveyor_flow",
                "title": "THE PARALLEL CONVEYOR",
                "subtitle": "50 Tokens Loaded at the Same Exact Microsecond",
                "start_sec": 12.0,
                "end_sec": 24.0
            },
            {
                "mode": "harmonic_oscillator",
                "title": "HARMONIC FREQUENCY STAMP",
                "subtitle": "Sine (High Freq) + Cosine (Low Freq) Harmonic Clocks",
                "start_sec": 24.0,
                "end_sec": 38.0
            },
            {
                "mode": "vector_fusion",
                "title": "VECTOR ADDITION CHAMBER",
                "subtitle": "Token Vector + Frequency Vector = Ordered Meaning",
                "start_sec": 38.0,
                "end_sec": 52.0
            }
        ]
        
    return scenes

def run_episode_pipeline(target_episode=None, dry_run=False):
    state = load_pipeline_state()
    episode_num = target_episode if target_episode else state.get("current_episode", 26)
    topic = SEQUENTIAL_TOPICS.get(episode_num, state.get("next_topic", f"Deep Architecture Part {episode_num}"))
    
    print(f"\n=======================================================")
    print(f"🎬 KISSA-E-MACHINE: Executing Episode {episode_num}")
    print(f"📌 Topic: {topic}")
    print(f"=======================================================")
    
    ep_dir = os.path.join(OUTPUT_DIR, f"EP_{episode_num}")
    os.makedirs(ep_dir, exist_ok=True)
    
    script_file = os.path.join(ep_dir, "script.txt")
    blueprint_file = os.path.join(ep_dir, "blueprint.md")
    storyboard_file = os.path.join(ep_dir, "storyboard.json")
    audio_file = os.path.join(ep_dir, "voiceover.mp3")
    video_file = os.path.join(ep_dir, "video.mp4")
    
    # 1. STAGE 1: Context-Aware Standalone Script Generation
    print("[1/4] STAGE 1: Generating Standalone Hinglish Script with Fresh Analogy Engine...")
    content = generate_stage_1_script(episode_num, topic)
    
    with open(blueprint_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    # 2. Synthesize Conversational Audio (Natural Female Voice: Edge-TTS hi-IN-SwaraNeural)
    print("[2/4] Synthesizing Natural Conversational Female Voiceover (hi-IN-SwaraNeural)...")
    clean_narration = tts_service.generate_voiceover(content, audio_file, voice_name="hi-IN-SwaraNeural")
    
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(clean_narration)
        
    # 3. STAGE 2: Dynamic Topic-Driven Visual Storyboarding & Rendering
    print("[3/4] STAGE 2: Generating Dynamic Visual Storyboard & Procedural 2D/3D Motion Video...")
    storyboard = generate_stage_2_storyboard(clean_narration, episode_num, topic)
    
    with open(storyboard_file, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, indent=2)
        
    video_engine.render_dynamic_video(
        storyboard,
        clean_narration,
        audio_file,
        video_file,
        episode_title=f"EP_{episode_num}: {topic}"
    )
    
    # 4. Telegram Delivery
    print("[4/4] Delivering Assets to Telegram...")
    caption = "🎬 Kissa-E-Machine: Fresh Dynamic Visual Engine [Verified Test]"
    
    telegram_service.send_message(
        f"🎬 <b>KISSA-E-MACHINE: Episode {episode_num} Ready!</b>\n"
        f"📌 <b>{topic}</b>\n\n"
        f"📜 <b>Spoken Script:</b>\n<i>\"{clean_narration}\"</i>"
    )
    
    telegram_service.send_audio(
        audio_file,
        caption=f"🎙️ Episode {episode_num} Conversational Voiceover: {topic}",
        title=f"Kissa-e-Machine EP{episode_num}",
        performer="Prava Studio"
    )
    
    telegram_service.send_video(
        video_file,
        caption=caption
    )
    
    telegram_service.send_document(
        blueprint_file,
        caption=f"📐 Master Video Blueprint EP_{episode_num}",
        mime_type="text/plain"
    )
    
    # Update pipeline state
    if not dry_run:
        next_ep = episode_num + 1
        state["last_topic"] = topic
        state["current_episode"] = next_ep
        state["next_topic"] = SEQUENTIAL_TOPICS.get(next_ep, f"Advanced Transformer Part {next_ep}")
        state["history"].append({
            "episode_number": episode_num,
            "topic": topic,
            "analogy_used": f"Dynamic physical metaphor for {topic}",
            "completed_at": datetime.now().isoformat(),
            "video_path": video_file,
            "audio_path": audio_file
        })
        save_pipeline_state(state)
        print(f"✅ Episode {episode_num} pipeline finished successfully! Advanced to Episode {next_ep}.")
    else:
        print(f"✅ Episode {episode_num} dry run finished successfully! Pipeline state preserved.")
        
    return {
        "episode": episode_num,
        "topic": topic,
        "audio_path": audio_file,
        "video_path": video_file,
        "blueprint_path": blueprint_file,
        "narration": clean_narration
    }

if __name__ == "__main__":
    import sys
    target = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_episode_pipeline(target, dry_run=False)
