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
    27: "Feed-Forward Layers & Long-Term Memory Storage"
}

# Locked Master Narrative Matrix: Analogies, Anchors, and Cliffhangers
EPISODE_METADATA = {
    22: {
        "yesterday_anchor": "How do you search for meaning inside high-dimensional vector spaces without losing your mind?",
        "mandatory_analogy": "The chaotic Indian wedding hall: Uncle ji arguing politics, blasting dhol, kids shrieking. The exact microsecond someone whispers 'Biryani ready hai' or calls your name, your brain filters out 99 conversations and spotlights that single plate of rice.",
        "technical_core": "Query (the hunger), Key (labels in the room), Dot Product (the matching spark), Value (the plate of rice).",
        "tomorrow_cliffhanger": "What happens when a word stops listening to the room, looks in the mirror, and attends to itself? That's Self-Attention."
    },
    23: {
        "yesterday_anchor": "Yesterday, we saw how attention acts like a spotlight filtering out background noise.",
        "mandatory_analogy": "The intense team brainstorming huddle or chaotic dinner table: someone drops a confusing comment like 'Bank' and everyone around the table shouts context clues—'River!' or 'Money!'—until its true meaning crystallizes in parallel.",
        "technical_core": "Every word in the sentence queries every other word at the exact same millisecond, calculating a dot-product handshake to absorb context.",
        "tomorrow_cliffhanger": "What happens if one dinner conversation isn't enough? What if eight different tables are debating simultaneously? That's Multi-Head Attention."
    },
    24: {
        "yesterday_anchor": "Yesterday, red yarn on a detective board showed words connecting to each other.",
        "mandatory_analogy": "The sports broadcast multi-camera crew: One camera locks onto the batsman's footwork, another watches the bowler's wrist spin, a third sweeps the outfield boundary. 8 distinct specialized camera heads watching the exact same play from 8 angles at once.",
        "technical_core": "8 parallel attention matrices projecting vectors into different subspaces, capturing syntax, tone, and long-range logic simultaneously.",
        "tomorrow_cliffhanger": "Now you've got 8 brilliant perspectives... but how do you fuse them into an engine that can actually think and generate? That's the Transformer."
    },
    25: {
        "yesterday_anchor": "Yesterday, 8 specialized camera heads gave our AI parallel vision.",
        "mandatory_analogy": "The two-star Michelin kitchen relay: The Encoder is the prep-station sous-chef digesting raw paragraphs into rich contextual flavor stocks; the Decoder is the master plating chef assembling the final course word-by-word, glancing back at the stock pot.",
        "technical_core": "Encoder processes the whole sequence in parallel; Decoder autoregressively generates tokens using cross-attention back into the encoder stack.",
        "tomorrow_cliffhanger": "Wait, if the chef cooks all the words simultaneously, how does the model know the difference between 'dog bites man' and 'man bites dog'? It has no concept of order!"
    },
    26: {
        "yesterday_anchor": "Yesterday, the Transformer cooked the whole sentence at once, but went completely blind to word order.",
        "mandatory_analogy": "Clock gears and stamped airline boarding passes: Since matrix math is timeless, we stamp every passenger with an oscillating wave code—a high-frequency sine gear and a low-frequency cosine gear—telling math the exact seat in time.",
        "technical_core": "Sinusoidal positional encoding vectors added directly to token embeddings, preserving geometric distance between positions.",
        "tomorrow_cliffhanger": "Now words have context and order... but where does the AI store real-world facts? Who remembers that Paris is in France?"
    },
    27: {
        "yesterday_anchor": "Yesterday, harmonic sine waves taught geometry how to tell time.",
        "mandatory_analogy": "The massive wooden library card catalog: Once attention decides which words matter, the Feed-Forward layer is where each token walks up to a two-layer filing cabinet, pulls open the drawer, and grabs factual world knowledge.",
        "technical_core": "Two-layer MLP with non-linear activation acting as key-value associative factual memory storage.",
        "tomorrow_cliffhanger": "What happens when you stack 96 of these layers with hundreds of billions of weights? Emergence. The machine starts to reason."
    }
}

def load_pipeline_state():
    if not os.path.exists(PIPELINE_STATE_FILE):
        state = {
            "current_episode": 22,
            "last_topic": "Vector Embeddings",
            "next_topic": SEQUENTIAL_TOPICS[22],
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

def generate_script_and_blueprint(episode_num, topic):
    meta = EPISODE_METADATA.get(episode_num, {
        "yesterday_anchor": f"Yesterday's cliffhanger brought us to the edge of neural architectures.",
        "mandatory_analogy": "A physical machine, postal sorting hub, or detective clue board.",
        "technical_core": "Core computational transformation in plain English.",
        "tomorrow_cliffhanger": "Tease the next evolutionary leap in the architecture."
    })
    
    system_instruction = (
        "You are the lead creator and master storyteller of 'Kissa-e-Machine'. "
        "Your voice: high-retention, peer-to-peer developer voice (like two senior engineers talking over Chai). "
        "STRICT CARDINAL RULES FOR EVERY GENERATION:\n"
        "1. ZERO SERIALIZATION: Strictly ban callbacks ('Yesterday we saw...', 'In the last part...', 'Continuing our series...'). Every reel must be a 100% self-contained standalone asset.\n"
        "2. HOOK (0–3s): Fast-paced, problem-first Hinglish placing the developer or machine in tension. Banned openers: 'Ever wondered...', 'What is...', 'Today we will learn...'. Example: 'Jab aap ek lamba prompt dete ho, toh model pehle words ko bhool kyun jaata hai?'\n"
        "3. TONE & JARGON: Zero raw textbook math/CS terms without an immediate punchline. Relatable, energetic, intellectual.\n"
        "4. SHARE TRIGGER (Seconds 15–35): Feature at least one counter-intuitive mental model tailored for WhatsApp/Discord sharing.\n"
        "5. BRAND PRONUNCIATION: Always write 'Prah-va' so speech engines never mispronounce it as 'Brava'.\n"
        "6. RUNTIME: 45 to 55 seconds spoken delivery (~115-135 words)."
    )
    
    prompt = f"""
Create the complete production package for Episode {episode_num} of "KISSA-E-MACHINE".
TOPIC: "{topic}"

NARRATIVE SPECIFICATIONS FOR THIS EPISODE:
- Yesterday's Anchor: {meta['yesterday_anchor']}
- Mandatory Relatable Analogy: {meta['mandatory_analogy']}
- Technical Core to demystify: {meta['technical_core']}
- Tomorrow's Cliffhanger: {meta['tomorrow_cliffhanger']}

SCRIPT STRUCTURE (45 to 50 seconds spoken delivery, ~115-135 words):
1. Provocative/counter-intuitive hook (Connect to yesterday's cliffhanger with a sharp question).
2. Grounded, vivid physical analogy (The emotional heart of the video).
3. The technical breakdown translated into plain English (No sterile textbook jargon).
4. The mathematical punchline (The spotlight / vector resonance).
5. Next-episode cliffhanger + Prava CTA ("Follow Prava, and keep questioning the machine").
6. Frequent delivery cues every 2-4 seconds:
   `[0:00 - 0:02 | Hook: Intense direct eye contact, sharp curious delivery]`
   `[0:02 - 0:04 | Micro-pause: Knowing smile, tilt chin down]`

MASTER VIDEO EDITING BLUEPRINT:
- Visual Style: Kurzgesagt / Vox High-Precision Scientific Flat Motion Design.
- 100% 2D vector forms, coordinate grids, celestial node clusters. ZERO stock footage, ZERO generic cyber clichés.
- Strict Palette:
  * Prussian Ink (#0B192C) - Background
  * Basalt Slate (#161B22) - Secondary geometric structures / axes / inactive nodes
  * Solar Flare Amber (#F77F00) - Primary focal vectors / search rays
  * Terracotta Coral (#E63946) - Attention spark / focal target ignition
  * Forest Sage (#2A9D8F) - Stabilized context & key matrices
  * Warm Cream (#FDF0D5) - Typography & mathematical equation overlays
- Complete scene-by-scene breakdown with Camera physics (smooth zooms, lateral pans) and tactile SFX cues.

Format your output with clear markdown headings:
# EPISODE {episode_num}: {topic}
## 1. SPOKEN SCRIPT & DELIVERY CUES
## 2. MASTER VIDEO EDITING BLUEPRINT
## 3. CLEAN SPOKEN NARRATION (Spoken words ONLY, no timestamps or stage cues)
"""
    response_text = gemini_service.generate_text(prompt, system_instruction, temperature=0.7)
    banned_words = ["dot product", "matrices", "vectors", "query", "key", "value", "embeddings", "mathematical handshake"]
    if response_text and any(bw in response_text.lower() for bw in banned_words):
        print("[KissaMachine] Generated text contained banned jargon. Enforcing locked zero-jargon master script.")
        response_text = None
    if not response_text:
        response_text = get_locked_fallback_content(episode_num, topic)
    return response_text

def get_locked_fallback_content(episode_num, topic):
    meta = EPISODE_METADATA.get(episode_num, EPISODE_METADATA[22])
    
    if episode_num == 22:
        return f"""# EPISODE 22: {topic}

## 1. SPOKEN SCRIPT & DELIVERY CUES
[0:00 - 0:03 | Hook: Intense direct eye contact, sharp curious delivery]
Ever wonder why your brain treats the word "The" like background noise, but "Free" like a siren?

[0:03 - 0:05 | Micro-pause: Knowing smile, tilt chin down]
Old AI treated every single word like an equal citizen. It was an absolute disaster.

[0:05 - 0:13 | Hands gesturing wide, mimicking a chaotic room]
Imagine a loud Indian wedding. Uncle ji is arguing politics, the dhol is deafening, and kids are shrieking. Total chaotic acoustic overload.

[0:13 - 0:19 | Shift: Lean in closer to the lens, whisper-adjacent tone]
But the second someone whispers, "Biryani ready hai," the entire room vanishes. Your brain shuts out ninety-nine voices and beams a spotlight on that single plate of rice.

[0:19 - 0:25 | Hand mimics holding an object, moving it across the frame]
In AI, that spotlight is called 'Attention.' It uses three simple things: a Query, a Key, and a Value.

[0:25 - 0:35 | Rapid-fire but clear, counting on fingers]
The Query is what you're hungry for. The Key is the tag on every word in the room. When they align? That's a 'Dot Product'—a mathematical spark that says: "Ignore the Uncle, focus on the Biryani."

[0:35 - 0:43 | Relax shoulders, expansive hand gesture]
The Value is the actual information you extract. Words no longer sit isolated; they look across the entire sentence and focus.

[0:43 - 0:46 | Cliffhanger: Raised eyebrow, playful tone]
Next time: what happens when a word looks in the mirror and attends to itself? That's Self-Attention.

[0:46 - 0:49 | Outro: Signature Prava nod, fade to black]
Follow Prava, and keep questioning the machine.

## 2. MASTER VIDEO EDITING BLUEPRINT
### Visual Style: Kurzgesagt / Vox High-Precision Scientific Flat Motion Design
- Color Palette:
  * Prussian Ink (#0B192C) - Endless void background
  * Basalt Slate (#161B22) - Geometric coordinate grid and inactive ambient nodes
  * Solar Flare Amber (#F77F00) - The active Query search ray
  * Terracotta Coral (#E63946) - The ignition of the attention hit ("Biryani / Target Word")
  * Forest Sage (#2A9D8F) - Surrounding Key/Value contextual clusters
  * Warm Cream (#FDF0D5) - Typography and mathematical equation overlays

### Scene-by-Scene Breakdown:
- Scene 1 (0:00 - 0:05 | The Sensory Overload):
  * Visual: Prussian Ink (#0B192C) background with dense Basalt Slate (#161B22) coordinate lines. Bouncing speech vectors frantically vibrating.
  * Camera: Subtle high-frequency vibration mimicking acoustic overload.
  * SFX: Layered muffled crowd murmurs and quiet vinyl crackle.
- Scene 2 (0:05 - 0:19 | The Biryani Filter):
  * Visual: Ambient nodes dim to 10% opacity. A brilliant Terracotta Coral (#E63946) node labeled "Biryani / Target" pulses at center coordinates.
  * Camera: Smooth snap zoom onto the focal node.
  * SFX: Crisp mechanical tactile click followed by a warm resolving bass drop.
- Scene 3 (0:19 - 0:35 | The Q-K-V Triad Mechanics):
  * Visual: Glowing amber (#F77F00) radar sweep (Query) intersects key nodes in Forest Sage (#2A9D8F). Dot product sparks in Terracotta Coral.
  * Formula HUD: Mathematical HUD in Warm Cream (#FDF0D5): Attention(Q,K,V) = softmax( (Q · Kᵀ) / √dₖ ) · V.
  * Camera: Lateral tracking along the spotlight beam.
  * SFX: High-tech frequency sweep and tactile synthesizer chime.
- Scene 4 (0:35 - 0:49 | The Spotlight Lattice & Outro):
  * Visual: Coordinated spotlight rays form a multidimensional lattice of mutual intelligence. Prava logo icon glides smoothly into center.
  * Camera: Slow cinematic pull-back revealing the full mathematical constellation.
  * SFX: Warm harmonic synthesizer chord fading cleanly into silence.

## 3. CLEAN SPOKEN NARRATION
Ever wonder why your brain treats the word "The" like background noise, but "Free" like a siren? Old AI treated every single word like an equal citizen. It was an absolute disaster. Imagine a loud Indian wedding. Uncle ji is arguing politics, the dhol is deafening, and kids are shrieking. Total chaotic acoustic overload. But the second someone whispers, "Biryani ready hai," the entire room vanishes. Your brain shuts out ninety-nine voices and beams a spotlight on that single plate of rice. In AI, that spotlight is called 'Attention.' It uses three simple things: a Query, a Key, and a Value. The Query is what you're hungry for. The Key is the tag on every word in the room. When they align? That's a 'Dot Product'—a mathematical spark that says: "Ignore the Uncle, focus on the Biryani." The Value is the actual information you extract. Words no longer sit isolated; they look across the entire sentence and focus. Next time: what happens when a word looks in the mirror and attends to itself? That's Self-Attention. Follow Prava, and keep questioning the machine.
"""
    elif episode_num == 23:
        return f"""# EPISODE 23: {topic}

## 1. SPOKEN SCRIPT & DELIVERY CUES
[0:00 - 0:03 | Hook: Intense direct eye contact, sharp curious delivery]
If I whisper the single word "Bank"... what picture popped into your head? A vault of cash? Or a muddy riverbank?

[0:03 - 0:05 | Micro-pause: Knowing smile, tilt chin down]
You can't decide. Because isolated words are completely clueless.

[0:05 - 0:17 | Conversational, energetic storytelling gesture, leaning in]
Picture a loud family dinner table. Someone mumbles the word "Bank". If you read one word at a time, you're totally in the dark.

[0:17 - 0:28 | Bright animated cadence, mimicking people nodding around a table]
But modern AI listens to everyone around the table at the exact same second. Across the table, the word "River" waves its hand. Next to it, "Water" nods.

[0:28 - 0:38 | Confident resolving energy, open hands coming together]
Instantly, the whole table agrees on what "Bank" means. That's Self-Attention—words gossiping with each other until all the confusion simply disappears.

[0:38 - 0:44 | Outro: Raised eyebrow, playful smirk]
Next time: what if one dinner conversation isn't enough? What if eight different tables are debating simultaneously?

[0:44 - 0:48 | Confident nod, direct eye contact]
Follow Prah-va, and keep questioning the machine.

## 2. MASTER VIDEO EDITING BLUEPRINT
### Visual Style: Kurzgesagt / Vox High-Precision Scientific Flat Motion Design
- Color Palette:
  * Prussian Ink (#0B192C) - Endless void dinner table coordinates
  * Basalt Slate (#161B22) - Secondary geometric coordinate grid & ambient nodes
  * Solar Flare Amber (#F77F00) - Active conversation pulse originating from "Bank"
  * Terracotta Coral (#E63946) - High-resonance gossip sparks connecting "Bank" to "River"
  * Forest Sage (#2A9D8F) - Stabilized surrounding context nodes ("River", "Water")
  * Warm Cream (#FDF0D5) - Word labels, HUD metrics, and dynamic captions

### Scene Breakdown:
1. The Clueless Word (0:00 - 0:05): A lone Basalt Slate node labeled "Bank" floating aimlessly on Prussian Ink grid. A question mark pulses in Solar Flare Amber.
2. The Dinner Table Shouting Clues (0:05 - 0:17): Multiple nodes pop up in a circle ("River", "Water", "Fish", "Cash", "Vault"). Directional sound wave vectors ripple across the table.
3. The Self-Attention Gossip Sparks (0:17 - 0:28): "River" and "Water" flash bright Sage and Amber. Glowing electric arcs shoot across the table to "Bank" with thick 6px pulsing strokes.
4. Crystallized Meaning & Outro (0:28 - 0:48): The "Bank" node morphs and illuminates in Forest Sage and Terracotta Coral, fully contextualized. 8 parallel table rings appear in the background teasing Multi-Head Attention. Smooth pull-back with Prah-va watermark.

## 3. CLEAN SPOKEN NARRATION
If I whisper the single word "Bank"... what picture popped into your head? A vault of cash? Or a muddy riverbank? You can't decide. Because isolated words are completely clueless. Picture a loud family dinner table. Someone mumbles the word "Bank". If you read one word at a time, you're totally in the dark. But modern AI listens to everyone around the table at the exact same second. Across the table, the word "River" waves its hand. Next to it, "Water" nods. Instantly, the whole table agrees on what "Bank" means. That's Self-Attention—words gossiping with each other until all the confusion simply disappears. Next time: what if one dinner conversation isn't enough? What if eight different tables are debating simultaneously? Follow Prah-va, and keep questioning the machine.
"""
    elif episode_num == 25:
        return f"""# EPISODE 25: {topic}

## 1. SPOKEN SCRIPT & DELIVERY CUES
[0:00 - 0:03 | Hook: Intense direct eye contact, sharp urgent Hinglish delivery]
Jab aap ChatGPT ko hazaar line ka code dete ho, toh model bina confuse huye har ek line ka context kaise yaad rakhta hai?

[0:03 - 0:06 | Micro-pause: Knowing smirk, tilt chin down]
Pehle ke AI models ek-ek word padhte the, jaise ek slow typewriter. Aakhiri line tak aate-aate shuru ka sab bhool jaate the!

[0:06 - 0:18 | Conversational storytelling gesture, leaning in over chai]
Enter: The Transformer Architecture. Isko ek two-star Michelin kitchen relay ki tarah socho.

[0:18 - 0:34 | Sharp, animated hand motions separating left and right stations - SHARE TRIGGER]
Left side par hai Encoder—hamara master sous-chef. Ye poore raw prompt ko ek second mein analyze karke ek super-dense flavor stock pot bana deta hai. 
Right side par hai Decoder—plating chef. Ye final answer ka har word ek-ek karke plate par sajata hai.

[0:34 - 0:46 | Expansive resolution, hands locking together in handshake]
Lekin har naya word rakhne se pehle, Decoder sous-chef ke stock pot mein chamach daal kar taste karta hai: 'Kya ye context se match hua?' Is double-handshake ko kehte hain Cross-Attention.

[0:46 - 0:52 | Confident nod, direct lens contact]
Har generative AI ka dimaag yehi high-speed kitchen hai. Follow Prah-va, and keep questioning the machine.

## 2. MASTER VIDEO EDITING BLUEPRINT
### Visual Style: 2.5D Isometric Multi-Scene Motion Design
- Scene 1 (0:00 - 0:10): 3D Server rack intake funnelling thousands of raw streaming tokens.
- Scene 2 (0:10 - 0:22): 6-Layer Isometric Encoder stack condensing information into glowing core stock pot.
- Scene 3 (0:22 - 0:35): 3D Decoder assembly line generating tokens autoregressively with robotic plating arm.
- Scene 4 (0:35 - 0:46): High-voltage Cross-Attention laser rail linking Encoder pot to Decoder arm with 99.8% match lock.
- Scene 5 (0:46 - End): Holographic Transformer fusion core pull-back with dynamic amber lens flare.

## 3. CLEAN SPOKEN NARRATION
Jab aap ChatGPT ko hazaar line ka code dete ho, toh model bina confuse huye har ek line ka context kaise yaad rakhta hai? Pehle ke AI models ek-ek word padhte the, jaise ek slow typewriter. Aakhiri line tak aate-aate shuru ka sab bhool jaate the! Enter: The Transformer Architecture. Isko ek two-star Michelin kitchen relay ki tarah socho. Left side par hai Encoder—hamara master sous-chef. Ye poore raw prompt ko ek second mein analyze karke ek super-dense flavor stock pot bana deta hai. Right side par hai Decoder—plating chef. Ye final answer ka har word ek-ek karke plate par sajata hai. Lekin har naya word rakhne se pehle, Decoder sous-chef ke stock pot mein chamach daal kar taste karta hai: 'Kya ye context se match hua?' Is double-handshake ko kehte hain Cross-Attention. Har generative AI ka dimaag yehi high-speed kitchen hai. Follow Prah-va, and keep questioning the machine.
"""
    else:
        # Template for EP 24, 26, 27
        return f"""# EPISODE {episode_num}: {topic}

## 1. SPOKEN SCRIPT & DELIVERY CUES
[0:00 - 0:03 | Hook: Intense direct eye contact, sharp curious delivery]
{meta['yesterday_anchor']}

[0:03 - 0:05 | Micro-pause: Knowing smile, tilt chin down]

[0:05 - 0:18 | Conversational storytelling gesture]
{meta['mandatory_analogy']}

[0:18 - 0:32 | Plain English technical breakdown]
{meta['technical_core']}

[0:32 - 0:42 | Mathematical punchline, deliberate emphasis]
The architecture doesn't just calculate numbers; it builds a multidimensional lattice of pure relational intelligence.

[0:42 - 0:46 | Cliffhanger: Raised eyebrow, playful smirk]
{meta['tomorrow_cliffhanger']}

[0:46 - 0:49 | Outro: Signature Prava nod, fade to black]
Follow Prava, and keep questioning the machine.

## 2. MASTER VIDEO EDITING BLUEPRINT
### Visual Style: Kurzgesagt / Vox High-Precision Scientific Flat Motion Design
- Color Palette:
  * Prussian Ink (#0B192C) - Background
  * Basalt Slate (#161B22) - Geometric coordinate grid
  * Solar Flare Amber (#F77F00) - Primary focal vectors
  * Terracotta Coral (#E63946) - Attention sparks
  * Forest Sage (#2A9D8F) - Context clusters
  * Warm Cream (#FDF0D5) - Typography and mathematical equation overlays

### Scene-by-Scene Breakdown:
1. Scene 1 (0:00 - 0:10): The Problem Void. Coordinate grid in #161B22 on #0B192C.
2. Scene 2 (0:10 - 0:25): The Physical Analogy in Motion.
3. Scene 3 (0:25 - 0:38): The Vector Mechanics & HUD overlay.
4. Scene 4 (0:38 - 0:49): The Synthesized Lattice and Cliffhanger Tease.

## 3. CLEAN SPOKEN NARRATION
{meta['yesterday_anchor']} {meta['mandatory_analogy']} {meta['technical_core']} The architecture doesn't just calculate numbers; it builds a multidimensional lattice of pure relational intelligence. {meta['tomorrow_cliffhanger']} Follow Prava, and keep questioning the machine.
"""

def run_episode_pipeline(target_episode=None, dry_run=False):
    state = load_pipeline_state()
    if target_episode is None:
        episode_num = state.get("current_episode", 22)
    else:
        episode_num = target_episode
        
    topic = SEQUENTIAL_TOPICS.get(episode_num, state.get("next_topic", f"Advanced Architecture Part {episode_num}"))
    
    print(f"\n=======================================================")
    print(f"🎬 KISSA-E-MACHINE: Executing Episode {episode_num}")
    print(f"📌 Topic: {topic}")
    print(f"=======================================================")
    
    ep_dir = os.path.join(OUTPUT_DIR, f"EP_{episode_num}")
    os.makedirs(ep_dir, exist_ok=True)
    
    script_file = os.path.join(ep_dir, "script.txt")
    blueprint_file = os.path.join(ep_dir, "blueprint.md")
    audio_file = os.path.join(ep_dir, "voiceover.mp3")
    video_file = os.path.join(ep_dir, "video.mp4")
    
    # 1. Script & Blueprint Generation (Locked Template)
    print("[1/4] Generating Script with Kissa-e-Machine Soul & Master Blueprint...")
    content = generate_script_and_blueprint(episode_num, topic)
    
    with open(blueprint_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    # 2. Voiceover Synthesis via Gemini Studio HD Voice (Aoede)
    print("[2/4] Synthesizing Voiceover using Gemini HD Studio Voice (Aoede)...")
    clean_narration = tts_service.generate_voiceover(content, audio_file, voice_name="Aoede")
    
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(clean_narration)
        
    # 3. Video Rendering
    print("[3/4] Rendering Master Flat-Motion Video with Dynamic Captions (Kurzgesagt/Vox style)...")
    video_engine.render_motion_video(episode_num, topic, audio_file, video_file, script_text=clean_narration)
    
    # 4. Telegram Delivery
    print("[4/4] Delivering Assets to Telegram...")
    caption = "🎬 Kissa-E-Machine: Standalone Production Engine [Verified Cloud Run]"
    
    # Send script summary / announcement
    telegram_service.send_message(
        f"🎬 <b>KISSA-E-MACHINE: Episode {episode_num} Ready!</b>\n"
        f"📌 <b>{topic}</b>\n\n"
        f"📜 <b>Spoken Script:</b>\n<i>\"{clean_narration}\"</i>"
    )
    
    # Send Voiceover MP3
    telegram_service.send_audio(
        audio_file,
        caption=f"🎙️ Episode {episode_num} HD Studio Voiceover (Aoede): {topic}",
        title=f"Kissa-e-Machine EP{episode_num}",
        performer="Prava Studio (Aoede)"
    )
    
    # Send Video MP4
    telegram_service.send_video(
        video_file,
        caption=caption
    )
    
    # Send Blueprint as Document
    telegram_service.send_document(
        blueprint_file,
        caption=f"📐 Master Video Blueprint EP_{episode_num}",
        mime_type="text/plain"
    )
    
    # If not dry run, advance state
    if not dry_run:
        next_ep = episode_num + 1
        state["last_topic"] = topic
        state["current_episode"] = next_ep
        state["next_topic"] = SEQUENTIAL_TOPICS.get(next_ep, f"Advanced Transformer Part {next_ep}")
        state["history"].append({
            "episode_number": episode_num,
            "topic": topic,
            "completed_at": datetime.now().isoformat(),
            "video_path": video_file,
            "audio_path": audio_file
        })
        save_pipeline_state(state)
        print(f"✅ Episode {episode_num} pipeline finished successfully! Advanced to Episode {next_ep}.")
    else:
        print(f"✅ Episode {episode_num} dry run finished successfully! Pipeline state preserved at Episode {episode_num}.")
        
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
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 23
    run_episode_pipeline(target, dry_run=False)
