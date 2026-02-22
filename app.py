from flask import Flask, jsonify, render_template, request

from config import config
from services.orchestrator import Orchestrator
from services.sms_gateway import SMSGateway


app = Flask(__name__)
orchestrator = Orchestrator()
sms = SMSGateway()

# phone_number -> session_id for simple SMS state
sms_sessions = {}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/result/<session_id>")
def result_page(session_id: str):
    try:
        data = orchestrator.result(session_id)
    except KeyError:
        return jsonify({"error": "session not found"}), 404
    return render_template("result.html", data=data)


@app.post("/api/session/start")
def start_session():
    payload = request.get_json(force=True)
    mode = payload.get("mode", "")
    submode = payload.get("submode", "")
    try:
        session = orchestrator.start_session(mode=mode, submode=submode)
        return jsonify(
            {
                "session_id": session.session_id,
                "mode": session.mode,
                "submode": session.submode,
                "selected_boss": session.selected_boss,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/session/message")
def add_message():
    payload = request.get_json(force=True)
    session_id = payload.get("session_id", "")
    message = (payload.get("message", "") or "").strip()
    resume_text = payload.get("resume_text", "")
    company_context = payload.get("company_context", "")
    projects_text = payload.get("projects_text", "")
    if not any([message, resume_text, company_context, projects_text]):
        return jsonify({"error": "Provide at least one of: message, resume_text, company_context, projects_text"}), 400

    try:
        session = orchestrator.add_message(
            session_id=session_id,
            message=message,
            resume_text=resume_text,
            company_context=company_context,
            projects_context=projects_text,
        )
        return jsonify(
            {
                "ok": True,
                "messages_count": len(session.messages),
                "company_context_set": bool(session.company_context),
                "projects_context_set": bool(session.projects_context),
                "resume_set": bool(session.resume_text),
            }
        )
    except KeyError:
        return jsonify({"error": "session not found"}), 404


@app.post("/api/session/<session_id>/finalize")
def finalize(session_id: str):
    try:
        result = orchestrator.finalize(session_id)
        return jsonify(result)
    except KeyError:
        return jsonify({"error": "session not found"}), 404
    except Exception as exc:
        return jsonify({"error": f"finalize failed: {exc}"}), 500


@app.post("/api/session/<session_id>/select-boss")
def select_boss(session_id: str):
    payload = request.get_json(force=True)
    boss_id = payload.get("boss_id", "")
    try:
        session = orchestrator.select_boss(session_id, boss_id)
        return jsonify({"ok": True, "session_id": session.session_id, "selected_boss": session.selected_boss})
    except KeyError:
        return jsonify({"error": "session not found"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/session/<session_id>/result")
def result(session_id: str):
    try:
        return jsonify(orchestrator.result(session_id))
    except KeyError:
        return jsonify({"error": "session not found"}), 404


@app.post("/webhook/sms")
def webhook_sms():
    from_number = request.form.get("From", "")
    body = (request.form.get("Body", "") or "").strip()

    if not from_number:
        return "", 400

    response_message = ""
    existing_session_id = sms_sessions.get(from_number)

    if body.upper() == "START":
        response_message = "Welcome to Chartroom. Reply 1 for Board, 2 for 1-on-1 Interview, 3 for Investor Pitch Prep."
    elif body == "1":
        session = orchestrator.start_session(mode="board_investors", phone_number=from_number)
        sms_sessions[from_number] = session.session_id
        response_message = "Board mode started. Share your startup idea, problem, users, traction, and resume highlights. Send DONE when finished."
    elif body == "2":
        session = orchestrator.start_session(mode="interview_1on1", phone_number=from_number)
        sms_sessions[from_number] = session.session_id
        response_message = "1-on-1 mode started. Describe your program. Optional: mention past work experience leverage. Send DONE when finished."
    elif body == "3":
        session = orchestrator.start_session(mode="investor_pitch_prep", phone_number=from_number)
        sms_sessions[from_number] = session.session_id
        response_message = "Investor prep mode started. Share company context, traction, ask, and likely investor concerns. Send DONE when finished."
    elif body.upper() == "DONE" and existing_session_id:
        result_payload = orchestrator.finalize(existing_session_id)
        files = result_payload.get("files", {})
        response_message = (
            "Session finalized. "
            f"Talking points file: {files.get('talking_points', 'n/a')} "
            f"Result page: {config.base_url}/result/{existing_session_id}"
        )
    elif body.upper() in {"BOSS 1", "BOSS 2", "BOSS 3"} and existing_session_id:
        boss_id = f"boss_{body.strip()[-1]}"
        orchestrator.select_boss(existing_session_id, boss_id)
        response_message = f"Selected {boss_id}. Keep sharing details, then send DONE."
    elif existing_session_id:
        orchestrator.add_message(existing_session_id, body)
        response_message = "Saved. Keep going, or send DONE to finalize."
    else:
        response_message = "Text START to begin."

    # Return TwiML manually to avoid dependency on twilio twiml helper.
    xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>{response_message}</Message></Response>"""
    return app.response_class(xml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
