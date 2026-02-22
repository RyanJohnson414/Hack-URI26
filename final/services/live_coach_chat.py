from pathlib import Path

from config import config
from services.gemini_client import GeminiClient


class LiveCoachChat:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini
        self.prompt = Path("prompts/system_live_coach_chat.txt").read_text(encoding="utf-8")

    def respond(
        self,
        mode: str,
        latest_message: str,
        transcript: str,
        coding_experience_level: str = "",
        company_context: str = "",
        projects_context: str = "",
        resume_text: str = "",
    ) -> str:
        user_prompt = (
            f"Mode: {mode}\n"
            f"Coding experience level: {coding_experience_level or 'not provided'}\n\n"
            "Latest user message:\n"
            f"{latest_message}\n\n"
            "Conversation transcript so far:\n"
            f"{transcript}\n\n"
            "Company context:\n"
            f"{company_context}\n\n"
            "Projects context:\n"
            f"{projects_context}\n\n"
            "Resume context:\n"
            f"{resume_text}\n"
        )
        raw = self.gemini.generate_json(config.gemini_model_main, self.prompt, user_prompt)
        return str(raw.get("coach_reply", "")).strip()
