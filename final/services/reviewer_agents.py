from pathlib import Path
from typing import Any, Dict

from config import config
from services.gemini_client import GeminiClient


class ReviewerAgents:
    def __init__(self, gemini: GeminiClient) -> None:
        self.gemini = gemini
        self.pmfit_prompt = Path("prompts/system_reviewer_pmfit.txt").read_text(encoding="utf-8")
        self.tech_prompt = Path("prompts/system_reviewer_tech.txt").read_text(encoding="utf-8")
        self.gtm_prompt = Path("prompts/system_reviewer_gtm.txt").read_text(encoding="utf-8")

    def run(
        self,
        pitch_outline: Dict[str, Any],
        transcript: str,
        resume_text: str = "",
        company_context: str = "",
        projects_context: str = "",
    ) -> Dict[str, Any]:
        user_prompt = (
            "Pitch outline JSON:\n"
            f"{pitch_outline}\n\n"
            "Founder transcript:\n"
            f"{transcript}\n\n"
            "Company context (optional):\n"
            f"{company_context}\n\n"
            "Projects context (optional, startups or personal projects):\n"
            f"{projects_context}\n\n"
            "Resume text:\n"
            f"{resume_text}"
        )
        return {
            "boss_1": {
                "label": "Customer Panel 1",
                "focus": "Customer Value and Problem Fit",
                "response": self.gemini.generate_json(config.gemini_model_reviewer_a, self.pmfit_prompt, user_prompt),
            },
            "boss_2": {
                "label": "Customer Panel 2",
                "focus": "Product Usability and Technical Friction",
                "response": self.gemini.generate_json(config.gemini_model_reviewer_b, self.tech_prompt, user_prompt),
            },
            "boss_3": {
                "label": "Customer Panel 3",
                "focus": "Adoption, Messaging, and Trust Signals",
                "response": self.gemini.generate_json(config.gemini_model_reviewer_c, self.gtm_prompt, user_prompt),
            },
        }
