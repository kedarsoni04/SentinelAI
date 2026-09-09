"""
AI Provider Factory for SentinelAI Phase 8.

Selects and instantiates the appropriate AIProvider based on application settings.
Always falls back to MockProvider if the configured provider's API key is missing
or if an import error occurs — the application never crashes due to missing AI config.
"""
import logging

from app.ai.base import AIProvider
from app.ai.providers.mock_provider import MockProvider
from app.core.config import settings

logger = logging.getLogger("sentinel.ai.factory")


def get_ai_provider() -> AIProvider:
    """
    Instantiate and return the configured AI provider.

    Selection logic:
    1. If AI_PROVIDER=gemini AND GEMINI_API_KEY is set → GeminiProvider
    2. If AI_PROVIDER=groq AND GROQ_API_KEY is set → GroqProvider
    3. Any other case (missing key, import error, unknown provider) → MockProvider

    This function is lightweight — it should be called per-request, not cached,
    so config changes take effect without restart.
    """
    provider = settings.AI_PROVIDER.lower().strip()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
            logger.warning(
                "AI_PROVIDER=gemini but GEMINI_API_KEY is not set — falling back to mock"
            )
            return MockProvider()
        try:
            from app.ai.providers.gemini_provider import GeminiProvider
            logger.info("AIProviderFactory: using GeminiProvider (model=%s)", settings.GEMINI_MODEL)
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            )
        except ImportError as e:
            logger.warning("GeminiProvider import failed (%s) — falling back to mock", e)
            return MockProvider()

    if provider == "groq":
        if not settings.GROQ_API_KEY or not settings.GROQ_API_KEY.strip():
            logger.warning(
                "AI_PROVIDER=groq but GROQ_API_KEY is not set — falling back to mock"
            )
            return MockProvider()
        try:
            from app.ai.providers.groq_provider import GroqProvider
            logger.info("AIProviderFactory: using GroqProvider (model=%s)", settings.GROQ_MODEL)
            return GroqProvider(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            )
        except ImportError as e:
            logger.warning("GroqProvider import failed (%s) — falling back to mock", e)
            return MockProvider()

    if provider != "mock":
        logger.warning(
            "Unknown AI_PROVIDER=%r — falling back to mock", settings.AI_PROVIDER
        )

    logger.info("AIProviderFactory: using MockProvider")
    return MockProvider()
