import os
import sys
import traceback
from flask import Flask, jsonify, request
from dotenv_loader import load_env

load_env()

app = Flask(__name__)

# Route: Health check for Google Cloud Run
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "prava-pipeline-service",
        "project": "prava-automation-514816",
        "region": "asia-south1",
        "version": "2.5.0"
    }), 200

# Route: Cloud Scheduler trigger for Kissa-e-Machine Content (9:00 AM IST)
@app.route("/trigger/content", methods=["POST", "GET"])
def trigger_content():
    try:
        import kissa_machine
        result = kissa_machine.run_episode_pipeline(dry_run=False)
        return jsonify({
            "status": "success",
            "module": "kissa_machine",
            "result": str(result)
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500

# Route: Cloud Scheduler trigger for Lead Outreach (11:00 AM - 5:00 PM IST)
@app.route("/trigger/outreach", methods=["POST", "GET"])
def trigger_outreach():
    try:
        import lead_outreach
        total = lead_outreach.run_outreach_pipeline(dry_run=False)
        return jsonify({
            "status": "success",
            "module": "lead_outreach",
            "total_logged": total
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500

# Route: Cloud Scheduler trigger for Evening Intelligence Briefing (9:00 PM IST)
@app.route("/trigger/briefing", methods=["POST", "GET"])
def trigger_briefing():
    try:
        import briefing
        dossier = briefing.generate_evening_briefing()
        return jsonify({
            "status": "success",
            "module": "briefing",
            "dossier_length": len(dossier)
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
