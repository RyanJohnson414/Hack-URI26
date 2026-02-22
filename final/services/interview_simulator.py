from pathlib import Path
from typing import Any, Dict

from config import config
from services.gemini_client import GeminiClient


class InterviewSimulator:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini
        self.prompt = Path("prompts/system_interview_simulator.txt").read_text(encoding="utf-8")

    def generate(
        self,
        mode: str,
        transcript: str,
        company_context: str,
        projects_context: str,
        resume_text: str,
        consensus: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_prompt = (
            f"Session mode: {mode}\n\n"
            "Founder transcript:\n"
            f"{transcript}\n\n"
            "Company context:\n"
            f"{company_context}\n\n"
            "Projects context:\n"
            f"{projects_context}\n\n"
            "Resume text:\n"
            f"{resume_text}\n\n"
            "Consensus summary JSON:\n"
            f"{consensus}\n"
        )
        return self.gemini.generate_json(config.gemini_model_main, self.prompt, user_prompt)
