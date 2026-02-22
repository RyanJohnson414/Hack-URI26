from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from services.gemini_client import GeminiClient
from services.board_live_chat import BoardLiveChat
from services.interview_coach import InterviewCoach
from services.interview_simulator import InterviewSimulator
from services.investor_prep import InvestorPrep
from services.live_coach_chat import LiveCoachChat
from services.output_writer import OutputWriter
from services.pitch_builder import PitchBuilder
from services.reviewer_agents import ReviewerAgents


VALID_MODES = {"board_investors", "interview_1on1", "investor_pitch_prep"}


@dataclass
class Session:
    session_id: str
    mode: str
    submode: str = ""
    messages: List[str] = field(default_factory=list)
    resume_text: str = ""
    company_context: str = ""
    projects_context: str = ""
    coding_experience_level: str = ""
    phone_number: str = ""
    selected_boss: str = "boss_1"
    final_payload: Dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    def __init__(self) -> None:
        self.sessions: Dict[str, Session] = {}
        self.gemini = GeminiClient()
        self.board_live_chat = BoardLiveChat(self.gemini)
        self.live_coach_chat = LiveCoachChat(self.gemini)
        self.pitch_builder = PitchBuilder(self.gemini)
        self.reviewers = ReviewerAgents(self.gemini)
        self.interview_coach = InterviewCoach(self.gemini)
        self.interview_simulator = InterviewSimulator(self.gemini)
        self.investor_prep = InvestorPrep(self.gemini)
        self.writer = OutputWriter()

    def start_session(
        self,
        mode: str,
        submode: str = "",
        phone_number: str = "",
        resume_text: str = "",
        company_context: str = "",
        projects_context: str = "",
        coding_experience_level: str = "",
    ) -> Session:
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}")
        sid = str(uuid4())
        session = Session(
            session_id=sid,
            mode=mode,
            submode=submode,
            phone_number=phone_number,
            resume_text=resume_text,
            company_context=company_context,
            projects_context=projects_context,
            coding_experience_level=coding_experience_level,
        )
        self.sessions[sid] = session
        return session

    def respond_to_message(self, session_id: str, message: str) -> Dict[str, object]:
        if session_id not in self.sessions:
            raise KeyError("Session not found")
        session = self.sessions[session_id]
        transcript = "\n".join(session.messages)

        if session.mode == "board_investors":
            boss_responses = self.board_live_chat.respond(
                latest_message=message,
                transcript=transcript,
                coding_experience_level=session.coding_experience_level,
                company_context=session.company_context,
                projects_context=session.projects_context,
                resume_text=session.resume_text,
            )
            responses = [
                {"boss_id": "boss_1", "label": "Panel 1", "message": boss_responses.get("boss_1", "")},
                {"boss_id": "boss_2", "label": "Panel 2", "message": boss_responses.get("boss_2", "")},
                {"boss_id": "boss_3", "label": "Panel 3", "message": boss_responses.get("boss_3", "")},
            ]
        else:
            coach_reply = self.live_coach_chat.respond(
                mode=session.mode,
                latest_message=message,
                transcript=transcript,
                coding_experience_level=session.coding_experience_level,
                company_context=session.company_context,
                projects_context=session.projects_context,
                resume_text=session.resume_text,
            )
            label = "Interview Coach" if session.mode == "interview_1on1" else "Pitch Coach"
            responses = [{"boss_id": "coach", "label": label, "message": coach_reply}]

        return {"session_id": session_id, "mode": session.mode, "responses": responses}

    def add_message(
        self,
        session_id: str,
        message: str,
        resume_text: str = "",
        company_context: str = "",
        projects_context: str = "",
        coding_experience_level: str = "",
    ) -> Session:
        if session_id not in self.sessions:
            raise KeyError("Session not found")
        session = self.sessions[session_id]
        if message:
            session.messages.append(message)
        if resume_text:
            session.resume_text = resume_text
        if company_context:
            session.company_context = company_context
        if projects_context:
            session.projects_context = projects_context
        if coding_experience_level:
            session.coding_experience_level = coding_experience_level
        return session

    def select_boss(self, session_id: str, boss_id: str) -> Session:
        if session_id not in self.sessions:
            raise KeyError("Session not found")
        if boss_id not in {"boss_1", "boss_2", "boss_3"}:
            raise ValueError("boss_id must be one of: boss_1, boss_2, boss_3")
        session = self.sessions[session_id]
        session.selected_boss = boss_id
        return session

    def finalize(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise KeyError("Session not found")

        session = self.sessions[session_id]
        transcript = "\n".join(session.messages)

        if session.mode == "board_investors":
            deck = self.pitch_builder.build(
                transcript,
                session.resume_text,
                session.company_context,
                session.projects_context,
            )
            reviewers = self.reviewers.run(
                deck,
                transcript,
                session.resume_text,
                session.company_context,
                session.projects_context,
            )
            consensus = self._merge_reviewer_consensus(reviewers, deck, session.selected_boss)

            deck_path = self.writer.write_json("deck_outline", deck)
            reviewers_path = self.writer.write_json("reviewer_board_report", {"reviewers": reviewers, "consensus": consensus})
            talking_path = self.writer.write_talking_points(session.mode, consensus)

            payload = {
                "mode": session.mode,
                "submode": session.submode,
                "selected_boss": session.selected_boss,
                "company_context": session.company_context,
                "projects_context": session.projects_context,
                "deck": deck,
                "reviewers": reviewers,
                "consensus": consensus,
                "files": {
                    "deck_outline": deck_path,
                    "reviewer_board_report": reviewers_path,
                    "talking_points": talking_path,
                },
            }
        elif session.mode == "interview_1on1":
            coach = self.interview_coach.coach(
                transcript,
                session.resume_text,
                session.submode,
                session.company_context,
                session.projects_context,
                session.coding_experience_level,
            )
            consensus = {
                "top_strengths": coach.get("top_strengths", []),
                "top_gaps": coach.get("top_gaps", []),
                "investor_narrative_60s": coach.get("project_narrative_60s", ""),
                "interview_narrative_60s": coach.get("interview_narrative_60s", ""),
                "past_work_leverage": coach.get("past_work_leverage", []),
                "highest_roi_next_steps_30d": coach.get("highest_roi_next_steps_30d", []),
                "customer_requested_changes": coach.get("customer_requested_changes", []),
                "website_change_recommendations": coach.get("website_change_recommendations", []),
            }
            coach_path = self.writer.write_json("interview_coach_report", coach)
            talking_path = self.writer.write_talking_points(session.mode, consensus)

            payload = {
                "mode": session.mode,
                "submode": session.submode,
                "company_context": session.company_context,
                "projects_context": session.projects_context,
                "coding_experience_level": session.coding_experience_level,
                "interview_coach": coach,
                "consensus": consensus,
                "files": {
                    "interview_report": coach_path,
                    "talking_points": talking_path,
                },
            }
        else:
            investor_prep = self.investor_prep.prepare(
                transcript,
                session.company_context,
                session.projects_context,
                session.resume_text,
                session.coding_experience_level,
            )
            consensus = {
                "top_strengths": investor_prep.get("top_strengths", []),
                "top_gaps": investor_prep.get("top_gaps", []),
                "investor_narrative_60s": investor_prep.get("investor_narrative_60s", ""),
                "highest_roi_next_steps_30d": investor_prep.get("highest_roi_next_steps_30d", []),
                "realistic_investor_questions": investor_prep.get("realistic_investor_questions", []),
                "suggested_strong_answers": investor_prep.get("suggested_strong_answers", []),
                "likely_follow_up_questions": investor_prep.get("likely_follow_up_questions", []),
                "diligence_red_flags": investor_prep.get("diligence_red_flags", []),
                "funding_use_plan": investor_prep.get("funding_use_plan", []),
            }
            prep_path = self.writer.write_json("investor_prep_report", investor_prep)
            talking_path = self.writer.write_talking_points(session.mode, consensus)
            payload = {
                "mode": session.mode,
                "submode": session.submode,
                "company_context": session.company_context,
                "projects_context": session.projects_context,
                "coding_experience_level": session.coding_experience_level,
                "investor_prep": investor_prep,
                "consensus": consensus,
                "files": {
                    "investor_prep_report": prep_path,
                    "talking_points": talking_path,
                },
            }

        interview_simulation = self.interview_simulator.generate(
            mode=session.mode,
            transcript=transcript,
            company_context=session.company_context,
            projects_context=session.projects_context,
            resume_text=session.resume_text,
            consensus=payload.get("consensus", {}),
        )
        interview_path = self.writer.write_json("mock_interview", interview_simulation)
        payload["mock_interview"] = interview_simulation
        payload.setdefault("files", {})["mock_interview"] = interview_path

        session.final_payload = payload
        return payload

    def result(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise KeyError("Session not found")
        session = self.sessions[session_id]
        return {
            "session_id": session.session_id,
            "mode": session.mode,
            "submode": session.submode,
            "selected_boss": session.selected_boss,
            "company_context": session.company_context,
            "projects_context": session.projects_context,
            "coding_experience_level": session.coding_experience_level,
            "messages_count": len(session.messages),
            "has_final": bool(session.final_payload),
            "final": session.final_payload,
        }

    def _merge_reviewer_consensus(self, reviewers: Dict[str, Any], deck: Dict[str, Any], selected_boss: str) -> Dict[str, Any]:
        strengths = []
        gaps = []
        next_steps = []
        customer_changes = []
        website_changes = []

        for _, boss_data in reviewers.items():
            response = boss_data.get("response", {})
            strengths.extend(response.get("top_strengths", []))
            gaps.extend(response.get("top_gaps", []))
            next_steps.extend(response.get("highest_roi_next_steps_30d", []))
            customer_changes.extend(response.get("customer_requested_changes", []))
            website_changes.extend(response.get("website_change_recommendations", []))

        selected = reviewers.get(selected_boss, {})
        selected_response = selected.get("response", {})
        selected_label = selected.get("label", selected_boss)
        selected_focus = selected.get("focus", "")
        selected_path = {
            "boss_id": selected_boss,
            "label": selected_label,
            "focus": selected_focus,
            "top_strengths": selected_response.get("top_strengths", []),
            "top_gaps": selected_response.get("top_gaps", []),
            "key_questions": selected_response.get("key_questions", []),
            "highest_roi_next_steps_30d": selected_response.get("highest_roi_next_steps_30d", []),
            "customer_requested_changes": selected_response.get("customer_requested_changes", []),
            "website_change_recommendations": selected_response.get("website_change_recommendations", []),
        }

        prioritized_strengths = selected_response.get("top_strengths", []) or strengths
        prioritized_gaps = selected_response.get("top_gaps", []) or gaps
        prioritized_next_steps = selected_response.get("highest_roi_next_steps_30d", []) or next_steps
        prioritized_customer_changes = selected_response.get("customer_requested_changes", []) or customer_changes
        prioritized_website_changes = selected_response.get("website_change_recommendations", []) or website_changes

        return {
            "selected_boss_path": selected_path,
            "top_strengths": prioritized_strengths[:5],
            "top_gaps": prioritized_gaps[:5],
            "investor_narrative_60s": deck.get("investor_narrative_60s", ""),
            "interview_narrative_60s": deck.get("interview_narrative_60s", ""),
            "past_work_leverage": deck.get("past_work_leverage", []),
            "highest_roi_next_steps_30d": prioritized_next_steps[:5],
            "customer_requested_changes": prioritized_customer_changes[:5],
            "website_change_recommendations": prioritized_website_changes[:5],
        }
