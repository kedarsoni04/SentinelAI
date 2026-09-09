"""
Abstract base class and data structures for the AI Incident Intelligence layer.

Design principles:
- AIProvider is a pure interface — no concrete dependencies here.
- IncidentContext contains only sanitized textual metadata (no PII, no frame paths).
- IncidentAnalysisResult is a plain dataclass for easy serialisation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Input Context ────────────────────────────────────────────────────────────

@dataclass
class EventSummary:
    """
    Sanitized summary of a single SecurityEvent for AI context.
    Contains ONLY observable metadata — no identity inferences.
    """
    event_id: str
    event_type: str          # e.g. "INTRUSION", "LOITERING"
    severity: str            # e.g. "HIGH"
    title: str
    description: str
    start_timestamp: float   # seconds into the video
    end_timestamp: Optional[float]
    duration_seconds: Optional[float]
    confidence: Optional[float]
    class_name: Optional[str]  # detected object class, e.g. "person"
    rule_name: Optional[str]
    zone_name: Optional[str]


@dataclass
class IncidentContext:
    """
    Complete, sanitized context package sent to the AI provider.
    No raw video frames, filesystem paths, or personally identifiable information.
    """
    report_id: str
    camera_name: Optional[str]
    camera_location: Optional[str]
    zone_names: List[str] = field(default_factory=list)
    job_original_filename: Optional[str] = None
    job_duration_seconds: Optional[float] = None
    events: List[EventSummary] = field(default_factory=list)
    total_events: int = 0
    event_type_counts: Dict[str, int] = field(default_factory=dict)
    severity_counts: Dict[str, int] = field(default_factory=dict)


# ─── Output Result ────────────────────────────────────────────────────────────

@dataclass
class IncidentAnalysisResult:
    """
    Structured result returned by an AIProvider after analysis.
    All fields are plain text or simple data structures — ready for DB storage.
    """
    summary: str
    timeline: List[Dict[str, str]]   # [{timestamp_label, event_type, description}]
    risk_level: str                  # LOW / MEDIUM / HIGH / CRITICAL
    risk_explanation: str
    recommendations: List[str]       # Human operator action items
    disclaimer: str                  # Mandatory human-review disclaimer
    ai_provider: str
    ai_model: str
    prompt_tokens: Optional[int] = None


# ─── Abstract Provider ────────────────────────────────────────────────────────

class AIProvider(ABC):
    """
    Abstract interface for AI backend providers.

    Implementations: GeminiProvider, GroqProvider, MockProvider.
    Selected at runtime by provider_factory.get_ai_provider().
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier string."""
        ...

    @abstractmethod
    async def generate_incident_analysis(
        self, context: IncidentContext
    ) -> IncidentAnalysisResult:
        """
        Generate a structured AI incident analysis from sanitized context.
        Must NEVER make enforcement decisions or identify individuals.
        Must ALWAYS include a human-review disclaimer.
        """
        ...
