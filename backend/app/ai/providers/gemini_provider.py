"""
Gemini AI Provider for SentinelAI Phase 8.

Uses the google-generativeai SDK to call Gemini models.
Handles API errors gracefully — caller should fall back to MockProvider on failure.
"""
import json
import logging
from typing import Optional

from app.ai.base import AIProvider, IncidentAnalysisResult, IncidentContext
from app.ai.prompt_builder import build_incident_prompt

logger = logging.getLogger("sentinel.ai.gemini")

_DISCLAIMER = (
    "This AI-generated report is a tool to assist human security operators. "
    "It does not constitute evidence, does not identify individuals, and must not "
    "be used as the sole basis for any enforcement, legal, or security action. "
    "All findings require human verification and judgment."
)


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider.
    Requires: pip install google-generativeai>=0.8.0
    """

    def __init__(self, api_key: str, model: str, max_tokens: int, temperature: float):
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate_incident_analysis(
        self, context: IncidentContext
    ) -> IncidentAnalysisResult:
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai>=0.8.0"
            )

        genai.configure(api_key=self._api_key)

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        model = genai.GenerativeModel(
            model_name=self._model,
            generation_config=generation_config,
        )

        prompt = build_incident_prompt(context)

        logger.info(
            "GeminiProvider: sending request for report=%s, model=%s",
            context.report_id,
            self._model,
        )
        try:
            response = model.generate_content(prompt)
            raw_text = (response.text or "").strip()
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            parsed = json.loads(raw_text)
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", None)

        except json.JSONDecodeError as e:
            logger.error("GeminiProvider: failed to parse JSON response: %s", e)
            raise RuntimeError(f"Gemini returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error("GeminiProvider: API error: %s", e)
            raise RuntimeError(f"Gemini API error: {e}") from e

        return IncidentAnalysisResult(
            summary=parsed.get("summary", "Analysis could not be completed."),
            timeline=parsed.get("timeline", []),
            risk_level=parsed.get("risk_level", "MEDIUM"),
            risk_explanation=parsed.get("risk_explanation", ""),
            recommendations=parsed.get("recommendations", []),
            disclaimer=parsed.get("disclaimer", _DISCLAIMER),
            ai_provider=self.provider_name,
            ai_model=self._model,
            prompt_tokens=prompt_tokens,
        )
