import json
from typing import Any, Dict, List

import google.generativeai as genai

from config import config


class GeminiClient:
    def __init__(self) -> None:
        if not config.gemini_api_key:
            raise ValueError(
                "Missing Gemini API key. Set one of: GEMINI_API_KEY, GOOGLE_API_KEY, or key in final/.env"
            )
        genai.configure(api_key=config.gemini_api_key)
        self._available_models = self._load_available_models()
        self._preferred_fallbacks = [
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ]
        self._model_aliases = {
            "gemini-1.5-flash": "gemini-3-flash-preview",
            "gemini-1.5-pro": "gemini-3-flash-preview",
        }

    def _load_available_models(self) -> List[str]:
        try:
            models = genai.list_models()
        except Exception:
            return []
        names: List[str] = []
        for model in models:
            name = getattr(model, "name", "")
            if not name:
                continue
            short = name.replace("models/", "")
            names.append(short)
        return names

    def _choose_model(self, requested: str) -> str:
        requested = self._model_aliases.get(requested, requested)
        if not self._available_models:
            return requested
        if requested in self._available_models:
            return requested
        for candidate in self._preferred_fallbacks:
            if candidate in self._available_models:
                return candidate
        return self._available_models[0]

    def generate_json(self, model_name: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        candidates = [self._choose_model(model_name), *self._preferred_fallbacks]
        deduped_candidates: List[str] = []
        for candidate in candidates:
            if candidate and candidate not in deduped_candidates:
                deduped_candidates.append(candidate)

        response = None
        last_exc: Exception | None = None
        for candidate in deduped_candidates:
            try:
                model = genai.GenerativeModel(
                    model_name=candidate,
                    system_instruction=system_prompt,
                )
                response = model.generate_content(
                    user_prompt,
                    generation_config={"response_mime_type": "application/json"},
                )
                break
            except Exception as exc:
                last_exc = exc

        if response is None and last_exc is not None:
            raise last_exc
        text = (response.text or "").strip()
        if not text:
            return {"raw": "", "error": "Empty response"}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text, "error": "Invalid JSON from model"}
