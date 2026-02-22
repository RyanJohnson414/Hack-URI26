# The Chartroom (MVP)

Python + Flask + Gemini + SMS-first flow for pitch deck structuring and interview coaching. This app is prepared to help first time interviewers and experienced interviewers to prepare themselves for the high pressure of interviews.

## Modes
- `board_investors`
  -'choice of 3 modes <1> related to financial understandings and goals and how they are meant to achieve their financial goals, <2> one for understanding user experiences and prepared to tailor make the site to connect to potential users and how to fix the user experience of the site features that people want and features that people dont want, <3> Adoption and pushing to production good for reviewing the final spots where people need to see the risks of their publishing off to the market and how to address them before its too late'
- `interview 1on1`
  - optional submode: `software_engineer_interview_prep` and needed interview prep for interviewing for internships especially for unexperienced applicants so they do not fold under the pressure of a true interview.
- `investor_pitch_prep` prepare to pitch the current startup to a new group of investors and properly prepare for the questions they will ask and what you need to do to be ready to properly interview with large stakes of money and the future of your startup on the line.

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
- `interview_coach_report_<timestamp>.json`
- `talking_points_<timestamp>.txt`

