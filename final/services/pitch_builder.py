from pathlib import Path
from typing import Any, Dict

from config import config
from services.gemini_client import GeminiClient


class PitchBuilder:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini
        self.prompt = Path("prompts/system_pitch_builder.txt").read_text(encoding="utf-8")

    def build(
        self,
        transcript: str,
        resume_text: str = "",
        company_context: str = "",
        projects_context: str = "",
    ) -> Dict[str, Any]:
        user_prompt = (
            "Founder transcript:\n"
            f"{transcript}\n\n"
            "Company context (optional, for existing company pitches):\n"
            f"{company_context}\n\n"
            "Projects context (optional, startups or personal projects):\n"
            f"{projects_context}\n\n"
            "Resume text (optional):\n"
            f"{resume_text}"
        )
        return self.gemini.generate_json(config.gemini_model_main, self.prompt, user_prompt)
