import os
import math
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 6-Color Scientific Motion Palette (Vox / Kurzgesagt Style)
COLOR_PRUSSIAN_INK = (11, 25, 44)       # #0B192C (Deep void backdrop)
COLOR_BASALT_SLATE = (22, 27, 34)       # #161B22 (Secondary structure & dark outline)
COLOR_SOLAR_AMBER  = (247, 127, 0)      # #F77F00 (Vibrant Golden Amber - Active Head & Highlight)
COLOR_CORAL        = (230, 57, 70)      # #E63946 (Terracotta Coral - Alert & Focus)
COLOR_FOREST_SAGE  = (42, 157, 143)     # #2A9D8F (Contextual Forest Sage)
COLOR_WARM_CREAM   = (253, 240, 213)    # #FDF0D5 (Warm Cream Typography)
COLOR_CRISP_WHITE  = (255, 255, 255)    # #FFFFFF (Clean Subtitles & Bright Highlights)
COLOR_CYAN_GLOW    = (0, 212, 255)      # Technical beam & tracking reticle
COLOR_DARK_SHADOW  = (16, 22, 34)       # #101622 (Solid drop shadow & stroke)

def get_audio_duration(audio_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"[VideoEngine] Error reading audio duration: {e}")
        return 50.0

def build_caption_timeline(script_text, total_duration):
    words = script_text.split()
    total_words = len(words)
    if total_words == 0:
        return []
        
    time_per_word = total_duration / total_words
    chunks = []
    current_chunk = []
    
    for i, w in enumerate(words):
        current_chunk.append((w, i * time_per_word, (i + 1) * time_per_word))
        is_break = any(w.endswith(p) for p in [".", "?", "!", "—", ",", "..."])
        if len(current_chunk) >= 5 or (len(current_chunk) >= 3 and is_break) or i == total_words - 1:
            chunk_start = current_chunk[0][1]
            chunk_end = current_chunk[-1][2]
            chunks.append({
                "words": [cw[0] for cw in current_chunk],
                "word_starts": [cw[1] for cw in current_chunk],
                "word_ends": [cw[2] for cw in current_chunk],
                "start": chunk_start,
                "end": chunk_end
            })
            current_chunk = []
            
    return chunks

def get_fonts():
    # Load system or fallback fonts
    font_candidates = [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\seguiemj.ttf",
        "C:\\Windows\\Fonts\\consola.ttf"
    ]
    header_font = None
    subhead_font = None
    small_font = None
    mono_font = None
    caption_font = None
    time_font = None
    
    for p in font_candidates:
        if os.path.exists(p):
            try:
                header_font = ImageFont.truetype(p, 42)
                subhead_font = ImageFont.truetype(p, 26)
                small_font = ImageFont.truetype(p, 22)
                mono_font = ImageFont.truetype(p, 20)
                caption_font = ImageFont.truetype(p, 46)
                time_font = ImageFont.truetype(p, 22)
                break
            except Exception:
                pass
                
    if header_font is None:
        default = ImageFont.load_default()
        header_font = default
        subhead_font = default
        small_font = default
        mono_font = default
        caption_font = default
        time_font = default
        
    return {
        "header": header_font,
        "subhead": subhead_font,
        "small": small_font,
        "mono_small": mono_font,
        "caption": caption_font,
        "time": time_font
    }

def draw_perspective_grid(draw, width, height, t, drift_speed=1.5):
    """Clean technical perspective grid with continuous camera drift."""
    drift_x = int(math.sin(t * drift_speed) * 25)
    drift_y = int(math.cos(t * drift_speed * 0.8) * 15)
    draw.rectangle([0, 0, width, height], fill=COLOR_PRUSSIAN_INK)
    for gx in range(-150, width + 150, 80):
        draw.line([(gx + drift_x, 0), (gx + drift_x + 300, height)], fill=(16, 26, 42), width=1)
        draw.line([(gx + drift_x + 300, 0), (gx + drift_x, height)], fill=(16, 26, 42), width=1)
    return drift_x, drift_y

def render_scene_order_chaos(draw, width, height, t, scene_meta, fonts):
    """
    SCENE: ORDER CHAOS / THE BAG OF WORDS TRAP
    Visualizes the fundamental problem: words arriving unordered in parallel.
    Flipping comparison tiles ('DOG BITES MAN' vs 'MAN BITES DOG') with alert beacons.
    """
    drift_x, drift_y = draw_perspective_grid(draw, width, height, t, drift_speed=2.0)
    cx, cy = width // 2 + drift_x // 2, 530 + drift_y // 2
    
    # Header HUD
    title = scene_meta.get("title", "THE BAG OF WORDS TRAP")
    subtitle = scene_meta.get("subtitle", "Order Confusion: 'Dog Bites Man' vs 'Man Bites Dog'")
    draw.text((width // 2, 170), title, fill=COLOR_CORAL, font=fonts["header"], anchor="mm")
    draw.text((width // 2, 220), subtitle, fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
    
    # Alert Warning Box
    pulse = 0.5 + 0.5 * math.sin(t * 8.0)
    box_col = COLOR_CORAL if pulse > 0.4 else COLOR_BASALT_SLATE
    draw.rounded_rectangle([cx - 320, 260, cx + 320, 310], radius=8, fill=(18, 22, 34), outline=box_col, width=2)
    draw.text((cx, 285), "⚠️ ALERT: PARALLEL TOKENS LACK TEMPORAL ORDER", fill=COLOR_CORAL, font=fonts["small"], anchor="mm")
    
    # Two Conflicting Word Sequences flipping and colliding
    flip_cycle = math.sin(t * 3.5)
    y_seq1 = cy - 80
    y_seq2 = cy + 80
    
    # Sentence 1: DOG -> BITES -> MAN
    s1_tokens = ["DOG", "BITES", "MAN"]
    s2_tokens = ["MAN", "BITES", "DOG"]
    
    s1_x_offset = int(flip_cycle * 60)
    for i, tok in enumerate(s1_tokens):
        bx = cx - 220 + i * 220 + s1_x_offset
        by = y_seq1
        col = COLOR_SOLAR_AMBER if tok == "DOG" else COLOR_FOREST_SAGE
        draw.rounded_rectangle([bx - 80, by - 35, bx + 80, by + 35], radius=10, fill=COLOR_BASALT_SLATE, outline=col, width=3)
        draw.text((bx, by), tok, fill=COLOR_CRISP_WHITE, font=fonts["small"], anchor="mm")
        # Position index tag
        draw.text((bx, by - 55), f"pos: ?", fill=(160, 180, 200), font=fonts["mono_small"], anchor="mm")
        
    # Sentence 2: MAN -> BITES -> DOG
    s2_x_offset = -int(flip_cycle * 60)
    for i, tok in enumerate(s2_tokens):
        bx = cx - 220 + i * 220 + s2_x_offset
        by = y_seq2
        col = COLOR_CORAL if tok == "MAN" else COLOR_FOREST_SAGE
        draw.rounded_rectangle([bx - 80, by - 35, bx + 80, by + 35], radius=10, fill=COLOR_BASALT_SLATE, outline=col, width=3)
        draw.text((bx, by), tok, fill=COLOR_CRISP_WHITE, font=fonts["small"], anchor="mm")
        draw.text((bx, by + 55), f"pos: ?", fill=(160, 180, 200), font=fonts["mono_small"], anchor="mm")
        
    # Question mark energy rays between colliding concepts
    draw.line([(cx, y_seq1 + 40), (cx, y_seq2 - 40)], fill=COLOR_CORAL, width=3)
    draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=COLOR_PRUSSIAN_INK, outline=COLOR_WARM_CREAM, width=2)
    draw.text((cx, cy), "≠", fill=COLOR_CORAL, font=fonts["header"], anchor="mm")

def render_scene_conveyor_flow(draw, width, height, t, scene_meta, fonts):
    """
    SCENE: THE 3D ISOMETRIC CONVEYOR BELT / PARALLEL LUGGAGE TRACK
    Represents the physical metaphor: 50 items dumped on a belt simultaneously.
    """
    drift_x, drift_y = draw_perspective_grid(draw, width, height, t, drift_speed=1.5)
    cx, cy = width // 2, 540
    
    title = scene_meta.get("title", "THE PARALLEL CONVEYOR")
    subtitle = scene_meta.get("subtitle", "50 Tokens Loaded at the Same Exact Microsecond")
    draw.text((width // 2, 170), title, fill=COLOR_CYAN_GLOW, font=fonts["header"], anchor="mm")
    draw.text((width // 2, 220), subtitle, fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
    
    # 3D Conveyor Track (Left to Right isometric angle)
    draw.polygon([(100, cy + 140), (width - 100, cy - 80), (width - 100, cy - 20), (100, cy + 200)],
                 fill=(18, 28, 46), outline=COLOR_CYAN_GLOW, width=2)
    # Rollers along the track
    for r in range(12):
        frac = r / 11.0
        rx = int(100 + frac * (width - 200))
        ry = int((cy + 140) - frac * 220)
        draw.line([(rx, ry), (rx, ry + 60)], fill=(28, 44, 70), width=3)
        
    # Moving Token Packages / Luggage on Conveyor
    tokens = ["Token_0", "Token_1", "Token_2", "Token_3", "Token_4", "Token_5"]
    for i, tok in enumerate(tokens):
        pos = (t * 0.4 + i * 0.18) % 1.0
        px = int(140 + pos * (width - 280))
        py = int((cy + 160) - pos * 230)
        
        # Luggage / token block with 3D isometric sides
        draw.polygon([(px - 45, py), (px, py - 22), (px + 45, py), (px, py + 22)],
                     fill=COLOR_SOLAR_AMBER, outline=COLOR_WARM_CREAM, width=2)
        draw.polygon([(px - 45, py), (px, py + 22), (px, py + 50), (px - 45, py + 28)],
                     fill=(180, 90, 0), outline=COLOR_BASALT_SLATE)
        draw.polygon([(px + 45, py), (px, py + 22), (px, py + 50), (px + 45, py + 28)],
                     fill=(210, 110, 0), outline=COLOR_BASALT_SLATE)
        draw.text((px, py), f"#{i}", fill=COLOR_BASALT_SLATE, font=fonts["small"], anchor="mm")

def render_scene_harmonic_oscillator(draw, width, height, t, scene_meta, fonts):
    """
    SCENE: HARMONIC WAVE FREQUENCY GENERATOR
    Mathematical visualization of Sinusoidal Positional Encoding:
    Real-time high-frequency Sine wave + low-frequency Cosine wave rippling
    with laser stamping heads etching timecodes into passing tokens.
    """
    drift_x, drift_y = draw_perspective_grid(draw, width, height, t, drift_speed=1.0)
    cx = width // 2
    
    title = scene_meta.get("title", "HARMONIC FREQUENCY STAMP")
    subtitle = scene_meta.get("subtitle", "Sine (High Freq) + Cosine (Low Freq) Harmonic Clocks")
    draw.text((cx, 170), title, fill=COLOR_SOLAR_AMBER, font=fonts["header"], anchor="mm")
    draw.text((cx, 220), subtitle, fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
    
    # Formula HUD box
    draw.rounded_rectangle([cx - 340, 260, cx + 340, 310], radius=8, fill=(14, 20, 32), outline=COLOR_FOREST_SAGE, width=2)
    draw.text((cx, 285), "PE(pos, 2i) = sin(pos/10000^(2i/d))  |  PE(pos, 2i+1) = cos(pos/10000^(2i/d))",
              fill=COLOR_FOREST_SAGE, font=fonts["mono_small"], anchor="mm")
              
    sine_y_base = 450
    cosine_y_base = 650
    
    # 1. High-Frequency Sine Wave (Solar Flare Amber #F77F00)
    draw.text((100, sine_y_base - 55), "FAST CLOCK: HIGH-FREQ SINE (Seconds Gear)", fill=COLOR_SOLAR_AMBER, font=fonts["small"])
    sine_points = []
    for x in range(60, width - 60, 8):
        y = sine_y_base + int(45 * math.sin((x * 0.02) - (t * 5.0)))
        sine_points.append((x, y))
    for i in range(len(sine_points) - 1):
        draw.line([sine_points[i], sine_points[i+1]], fill=COLOR_SOLAR_AMBER, width=4)
        
    # 2. Low-Frequency Cosine Wave (Cyan Glow #00D4FF)
    draw.text((100, cosine_y_base - 55), "SLOW CLOCK: LOW-FREQ COSINE (Hours Gear)", fill=COLOR_CYAN_GLOW, font=fonts["small"])
    cosine_points = []
    for x in range(60, width - 60, 8):
        y = cosine_y_base + int(55 * math.cos((x * 0.007) - (t * 2.0)))
        cosine_points.append((x, y))
    for i in range(len(cosine_points) - 1):
        draw.line([cosine_points[i], cosine_points[i+1]], fill=COLOR_CYAN_GLOW, width=4)
        
    # Laser Stamping Heads tracking along the waves
    for stamp_i in range(3):
        stamp_x = int(240 + stamp_i * 300 + 40 * math.sin(t * 2.0 + stamp_i))
        s_y = sine_y_base + int(45 * math.sin((stamp_x * 0.02) - (t * 5.0)))
        c_y = cosine_y_base + int(55 * math.cos((stamp_x * 0.007) - (t * 2.0)))
        
        # Stamping beam
        draw.line([(stamp_x, s_y), (stamp_x, c_y)], fill=COLOR_WARM_CREAM, width=2)
        draw.ellipse([stamp_x - 8, s_y - 8, stamp_x + 8, s_y + 8], fill=COLOR_SOLAR_AMBER, outline=COLOR_CRISP_WHITE, width=2)
        draw.ellipse([stamp_x - 8, c_y - 8, stamp_x + 8, c_y + 8], fill=COLOR_CYAN_GLOW, outline=COLOR_CRISP_WHITE, width=2)
        
        # Stamped token badge
        badge_y = cosine_y_base + 95
        draw.rounded_rectangle([stamp_x - 55, badge_y - 20, stamp_x + 55, badge_y + 20],
                               radius=6, fill=COLOR_BASALT_SLATE, outline=COLOR_SOLAR_AMBER, width=2)
        draw.text((stamp_x, badge_y), f"POS #{stamp_i}", fill=COLOR_WARM_CREAM, font=fonts["mono_small"], anchor="mm")

def render_scene_vector_fusion(draw, width, height, t, scene_meta, fonts):
    """
    SCENE: VECTOR ADDITION CHAMBER
    Shows Word Embedding Vector directly adding to the Positional Encoding Vector:
    [Word Vector] + [Harmonic Wave Vector] = [Context-Aware Ordered Vector]
    """
    drift_x, drift_y = draw_perspective_grid(draw, width, height, t, drift_speed=1.5)
    cx, cy = width // 2, 530
    
    title = scene_meta.get("title", "VECTOR ADDITION CHAMBER")
    subtitle = scene_meta.get("subtitle", "Token Vector + Frequency Vector = Ordered Meaning")
    draw.text((cx, 170), title, fill=COLOR_CORAL, font=fonts["header"], anchor="mm")
    draw.text((cx, 220), subtitle, fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
    
    # Left: Word Meaning Vector
    left_x = cx - 260
    draw.rounded_rectangle([left_x - 130, cy - 70, left_x + 130, cy + 70],
                           radius=14, fill=(18, 28, 48), outline=COLOR_CYAN_GLOW, width=3)
    draw.text((left_x, cy - 20), "WORD EMBEDDING", fill=COLOR_CYAN_GLOW, font=fonts["small"], anchor="mm")
    draw.text((left_x, cy + 18), "[\"BIRYANI\": 512-dim]", fill=COLOR_WARM_CREAM, font=fonts["mono_small"], anchor="mm")
    
    # Plus Symbol
    draw.ellipse([cx - 75, cy - 25, cx - 25, cy + 25], fill=COLOR_BASALT_SLATE, outline=COLOR_WARM_CREAM, width=2)
    draw.text((cx - 50, cy), "+", fill=COLOR_WARM_CREAM, font=fonts["header"], anchor="mm")
    
    # Right: Positional Encoding Wave Vector
    right_x = cx + 200
    draw.rounded_rectangle([right_x - 130, cy - 70, right_x + 130, cy + 70],
                           radius=14, fill=(38, 28, 20), outline=COLOR_SOLAR_AMBER, width=3)
    draw.text((right_x, cy - 20), "POSITION VECTOR", fill=COLOR_SOLAR_AMBER, font=fonts["small"], anchor="mm")
    draw.text((right_x, cy + 18), "[sin/cos: 512-dim]", fill=COLOR_WARM_CREAM, font=fonts["mono_small"], anchor="mm")
    
    # Fusion Beam down to the Final Ordered Output
    arrow_y_start = cy + 90
    arrow_y_end = cy + 180
    draw.line([(cx, arrow_y_start), (cx, arrow_y_end)], fill=COLOR_WARM_CREAM, width=4)
    
    # Resulting Fused Vector Block
    pulse_w = int(12 + 6 * math.sin(t * 8.0))
    res_y = cy + 250
    draw.rounded_rectangle([cx - 280, res_y - 50, cx + 280, res_y + 50],
                           radius=16, fill=(14, 34, 28), outline=COLOR_FOREST_SAGE, width=3)
    draw.text((cx, res_y - 15), "ORDERED FINAL EMBEDDING", fill=COLOR_FOREST_SAGE, font=fonts["small"], anchor="mm")
    draw.text((cx, res_y + 18), "SAME 512-DIM VECTOR • ZERO LOST SLOTS", fill=COLOR_WARM_CREAM, font=fonts["mono_small"], anchor="mm")

def render_scene_synchronized_lattice(draw, width, height, t, scene_meta, fonts):
    """
    SCENE: SYNCHRONIZED ARCHITECTURE LATTICE
    The final resolution: Words in perfect sequential harmony with verified timecodes.
    """
    drift_x, drift_y = draw_perspective_grid(draw, width, height, t, drift_speed=1.0)
    cx, cy = width // 2, 530
    
    title = scene_meta.get("title", "SYNCHRONIZED TIMELINE")
    subtitle = scene_meta.get("subtitle", "100% Word Order Retention Across Hundreds of Layers")
    draw.text((cx, 170), title, fill=COLOR_FOREST_SAGE, font=fonts["header"], anchor="mm")
    draw.text((cx, 220), subtitle, fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
    
    # Ordered Sequence Timeline Rails
    tokens = ["Man", "bit", "the", "dog", "in", "the", "yard"]
    for i, tok in enumerate(tokens):
        x = 100 + i * 130
        y = cy + int(35 * math.sin(t * 3.0 + i * 0.8))
        
        # Connecting timeline wire
        if i < len(tokens) - 1:
            next_x = 100 + (i + 1) * 130
            next_y = cy + int(35 * math.sin(t * 3.0 + (i + 1) * 0.8))
            draw.line([(x, y), (next_x, next_y)], fill=COLOR_FOREST_SAGE, width=3)
            
        # Token Node Box
        draw.rounded_rectangle([x - 50, y - 35, x + 50, y + 35], radius=8,
                               fill=COLOR_BASALT_SLATE, outline=COLOR_SOLAR_AMBER, width=2)
        draw.text((x, y - 8), tok, fill=COLOR_CRISP_WHITE, font=fonts["small"], anchor="mm")
        draw.text((x, y + 16), f"t={i}", fill=COLOR_FOREST_SAGE, font=fonts["mono_small"], anchor="mm")
        
    # Verified Lock Status
    lock_y = cy + 180
    draw.rounded_rectangle([cx - 240, lock_y - 25, cx + 240, lock_y + 25],
                           radius=12, fill=(16, 24, 38), outline=COLOR_FOREST_SAGE, width=2)
    draw.text((cx, lock_y), "✓ SEQUENCE PRESERVED WITHOUT RECURSION", fill=COLOR_FOREST_SAGE, font=fonts["small"], anchor="mm")

def render_dynamic_frame(draw, width, height, t, progress, current_scene, fonts):
    """
    Dispatches frame rendering to the modular scene generator matching the scene storyboard.
    """
    mode = current_scene.get("mode", "order_chaos")
    
    if mode == "order_chaos":
        render_scene_order_chaos(draw, width, height, t, current_scene, fonts)
    elif mode == "conveyor_flow":
        render_scene_conveyor_flow(draw, width, height, t, current_scene, fonts)
    elif mode == "harmonic_oscillator":
        render_scene_harmonic_oscillator(draw, width, height, t, current_scene, fonts)
    elif mode in ["vector_stamp", "vector_fusion"]:
        render_scene_vector_fusion(draw, width, height, t, current_scene, fonts)
    elif mode in ["synchronized_lattice", "final_resolution"]:
        render_scene_synchronized_lattice(draw, width, height, t, current_scene, fonts)
    else:
        # Graceful fallback to harmonic oscillator
        render_scene_harmonic_oscillator(draw, width, height, t, current_scene, fonts)

def render_dynamic_video(storyboard, script_text, audio_path, output_mp4_path, episode_title="Kissa-e-Machine"):
    """
    Master video rendering engine:
    - Renders 1080x1920 vertical format.
    - Dynamically swaps 4-5 procedural scene visuals mapped to storyboard timestamps.
    - Centers dynamic burned-in subtitles strictly in the safe lower-middle zone (Y: 55-62%).
    - Highlights the currently spoken word in Solar Flare Amber (#F77F00).
    - Muxes cleanly with the voiceover MP3 using FFmpeg.
    """
    width = 1080
    height = 1920
    fps = 24
    
    duration = get_audio_duration(audio_path)
    if duration <= 5.0:
        duration = 50.0
    total_frames = int(duration * fps)
    print(f"[VideoEngine] Rendering {total_frames} frames ({duration:.2f}s) at {fps} FPS (1080x1920)...")
    
    captions = build_caption_timeline(script_text, duration)
    fonts = get_fonts()
    
    # Subtitle safe zone: Y 55% - 62% (for 1920 height, ~1060 to 1190)
    caption_box_y = int(height * 0.58)
    
    # Prepare scenes with normalized timings
    scenes = storyboard if storyboard and len(storyboard) > 0 else [
        {"mode": "order_chaos", "title": "THE BAG OF WORDS TRAP", "subtitle": "Math Has Zero Concept of Time or Order", "start_sec": 0.0, "end_sec": 12.0},
        {"mode": "conveyor_flow", "title": "THE PARALLEL CONVEYOR", "subtitle": "50 Tokens Loaded at the Same Exact Microsecond", "start_sec": 12.0, "end_sec": 24.0},
        {"mode": "harmonic_oscillator", "title": "HARMONIC FREQUENCY STAMP", "subtitle": "Sine (High Freq) + Cosine (Low Freq) Harmonic Clocks", "start_sec": 24.0, "end_sec": 38.0},
        {"mode": "vector_fusion", "title": "VECTOR ADDITION CHAMBER", "subtitle": "Token Vector + Frequency Vector = Ordered Meaning", "start_sec": 38.0, "end_sec": duration}
    ]
    
    temp_raw_avi = output_mp4_path + ".temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(temp_raw_avi, fourcc, fps, (width, height))
    
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        progress = frame_idx / total_frames
        
        img = Image.new("RGB", (width, height), COLOR_PRUSSIAN_INK)
        draw = ImageDraw.Draw(img)
        
        # 1. Determine active scene
        active_scene = scenes[-1]
        for s in scenes:
            if s.get("start_sec", 0.0) <= t < s.get("end_sec", duration):
                active_scene = s
                break
                
        # 2. Render dynamic procedural scene visual
        render_dynamic_frame(draw, width, height, t, progress, active_scene, fonts)
        
        # 3. Dynamic Burned-In Subtitles (Lower-Middle Safe Zone: Y 55-62%)
        active_chunk = None
        for c in captions:
            if c["start"] <= t <= c["end"]:
                active_chunk = c
                break
                
        if active_chunk:
            c_words = active_chunk["words"]
            space_w = fonts["caption"].getbbox(" ")[2]
            word_widths = [fonts["caption"].getbbox(w)[2] for w in c_words]
            total_w = sum(word_widths) + space_w * (len(c_words) - 1)
            start_x = (width - total_w) // 2
            
            # Rounded glass contrast backdrop pill
            pill_pad_x = 26
            pill_pad_y = 16
            draw.rounded_rectangle([start_x - pill_pad_x, caption_box_y - pill_pad_y,
                                    start_x + total_w + pill_pad_x, caption_box_y + 75],
                                   radius=16, fill=(10, 16, 26, 220), outline=(28, 40, 60), width=1)
                                   
            cur_x = start_x
            for i, w in enumerate(c_words):
                w_start = active_chunk["word_starts"][i]
                w_end = active_chunk["word_ends"][i]
                is_active_word = (w_start <= t <= w_end)
                
                # Active word in Solar Flare Amber (#F77F00), rest in Warm Cream / Crisp White
                word_fill = COLOR_SOLAR_AMBER if is_active_word else COLOR_WARM_CREAM
                
                # 3.5px solid dark outline (#161B22) for high-contrast legibility across devices
                draw.text((cur_x, caption_box_y), w, font=fonts["caption"], fill=word_fill,
                          stroke_width=4, stroke_fill=COLOR_DARK_SHADOW)
                cur_x += word_widths[i] + space_w
                
        # 4. Minimalist Header & Footer Telemetry
        draw.text((60, 60), f"KISSA-E-MACHINE • {episode_title.upper()}", fill=(140, 160, 185), font=fonts["mono_small"])
        
        sec_current = int(t)
        sec_total = int(duration)
        timestamp_str = f"{sec_current // 60}:{sec_current % 60:02d} / {sec_total // 60}:{sec_total % 60:02d}"
        draw.text((width - 240, height - 90), timestamp_str, fill=COLOR_WARM_CREAM, font=fonts["time"])
        draw.text((60, height - 90), "STANDALONE PRODUCTION ENGINE • PRAVA", fill=(130, 150, 175), font=fonts["time"])
        
        # Write Frame
        frame_np = np.array(img)
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
        
    out.release()
    print("[VideoEngine] Frames rendered. Muxing with FFmpeg...")
    
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", temp_raw_avi,
        "-i", audio_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4_path
    ]
    subprocess.run(mux_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    if os.path.exists(temp_raw_avi):
        os.remove(temp_raw_avi)
        
    print(f"[VideoEngine] Final video master ready: {output_mp4_path}")
    return output_mp4_path

# Backward compatibility alias
def render_motion_video(episode_num, topic, audio_path, output_mp4_path, script_text=""):
    return render_dynamic_video(None, script_text, audio_path, output_mp4_path, episode_title=f"EP_{episode_num}: {topic}")
