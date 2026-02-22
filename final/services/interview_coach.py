from pathlib import Path
from typing import Any, Dict

from config import config
from services.gemini_client import GeminiClient


class InterviewCoach:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini
        self.prompt = Path("prompts/system_interview_coach.txt").read_text(encoding="utf-8")

    def coach(
        self,
        transcript: str,
        resume_text: str = "",
        submode: str = "",
        company_context: str = "",
        projects_context: str = "",
        coding_experience_level: str = "",
    ) -> Dict[str, Any]:
        user_prompt = (
            f"Mode: interview_1on1\nSubmode: {submode or 'none'}\n\n"
            f"Coding experience level: {coding_experience_level or 'not provided'}\n\n"
            "Conversation transcript:\n"
            f"{transcript}\n\n"
            "Company context (optional):\n"
            f"{company_context}\n\n"
            "Projects context (optional, startups or personal projects):\n"
            f"{projects_context}\n\n"
            "Resume text:\n"
            f"{resume_text}"
        )
        return self.gemini.generate_json(config.gemini_model_main, self.prompt, user_prompt)
