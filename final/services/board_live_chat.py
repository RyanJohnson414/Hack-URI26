from pathlib import Path
from typing import Dict

from config import config
from services.gemini_client import GeminiClient


class BoardLiveChat:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini
        self.prompt = Path("prompts/system_board_live_chat.txt").read_text(encoding="utf-8")

    def respond(
        self,
        latest_message: str,
        transcript: str,
        coding_experience_level: str = "",
        company_context: str = "",
        projects_context: str = "",
        resume_text: str = "",
    ) -> Dict[str, str]:
        user_prompt = (
            "Latest founder message:\n"
            f"{latest_message}\n\n"
            "Coding experience level:\n"
            f"{coding_experience_level or 'not provided'}\n\n"
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
        return {
            "boss_1": str(raw.get("boss_1", "")).strip(),
            "boss_2": str(raw.get("boss_2", "")).strip(),
            "boss_3": str(raw.get("boss_3", "")).strip(),
        }
