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
        is_break = any(w.endswith(p) for p in [".", "?", "!", "—", ","])
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

def render_scene_1_token_overload(draw, width, height, t, progress, fonts):
    """
    SCENE 1 (0:00 - 0:10): The Token River & Input Intake
    Isometric server rack tower with thousands of text tokens streaming down
    into an intake funnel. Camera drifts dynamically with slight continuous zoom.
    """
    drift_x = int(math.sin(t * 1.5) * 30)
    drift_y = int(math.cos(t * 1.2) * 20)
    
    # Background grid with perspective drift
    draw.rectangle([0, 0, width, height], fill=COLOR_PRUSSIAN_INK)
    for gx in range(-100, width + 100, 75):
        draw.line([(gx + drift_x, 0), (gx + drift_x + 350, height)], fill=(16, 26, 42), width=1)
        draw.line([(gx + drift_x + 350, 0), (gx + drift_x, height)], fill=(16, 26, 42), width=1)
        
    # Isometric Server Intake Chassis
    chassis_cx = width // 2 + drift_x // 2
    chassis_cy = 520 + drift_y // 2
    
    # Tower base shadow
    draw.ellipse([chassis_cx - 360, chassis_cy + 180, chassis_cx + 360, chassis_cy + 320], fill=(8, 14, 24))
    
    # 3D Intake Funnel (Top)
    funnel_rx, funnel_ry = 320, 140
    draw.ellipse([chassis_cx - funnel_rx, chassis_cy - funnel_ry,
                  chassis_cx + funnel_rx, chassis_cy + funnel_ry], fill=(20, 34, 56), outline=COLOR_CYAN_GLOW, width=4)
    draw.ellipse([chassis_cx - funnel_rx + 40, chassis_cy - funnel_ry + 20,
                  chassis_cx + funnel_rx - 40, chassis_cy + funnel_ry - 20], fill=(12, 18, 30), outline=COLOR_SOLAR_AMBER, width=2)
                  
    # Streaming Input Tokens Raining Down (High speed)
    tokens = ["def", "query", "user_input", "context", "history", "payload", "tokens", "batch", "tensor", "1000_lines"]
    for i in range(16):
        tok_speed = 320 + (i * 35) % 150
        tok_y = int((t * tok_speed + i * 90) % (chassis_cy + 100))
        tok_x = chassis_cx + int(240 * math.sin(i * 1.7 + t * 2.0) * (1.0 - (tok_y / (chassis_cy + 120)) * 0.7))
        tok_text = tokens[i % len(tokens)]
        
        # Token pill box
        pill_w = fonts["small"].getbbox(tok_text)[2] + 16
        draw.rounded_rectangle([tok_x - pill_w // 2, tok_y - 12, tok_x + pill_w // 2, tok_y + 12],
                               radius=6, fill=COLOR_BASALT_SLATE, outline=COLOR_CYAN_GLOW, width=1)
        draw.text((tok_x, tok_y), tok_text, fill=COLOR_WARM_CREAM, font=fonts["mono_small"], anchor="mm")
        
    # Lower Collector Reservoir
    draw.rectangle([chassis_cx - 180, chassis_cy, chassis_cx + 180, chassis_cy + 220],
                   fill=(16, 26, 44), outline=COLOR_FOREST_SAGE, width=3)
    draw.ellipse([chassis_cx - 180, chassis_cy + 220 - 45, chassis_cx + 180, chassis_cy + 220 + 45],
                 fill=(14, 22, 38), outline=COLOR_FOREST_SAGE, width=3)
                 
    # HUD Alert Overlay
    draw.rectangle([chassis_cx - 250, 180, chassis_cx + 250, 230], fill=(14, 20, 32, 220), outline=COLOR_CORAL, width=2)
    pulse_dot = "●" if (int(t * 3) % 2 == 0) else "○"
    draw.text((chassis_cx, 205), f"{pulse_dot} PROMPT INGESTION: 1,000+ TOKENS STREAMING", fill=COLOR_CORAL, font=fonts["small"], anchor="mm")

def render_scene_2_encoder_chamber(draw, width, height, t, progress, fonts):
    """
    SCENE 2 (0:10 - 0:22): The Encoder (The Master Sous-Chef)
    Isometric multi-layer digestion chamber compressing raw sequence into a rich
    contextual stock pot. Continuous 45-degree angle drift.
    """
    draw.rectangle([0, 0, width, height], fill=COLOR_PRUSSIAN_INK)
    
    drift = int(math.sin(t * 2.0) * 25)
    center_x = width // 2 + drift
    center_y = 500
    
    draw.text((width // 2, 170), "THE ENCODER: MASTER SOUS-CHEF", fill=COLOR_CYAN_GLOW, font=fonts["header"], anchor="mm")
    draw.text((width // 2, 215), "Parallel Processing: Digesting Entire Sequence All At Once",
              fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
              
    # 6 Stacked Isometric Compression Plates (N=6 Layers)
    for layer in range(6):
        ly = center_y + 160 - layer * 52
        rx, ry = 310 - layer * 15, 110 - layer * 6
        
        # Plate drop shadow
        draw.ellipse([center_x - rx, ly + 14 - ry, center_x + rx, ly + 14 + ry], fill=(8, 14, 22))
        
        # Isometric plate
        plate_color = (22, 36, 58) if layer < 5 else COLOR_FOREST_SAGE
        draw.ellipse([center_x - rx, ly - ry, center_x + rx, ly + ry],
                     fill=plate_color, outline=COLOR_CYAN_GLOW, width=2)
                     
        # Layer label
        draw.text((center_x - rx + 35, ly), f"LAYER {layer+1}", fill=COLOR_WARM_CREAM, font=fonts["mono_small"], anchor="lm")
        
        # Energy scanning beams between plates
        scan_offset = math.sin(t * 5.0 + layer) * (rx - 40)
        draw.line([(center_x + scan_offset, ly - ry), (center_x + scan_offset, ly + ry)],
                  fill=COLOR_SOLAR_AMBER, width=3)
                  
    # Central Condensed Stock Pot (Concentrated Context Sphere)
    core_y = center_y - 180
    pulse_r = int(65 + 10 * math.sin(t * 8.0))
    draw.ellipse([center_x - pulse_r - 20, core_y - pulse_r - 20,
                  center_x + pulse_r + 20, core_y + pulse_r + 20], outline=COLOR_SOLAR_AMBER, width=2)
    draw.ellipse([center_x - pulse_r, core_y - pulse_r, center_x + pulse_r, core_y + pulse_r],
                 fill=COLOR_CORAL, outline=COLOR_CRISP_WHITE, width=4)
    draw.text((center_x, core_y), "CONTEXT\nSTOCK", fill=COLOR_WARM_CREAM, font=fonts["small"], anchor="mm")

def render_scene_3_decoder_station(draw, width, height, t, progress, fonts):
    """
    SCENE 3 (0:22 - 0:35): The Decoder (The Master Plating Chef)
    Perspective snaps to the right station: An automated conveyor where new tokens
    are plated one by one in autoregressive sequence.
    """
    draw.rectangle([0, 0, width, height], fill=COLOR_PRUSSIAN_INK)
    
    draw.text((width // 2, 170), "THE DECODER: PLATING CHEF", fill=COLOR_SOLAR_AMBER, font=fonts["header"], anchor="mm")
    draw.text((width // 2, 215), "Autoregressive Generation: Assembling Word By Word",
              fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
              
    cx, cy = width // 2, 540
    
    # 3D Conveyor Track
    draw.polygon([(80, cy + 120), (width - 80, cy - 60), (width - 80, cy - 10), (80, cy + 170)],
                 fill=(18, 26, 42), outline=COLOR_BASALT_SLATE)
    draw.line([(80, cy + 120), (width - 80, cy - 60)], fill=COLOR_CYAN_GLOW, width=3)
    draw.line([(80, cy + 170), (width - 80, cy - 10)], fill=COLOR_CYAN_GLOW, width=3)
    
    # Plated Output Word Pedestals moving along the line
    output_tokens = ["The", "AI", "synthesizes", "coherent", "logic", "instantly"]
    for i, tok in enumerate(output_tokens):
        pos = (t * 0.35 + i * 0.16) % 1.0
        px = int(120 + pos * (width - 240))
        py = int((cy + 140) - pos * 180)
        
        # Pedestal disc
        draw.ellipse([px - 45, py - 18, px + 45, py + 18], fill=COLOR_FOREST_SAGE, outline=COLOR_WARM_CREAM, width=2)
        draw.text((px, py - 4), tok, fill=COLOR_CRISP_WHITE, font=fonts["small"], anchor="mm")
        
    # High-Precision Robotic Plating Arm
    arm_x = cx + int(60 * math.sin(t * 3.0))
    arm_y = cy - 140
    draw.line([(arm_x - 100, arm_y - 120), (arm_x, arm_y)], fill=COLOR_BASALT_SLATE, width=8)
    draw.line([(arm_x, arm_y), (arm_x, arm_y + 110)], fill=COLOR_SOLAR_AMBER, width=6)
    draw.ellipse([arm_x - 14, arm_y + 110 - 14, arm_x + 14, arm_y + 110 + 14], fill=COLOR_CORAL, outline=COLOR_CRISP_WHITE, width=2)
    
    # Active Plating Spark
    if int(t * 4) % 2 == 0:
        draw.line([(arm_x, arm_y + 110), (arm_x + 25, arm_y + 140)], fill=COLOR_WARM_CREAM, width=3)
        draw.line([(arm_x, arm_y + 110), (arm_x - 25, arm_y + 140)], fill=COLOR_WARM_CREAM, width=3)

def render_scene_4_cross_attention_fusion(draw, width, height, t, progress, fonts):
    """
    SCENE 4 (0:35 - 0:46): The Double Handshake (Cross-Attention Bridge)
    Wide view showing the Encoder's Stock Pot on the left and Decoder Plating Station
    on the right, connected by a high-voltage laser rail.
    """
    draw.rectangle([0, 0, width, height], fill=COLOR_PRUSSIAN_INK)
    
    draw.text((width // 2, 170), "CROSS-ATTENTION: THE DOUBLE HANDSHAKE", fill=COLOR_CORAL, font=fonts["header"], anchor="mm")
    draw.text((width // 2, 215), "Before Placing Each Word, The Decoder Tastes The Stock Pot",
              fill=COLOR_WARM_CREAM, font=fonts["subhead"], anchor="mm")
              
    left_x, left_y = 230, 520
    right_x, right_y = width - 230, 520
    
    # Left: Encoder Pot
    draw.ellipse([left_x - 110, left_y - 65, left_x + 110, left_y + 65], fill=(20, 36, 56), outline=COLOR_CYAN_GLOW, width=3)
    draw.text((left_x, left_y), "ENCODER\n(ALL CONTEXT)", fill=COLOR_WARM_CREAM, font=fonts["small"], anchor="mm")
    
    # Right: Decoder Output
    draw.ellipse([right_x - 110, right_y - 65, right_x + 110, right_y + 65], fill=(36, 26, 48), outline=COLOR_SOLAR_AMBER, width=3)
    draw.text((right_x, right_y), "DECODER\n(NEW WORD)", fill=COLOR_WARM_CREAM, font=fonts["small"], anchor="mm")
    
    # Connecting High-Voltage Cross-Attention Laser Rails
    rail_pulse = 0.5 + 0.5 * math.sin(t * 12.0)
    rail_col = COLOR_SOLAR_AMBER if rail_pulse > 0.4 else COLOR_CORAL
    draw.line([(left_x + 110, left_y), (right_x - 110, right_y)], fill=rail_col, width=6)
    
    # Traveling Tasting Particle Spoons
    for pi in range(3):
        particle_pos = (t * 2.0 + pi * 0.33) % 1.0
        px = int((left_x + 110) + particle_pos * (right_x - left_x - 220))
        py = int(left_y + 35 * math.sin(particle_pos * math.pi * 2))
        draw.ellipse([px - 10, py - 10, px + 10, py + 10], fill=COLOR_CRISP_WHITE, outline=COLOR_SOLAR_AMBER, width=2)
        
    # Central Cross-Attention Lock HUD
    mid_x, mid_y = width // 2, 640
    draw.rounded_rectangle([mid_x - 200, mid_y - 30, mid_x + 200, mid_y + 30],
                           radius=12, fill=(16, 24, 38), outline=COLOR_FOREST_SAGE, width=2)
    draw.text((mid_x, mid_y), "CONTEXT MATCH: 99.8% VERIFIED", fill=COLOR_FOREST_SAGE, font=fonts["small"], anchor="mm")

def render_scene_5_crystallized_transformer(draw, width, height, t, progress, fonts):
    """
    SCENE 5 (0:46 - End): The Unified Transformer Engine
    Dynamic slow cinematic pull-back showing the complete full-stack architecture
    resonating as a unified thinking machine.
    """
    draw.rectangle([0, 0, width, height], fill=COLOR_PRUSSIAN_INK)
    
    draw.text((width // 2, 170), "THE TRANSFORMER ARCHITECTURE", fill=COLOR_WARM_CREAM, font=fonts["header"], anchor="mm")
    draw.text((width // 2, 215), "The Kitchen Engine Behind All Modern Generative AI",
              fill=COLOR_SOLAR_AMBER, font=fonts["subhead"], anchor="mm")
              
    cx, cy = width // 2, 540
    
    # Outer Rotating Holographic Rings
    for ring_idx, (rx, ry, col) in enumerate([(380, 240, COLOR_FOREST_SAGE),
                                              (300, 180, COLOR_CYAN_GLOW),
                                              (220, 130, COLOR_SOLAR_AMBER)]):
        angle = t * 0.6 * (1 if ring_idx % 2 == 0 else -1)
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=2)
        
    # Glowing Fusion Core
    pulse_size = int(60 + 12 * math.sin(t * 6.0))
    draw.ellipse([cx - pulse_size, cy - pulse_size, cx + pulse_size, cy + pulse_size],
                 fill=COLOR_WARM_CREAM, outline=COLOR_CRISP_WHITE, width=4)
    draw.text((cx, cy), "TRANSFORMER\nFUSION", fill=COLOR_BASALT_SLATE, font=fonts["mono_small"], anchor="mm")

def render_motion_video(episode_num, topic, audio_path, output_mp4_path, script_text=""):
    duration = get_audio_duration(audio_path)
    fps = 24
    total_frames = int(duration * fps)
    width, height = 1080, 1920
    
    captions = build_caption_timeline(script_text, duration)
    temp_raw_avi = output_mp4_path.replace(".mp4", "_raw.avi")
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(temp_raw_avi, fourcc, fps, (width, height))
    
    # Fonts
    font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    font_target = font_bold_path if os.path.exists(font_bold_path) else next((p for p in linux_fonts if os.path.exists(p)), None)
    
    try:
        fonts = {
            "header": ImageFont.truetype(font_target, 40) if font_target else ImageFont.load_default(),
            "subhead": ImageFont.truetype(font_target, 26) if font_target else ImageFont.load_default(),
            "small": ImageFont.truetype(font_target, 22) if font_target else ImageFont.load_default(),
            "mono_small": ImageFont.truetype(font_target, 18) if font_target else ImageFont.load_default(),
            # Subtitle font: Montserrat Black / Arial Bold (Size 58)
            "caption": ImageFont.truetype(font_target, 58) if font_target else ImageFont.load_default(),
            "badge": ImageFont.truetype(font_target, 26) if font_target else ImageFont.load_default(),
            "time": ImageFont.truetype(font_target, 24) if font_target else ImageFont.load_default()
        }
    except:
        default_f = ImageFont.load_default()
        fonts = {k: default_f for k in ["header", "subhead", "small", "mono_small", "caption", "badge", "time"]}
        
    # 5 Sequential Scene Shifts (every ~10-12s, dynamic multi-scene compositing)
    s1_end = min(10.0, duration * 0.20)
    s2_end = min(22.0, duration * 0.44)
    s3_end = min(35.0, duration * 0.70)
    s4_end = min(46.0, duration * 0.90)
    
    print(f"[VideoEngine] Rendering Dynamic 5-Scene Video for EP_{episode_num} ({total_frames} frames, {duration:.1f}s)...")
    
    for f in range(total_frames):
        t = f / fps
        progress = t / duration
        
        img = Image.new("RGB", (width, height), COLOR_PRUSSIAN_INK)
        draw = ImageDraw.Draw(img)
        
        # 1. Topic-Driven Dynamic Scene Rendering
        if t < s1_end:
            render_scene_1_token_overload(draw, width, height, t, progress, fonts)
        elif t < s2_end:
            render_scene_2_encoder_chamber(draw, width, height, t, progress, fonts)
        elif t < s3_end:
            render_scene_3_decoder_station(draw, width, height, t, progress, fonts)
        elif t < s4_end:
            render_scene_4_cross_attention_fusion(draw, width, height, t, progress, fonts)
        else:
            render_scene_5_crystallized_transformer(draw, width, height, t, progress, fonts)
            
        # 2. Header Section (Episode Badge)
        draw.rectangle([50, 55, 480, 110], fill=COLOR_BASALT_SLATE, outline=COLOR_SOLAR_AMBER, width=2)
        draw.text((70, 70), f"KISSA-E-MACHINE • EP {episode_num}", fill=COLOR_WARM_CREAM, font=fonts["badge"])
        
        # 3. Dynamic Word-Level Subtitles in Safe Zone (Y: 52% - 60% -> Y = 1040 - 1150)
        caption_box_y = 1050
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
            
            # Contrast rounded glass pill backdrop
            pill_pad_x = 24
            pill_pad_y = 14
            draw.rounded_rectangle([start_x - pill_pad_x, caption_box_y - pill_pad_y,
                                    start_x + total_w + pill_pad_x, caption_box_y + 75],
                                   radius=16, fill=(10, 16, 26, 220), outline=(28, 40, 60), width=1)
                                   
            cur_x = start_x
            for i, w in enumerate(c_words):
                w_start = active_chunk["word_starts"][i]
                w_end = active_chunk["word_ends"][i]
                is_active_word = (w_start <= t <= w_end)
                
                # Active word highlighted in Solar Flare Amber (#F77F00), rest Warm Cream / Crisp White
                word_fill = COLOR_SOLAR_AMBER if is_active_word else COLOR_WARM_CREAM
                
                # 3.5px solid dark outline (#161B22) for razor-sharp readability across screens
                draw.text((cur_x, caption_box_y), w, font=fonts["caption"], fill=word_fill,
                          stroke_width=4, stroke_fill=COLOR_DARK_SHADOW)
                cur_x += word_widths[i] + space_w
                
        # 4. Clean Minimal Footer
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
