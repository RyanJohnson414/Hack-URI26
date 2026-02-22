import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _first_nonempty(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "")
        if value and value.strip():
            return value.strip().strip('"').strip("'")
    return ""


@dataclass
class Config:
    # Support common names users already have in .env.
    gemini_api_key: str = _first_nonempty("GEMINI_API_KEY", "GOOGLE_API_KEY", "key")
    gemini_model_main: str = os.getenv("GEMINI_MODEL_MAIN", "gemini-1.5-pro")
    gemini_model_reviewer_a: str = os.getenv("GEMINI_MODEL_REVIEWER_A", "gemini-1.5-flash")
    gemini_model_reviewer_b: str = os.getenv("GEMINI_MODEL_REVIEWER_B", "gemini-1.5-flash")
    gemini_model_reviewer_c: str = os.getenv("GEMINI_MODEL_REVIEWER_C", "gemini-1.5-flash")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER", "")
    base_url: str = os.getenv("BASE_URL", "http://127.0.0.1:5000")


config = Config()
