import os
import sys
import time
import argparse
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv_loader import load_env
import db
import telegram_service
import kissa_machine
import lead_outreach
import briefing

load_env()

BASE_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(BASE_DIR, "daemon.log")
SCHEDULE_STATE_FILE = os.path.join(BASE_DIR, "schedule_state.json")
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "output", "outreach_today.csv")

def get_ist_now():
    """
    Explicitly retrieves current time in Asia/Kolkata (IST / UTC+5:30).
    Resilient across Windows and Linux environments without external tzdata dependencies.
    """
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        try:
            import pytz
            return datetime.now(pytz.timezone("Asia/Kolkata"))
        except Exception:
            ist_tz = timezone(timedelta(hours=5, minutes=30), name="IST")
            return datetime.now(ist_tz)

def log(msg):
    now_ist = get_ist_now()
    timestamp = now_ist.strftime("%Y-%m-%d %H:%M:%S %Z")
    entry = f"[{timestamp}] {msg}"
    print(entry, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def load_schedule_state():
    if os.path.exists(SCHEDULE_STATE_FILE):
        try:
            with open(SCHEDULE_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "module_a": None,
        "module_b": None,
        "module_c": None
    }

def save_schedule_state(state):
    try:
        with open(SCHEDULE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"Error saving schedule state: {e}")

def send_telegram_briefing(text_summary, csv_path=None):
    """
    Bulletproof Telegram sender:
    1. ALWAYS delivers the text summary first (never blocked by file issues).
    2. Safely uploads the CSV document if available with proper MIME headers.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "9245204036:AAGHlHilMstsWDgJubVoLkpsL7iE0QPjz2w")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5393017337")
    
    # 1. ALWAYS send the text summary first (never blocked by file issues)
    url_msg = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Handle message length limit (4096 chars)
    chunks = []
    if len(text_summary) > 4000:
        parts = text_summary.split("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if len(parts) >= 3:
            chunks.append(parts[0] + "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + parts[1])
            chunks.append("━━━━━━━━━━━━━━━━━━━━━━━━━━" + "━━━━━━━━━━━━━━━━━━━━━━━━━━".join(parts[2:]))
        else:
            chunks = [text_summary[:4000], text_summary[4000:]]
    else:
        chunks = [text_summary]
        
    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            r = requests.post(url_msg, data=payload, timeout=20)
            print("Telegram text status:", r.status_code, r.text[:100])
            if r.status_code != 200:
                # Fallback without parse_mode
                payload.pop("parse_mode", None)
                r_retry = requests.post(url_msg, data=payload, timeout=20)
                print("Telegram text retry status:", r_retry.status_code)
        except Exception as e:
            print("Failed to send Telegram text summary:", e)

    # 2. Safely upload the CSV document if available
    if csv_path and os.path.exists(csv_path):
        try:
            url_doc = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            with open(csv_path, "rb") as f:
                files = {"document": ("outreach_today.csv", f, "text/csv")}
                data = {"chat_id": chat_id, "caption": "📊 Outreach Log (CSV • 1-tap open in Sheets / Excel)"}
                r_doc = requests.post(url_doc, data=data, files=files, timeout=30)
                print("Telegram doc status:", r_doc.status_code, r_doc.text[:100])
        except Exception as e:
            print("Failed to send CSV attachment:", e)

def run_module_a():
    log("▶️ TRIGGER [09:00 AM IST]: Module A (Kissa-e-Machine Content Generation)")
    try:
        kissa_machine.run_episode_pipeline()
        log("✅ Module A completed successfully.")
    except Exception as e:
        log(f"❌ Error in Module A: {e}")
        telegram_service.send_message(f"⚠️ Error running Kissa-e-Machine: {e}")

def run_module_b():
    log("▶️ TRIGGER [11:00 AM - 05:00 PM IST]: Module B (Targeted Lead Outreach & CSV Export)")
    try:
        lead_outreach.run_outreach_pipeline()
        log("✅ Module B completed successfully.")
    except Exception as e:
        log(f"❌ Error in Module B: {e}")
        telegram_service.send_message(f"⚠️ Error running Lead Outreach: {e}")

def run_module_c():
    log("▶️ TRIGGER [09:00 PM IST]: Module C (Evening Dossier & CSV Document Delivery)")
    try:
        now_ist = get_ist_now()
        today_str = now_ist.strftime("%Y-%m-%d")
        
        # 1. Fetch outreach log from DB and export CSV
        records = db.get_outreach_for_date(today_str)
        if not records:
            conn = db.get_connection()
            rows = conn.cursor().execute("""
                SELECT platform, handle, post_url, message_text, status, timestamp
                FROM outreach_log 
                ORDER BY id DESC LIMIT 20
            """).fetchall()
            conn.close()
            records = [dict(r) for r in reversed(rows)]
            
        csv_file = db.export_today_csv(OUTPUT_CSV_PATH, today_str, custom_records=records)
        
        # 2. Fetch top news
        news_analysis = briefing.fetch_top_news()
        
        # 3. Format Executive Dossier
        now_str = now_ist.strftime("%B %d, %Y • %I:%M %p %Z")
        in_chat_outreach = briefing.format_outreach_in_chat(records)
        
        dossier_msg = (
            f"📋 <b>EXECUTIVE DOSSIER • EVENING BRIEFING</b>\n"
            f"🗓️ <i>{now_str}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌐 <b>TOP 3 GLOBAL TECH & BUSINESS INTELLIGENCE</b>\n\n"
            f"{news_analysis}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>TODAY'S OUTREACH LOG ({len(records)} PROSPECTS)</b>\n"
            f"<i>(Zero-Tap In-Chat Mirroring + Clickable Links)</i>\n\n"
            f"{in_chat_outreach}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📎 <i>Attached: <code>outreach_today.csv</code> (Mobile-optimized UTF-8-SIG for Excel/Sheets).</i>"
        )
        
        # 4. Deliver via bulletproof sender
        send_telegram_briefing(dossier_msg, csv_file)
        log("✅ Module C completed successfully.")
    except Exception as e:
        log(f"❌ Error in Module C: {e}")
        telegram_service.send_message(f"⚠️ Error running Evening Briefing: {e}")

def daemon_loop():
    log("🚀 Prava Autonomous Daemon running with fixed IST triggers...")
    log("⏰ IST Triggers: 9:00 AM (Content Engine) | 11:00 AM - 5:00 PM (Lead Outreach) | 9:00 PM (Evening Dossier)")
    db.init_db()
    
    state = load_schedule_state()
    log(f"Active schedule state: {state}")
    
    while True:
        now = get_ist_now()
        today_str = now.strftime("%Y-%m-%d")
        current_hour = now.hour
        
        # 1. Daily 9:00 AM IST: Episode Content Engine
        if current_hour >= 9 and state.get("module_a") != today_str:
            run_module_a()
            state["module_a"] = today_str
            save_schedule_state(state)
            
        # 2. Daily 11:00 AM - 5:00 PM IST: Targeted Lead Outreach
        if 11 <= current_hour < 17 and state.get("module_b") != today_str:
            run_module_b()
            state["module_b"] = today_str
            save_schedule_state(state)
            
        # 3. Daily 9:00 PM IST: Evening Briefing Dossier + CSV Document
        if current_hour >= 21 and state.get("module_c") != today_str:
            run_module_c()
            state["module_c"] = today_str
            save_schedule_state(state)
            
        time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prava Autonomous Agent Daemon")
    parser.add_argument("--run-all", action="store_true", help="Run full dry run of all modules immediately")
    parser.add_argument("--episode-now", action="store_true", help="Trigger Episode generation immediately")
    parser.add_argument("--outreach-now", action="store_true", help="Trigger Lead Outreach immediately")
    parser.add_argument("--briefing-now", action="store_true", help="Trigger Evening Briefing immediately")
    parser.add_argument("--daemon", action="store_true", help="Run persistent scheduling loop")
    
    args = parser.parse_args()
    
    if args.run_all:
        log("Executing complete immediate pipeline run for all modules...")
        run_module_a()
        run_module_b()
        run_module_c()
    elif args.episode_now:
        run_module_a()
    elif args.outreach_now:
        run_module_b()
    elif args.briefing_now:
        run_module_c()
    elif args.daemon:
        daemon_loop()
    else:
        daemon_loop()
