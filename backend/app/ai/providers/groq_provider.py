"""
Groq AI Provider for SentinelAI Phase 8.

Uses the groq SDK to call Llama/Mixtral models via the Groq API.
Handles API errors gracefully — caller should fall back to MockProvider on failure.
"""
import json
import logging

from app.ai.base import AIProvider, IncidentAnalysisResult, IncidentContext
from app.ai.prompt_builder import build_incident_prompt

logger = logging.getLogger("sentinel.ai.groq")

_DISCLAIMER = (
    "This AI-generated report is a tool to assist human security operators. "
    "It does not constitute evidence, does not identify individuals, and must not "
    "be used as the sole basis for any enforcement, legal, or security action. "
    "All findings require human verification and judgment."
)


class GroqProvider(AIProvider):
    """
    Groq AI provider — fast inference for Llama / Mixtral models.
    Requires: pip install groq>=0.11.0
    """

    def __init__(self, api_key: str, model: str, max_tokens: int, temperature: float):
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate_incident_analysis(
        self, context: IncidentContext
    ) -> IncidentAnalysisResult:
        try:
            from groq import Groq
        except ImportError:
            raise RuntimeError(
                "groq is not installed. Run: pip install groq>=0.11.0"
            )

        client = Groq(api_key=self._api_key)
        prompt = build_incident_prompt(context)

        logger.info(
            "GroqProvider: sending request for report=%s, model=%s",
            context.report_id,
            self._model,
        )

        try:
            completion = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                response_format={"type": "json_object"},
            )

            raw_text = completion.choices[0].message.content.strip()
            parsed = json.loads(raw_text)
            prompt_tokens = (
                completion.usage.prompt_tokens if completion.usage else None
            )

        except json.JSONDecodeError as e:
            logger.error("GroqProvider: failed to parse JSON response: %s", e)
            raise RuntimeError(f"Groq returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error("GroqProvider: API error: %s", e)
            raise RuntimeError(f"Groq API error: {e}") from e

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
