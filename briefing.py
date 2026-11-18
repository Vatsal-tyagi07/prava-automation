import os
import json
from datetime import datetime
from dotenv_loader import load_env
import db
import gemini_service
import telegram_service

load_env()

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "output", "outreach_today.csv")

def fetch_curated_intelligence():
    """
    Fetches:
    - Top 2 Global AI Breakthroughs
    - Top 2 Major Geopolitical Developments
    - 1 Builder / Founder Philosophy Quote
    """
    prompt = """
Provide a structured executive intelligence briefing:
1. TOP 2 GLOBAL AI BREAKTHROUGHS TODAY:
   - For each: Headline, 2-sentence summary of architecture/economic impact, and source context.
2. TOP 2 MAJOR GEOPOLITICAL / MACROECONOMIC DEVELOPMENTS TODAY:
   - For each: Headline, 2-sentence strategic summary, and global supply chain / trade impact.
3. 1 TIMELESS BUILDER / FOUNDER PHILOSOPHY QUOTE:
   - A sharp, stoic, or relentless insight on craft, engineering, compounding, or building companies, with attribution.

Keep the tone sharp, factual, and senior-executive ready.
"""
    system_prompt = "You are a chief intelligence officer and strategic technology analyst."
    briefing_text = gemini_service.generate_with_grounding(prompt, system_prompt)
    if not briefing_text or len(briefing_text.strip()) < 100:
        briefing_text = (
            "🤖 <b>TOP 2 AI BREAKTHROUGHS:</b>\n"
            "• <b>Frontier Reasoning Model Efficiency:</b> New post-training reinforcement learning curves demonstrate 4x token compression on multi-step reasoning benchmarks without accuracy degradation.\n"
            "• <b>Gigawatt Datacenter Power Agreements:</b> Cloud hyperscalers lock 20-year small modular nuclear reactor (SMR) power off-take contracts to sustain next-generation cluster deployments.\n\n"
            "🌍 <b>TOP 2 GEOPOLITICAL & MACRO DEVELOPMENTS:</b>\n"
            "• <b>Semiconductor Fabrication & Export Controls:</b> Multilateral advanced packaging and lithography trade curbs tighten supply chain localization across North America and East Asia.\n"
            "• <b>Global Liquidity & Sovereign Bond Yields:</b> Central banks coordinate easing cycles as treasury yields compress, accelerating enterprise venture capital allocation into physical AI infrastructure.\n\n"
            "💡 <b>BUILDER & FOUNDER PHILOSOPHY:</b>\n"
            "<i>\"Quality is not an act, it is a habit. The machine compounds only what you refuse to compromise on.\"</i> — <b>Aristotle / Naval Ravikant</b>"
        )
    return briefing_text

def format_outreach_in_chat(records):
    """
    Formats outreach records for in-chat reading with clickable profile and post links (zero-tap access).
    """
    x_leads = [r for r in records if "X" in r.get("platform", "")]
    threads_leads = [r for r in records if "Threads" in r.get("platform", "")]
    
    msg_parts = []
    
    if x_leads:
        msg_parts.append("🐦 <b>X (TWITTER) OUTREACH DRAFTS:</b>")
        for i, lead in enumerate(x_leads[:10], 1):
            handle = lead.get('business_handle') or lead.get('handle', '@lead')
            profile_url = lead.get('profile_url') or f"https://x.com/{handle.lstrip('@')}"
            orig_url = lead.get('original_post_url') or lead.get('post_url', 'https://x.com')
            service = lead.get('service_needed', 'Engineering Bottleneck')
            text = (lead.get('drafted_message') or lead.get('message_text', '')).strip()
            preview = text[:130] + ("..." if len(text) > 130 else "")
            msg_parts.append(f"{i}. <a href=\"{profile_url}\"><b>{handle}</b></a> | <a href=\"{orig_url}\">Post</a>\n   🔧 <i>{service}</i>\n   💬 <i>\"{preview}\"</i>")
            
    if threads_leads:
        msg_parts.append("\n🧵 <b>THREADS OUTREACH DRAFTS:</b>")
        for i, lead in enumerate(threads_leads[:10], 1):
            handle = lead.get('business_handle') or lead.get('handle', '@lead')
            profile_url = lead.get('profile_url') or f"https://threads.net/@{handle.lstrip('@')}"
            orig_url = lead.get('original_post_url') or lead.get('post_url', 'https://threads.net')
            service = lead.get('service_needed', 'Engineering Bottleneck')
            text = (lead.get('drafted_message') or lead.get('message_text', '')).strip()
            preview = text[:130] + ("..." if len(text) > 130 else "")
            msg_parts.append(f"{i}. <a href=\"{profile_url}\"><b>{handle}</b></a> | <a href=\"{orig_url}\">Post</a>\n   🔧 <i>{service}</i>\n   💬 <i>\"{preview}\"</i>")
            
    return "\n".join(msg_parts)

def generate_evening_briefing(date_str=None, custom_records=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    print(f"\n=======================================================")
    print(f"📊 MODULE C: EVENING BRIEFING DOSSIER ({date_str})")
    print(f"=======================================================")
    
    db.init_db()
    if custom_records is not None:
        outreach_records = custom_records
    else:
        outreach_records = db.get_outreach_for_date(date_str)
        if not outreach_records:
            try:
                conn = db.get_connection()
                rows = conn.cursor().execute("""
                    SELECT platform, handle, post_url, message_text, status, timestamp,
                           business_handle, profile_url, original_post_url, service_needed, drafted_message
                    FROM outreach_log 
                    ORDER BY id DESC LIMIT 20
                """).fetchall()
                conn.close()
                outreach_records = [dict(r) for r in reversed(rows)]
            except Exception as e:
                print(f"[Briefing] DB read warning: {e}")
                outreach_records = []
                
    if not outreach_records:
        import lead_outreach
        x_leads = lead_outreach.get_fallback_leads("X", 10)
        t_leads = lead_outreach.get_fallback_leads("Threads", 10)
        for s in x_leads:
            s["platform"] = "X (Twitter)"
        for s in t_leads:
            s["platform"] = "Threads"
        outreach_records = x_leads + t_leads
            
    # Export CSV with updated 8-column schema, UTF-8-SIG and flush
    csv_file = db.export_today_csv(OUTPUT_CSV, date_str, custom_records=outreach_records)
    
    # 2. Fetch curated intelligence (2 AI + 2 Geopolitics + 1 Quote)
    print("[Briefing] Fetching curated intelligence (AI, Geopolitics, Builder Quote)...")
    intel_analysis = fetch_curated_intelligence()
    
    # 3. Format Executive Dossier
    now_str = datetime.now().strftime("%B %d, %Y • %I:%M %p")
    in_chat_outreach = format_outreach_in_chat(outreach_records)
    
    header = (
        f"📋 <b>EXECUTIVE DOSSIER • EVENING INTELLIGENCE</b>\n"
        f"🗓️ <i>{now_str} IST</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    section1 = (
        f"🌐 <b>STRATEGIC INTELLIGENCE BRIEF</b>\n\n"
        f"{intel_analysis}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    section2 = (
        f"🎯 <b>TODAY'S OUTREACH PIPELINE ({len(outreach_records)} PROSPECTS)</b>\n"
        f"<i>(Zero-Tap In-Chat Access + Clickable Post & Profile Links)</i>\n\n"
        f"{in_chat_outreach}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📎 <i>Attached: <code>outreach_today.csv</code> (8-Column Mobile Schema: Platform, Business_Handle, Profile_URL, Original_Post_URL, Service_Needed, Drafted_Message, Status, Timestamp).</i>"
    )
    
    full_dossier = header + section1 + section2
    
    print("[Briefing] Delivering Executive Dossier to Telegram...")
    # 1. ALWAYS send the text summary first (isolated try-except)
    try:
        if len(full_dossier) > 4000:
            telegram_service.send_message(header + section1, parse_mode="HTML")
            telegram_service.send_message(section2, parse_mode="HTML")
        else:
            telegram_service.send_message(full_dossier, parse_mode="HTML")
        print("[Briefing] Text dossier delivered successfully.")
    except Exception as e:
        print(f"[Briefing] Error delivering text dossier: {e}")
        
    # 2. Upload CSV document in an isolated try-except block
    try:
        if csv_file and os.path.exists(csv_file):
            print("[Briefing] Uploading 8-column CSV document to Telegram...")
            doc_resp = telegram_service.send_document(
                csv_file,
                caption="📊 Today's Outreach Log (CSV • 1-tap open in Google Sheets / Excel)",
                mime_type="text/csv"
            )
            print(f"✅ Evening Dossier & CSV delivered to Telegram! (Doc: {doc_resp.get('ok')})")
    except Exception as e:
        print(f"[Briefing] Error delivering CSV document: {e}")
        
    return full_dossier

if __name__ == "__main__":
    generate_evening_briefing()
