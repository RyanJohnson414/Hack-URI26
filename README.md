# The Chartroom (MVP)

Python + Flask + Gemini + SMS-first flow for pitch deck structuring and interview coaching.

## Modes
- `board_investors`
- `interview_1on1`
  - optional submode: `software_engineer_interview_prep`
- `investor_pitch_prep`

## Inputs
- `company_context` (optional, recommended for existing-company pitches)
- `resume_text` (optional)
- `projects_text` (optional, startups or personal projects)
- `message` (ongoing conversation text)

## Setup
1. Create and activate a virtualenv.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Ensure `.env` in project root contains Gemini API settings (and optional Twilio values).
4. Run:
   - `python app.py`

## API
- `POST /api/session/start`
- `POST /api/session/message`
- `POST /api/session/<session_id>/finalize`
- `GET /api/session/<session_id>/result`
- `POST /webhook/sms`

## Example curl
Start session:
```bash
curl -X POST http://127.0.0.1:5000/api/session/start -H "Content-Type: application/json" -d '{"mode":"board_investors"}'
```

Add message:
```bash
curl -X POST http://127.0.0.1:5000/api/session/message -H "Content-Type: application/json" -d '{"session_id":"<ID>","message":"We help SMBs automate procurement.","company_context":"Existing company: ...","resume_text":"Optional"}'
```

Finalize:
```bash
curl -X POST http://127.0.0.1:5000/api/session/<ID>/finalize
```

## Twilio webhook
- Point incoming message webhook to: `http://<host>:5000/webhook/sms`
- Text `START` to begin.

## Output files
Saved in `outputs/`:
- `deck_outline_<timestamp>.json`
- `reviewer_board_report_<timestamp>.json`
- `interview_coach_report_<timestamp>.json`
- `talking_points_<timestamp>.txt`
