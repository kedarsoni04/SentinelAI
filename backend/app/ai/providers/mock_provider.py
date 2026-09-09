"""
Mock AI Provider — zero-dependency fallback for SentinelAI Phase 8.

Used when:
  - AI_PROVIDER=mock (explicit)
  - Selected provider's API key is missing or invalid
  - External AI APIs are unreachable

Returns a deterministic, plausible AI incident analysis with an artificial
300ms delay to simulate a real API call. Safe for demos and CI/CD.
"""
import asyncio
import json
import logging
from typing import Dict

from app.ai.base import AIProvider, IncidentAnalysisResult, IncidentContext

logger = logging.getLogger("sentinel.ai.mock")

_DISCLAIMER = (
    "This AI-generated report is a tool to assist human security operators. "
    "It does not constitute evidence, does not identify individuals, and must not "
    "be used as the sole basis for any enforcement, legal, or security action. "
    "All findings require human verification and judgment."
)


class MockProvider(AIProvider):
    """
    Deterministic mock AI provider. No external API calls.
    Generates plausible-sounding analysis based on IncidentContext statistics.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-v1"

    async def generate_incident_analysis(
        self, context: IncidentContext
    ) -> IncidentAnalysisResult:
        # Simulate processing latency
        await asyncio.sleep(0.35)

        logger.info(
            "MockProvider: generating analysis for report=%s, events=%d",
            context.report_id,
            context.total_events,
        )

        # Derive risk level from severity distribution
        risk_level = self._derive_risk_level(context.severity_counts)

        # Build a timeline from events
        timeline = []
        for evt in sorted(context.events, key=lambda e: e.start_timestamp):
            minutes = int(evt.start_timestamp // 60)
            seconds = int(evt.start_timestamp % 60)
            timeline.append({
                "timestamp_label": f"{minutes}:{seconds:02d}",
                "event_type": evt.event_type,
                "description": evt.description,
            })

        # Build summary
        type_summary = ", ".join(
            f"{count} {etype.lower().replace('_', ' ')} detection(s)"
            for etype, count in context.event_type_counts.items()
        )
        camera_ref = (
            f"camera '{context.camera_name}'" if context.camera_name else "the monitored area"
        )
        summary = (
            f"Analysis of {camera_ref} identified {context.total_events} security event(s) "
            f"including {type_summary}. "
            f"Events were recorded over the monitored period with varying severity levels. "
            f"SOC operator review is required to assess the significance of these detections."
        )

        risk_explanation = self._derive_risk_explanation(risk_level, context)

        recommendations = [
            f"Review video footage at the identified timestamps for {camera_ref}.",
            "Verify whether detected events match known operational activities or represent anomalies.",
            "Check that all relevant security zones and rules are correctly configured.",
            "Document findings in the incident log with operator assessment notes.",
            "Escalate to a senior operator if HIGH or CRITICAL events cannot be explained.",
            "Consider adjusting detection thresholds if false positives are identified.",
        ]

        return IncidentAnalysisResult(
            summary=summary,
            timeline=timeline,
            risk_level=risk_level,
            risk_explanation=risk_explanation,
            recommendations=recommendations[:5],
            disclaimer=_DISCLAIMER,
            ai_provider=self.provider_name,
            ai_model=self.model_name,
            prompt_tokens=None,
        )

    def _derive_risk_level(self, severity_counts: Dict[str, int]) -> str:
        """Derive risk level from severity distribution."""
        if severity_counts.get("CRITICAL", 0) > 0:
            return "CRITICAL"
        if severity_counts.get("HIGH", 0) > 0:
            return "HIGH"
        if severity_counts.get("MEDIUM", 0) > 0:
            return "MEDIUM"
        return "LOW"

    def _derive_risk_explanation(self, risk_level: str, context: IncidentContext) -> str:
        explanations = {
            "CRITICAL": (
                f"One or more CRITICAL severity events were detected in {context.camera_name or 'the monitored area'}. "
                "This risk level indicates detections that require immediate human review and potential escalation."
            ),
            "HIGH": (
                f"HIGH severity events were detected, suggesting significant deviations from expected patterns. "
                "Human operator review is strongly recommended before dismissing these events."
            ),
            "MEDIUM": (
                f"MEDIUM severity detections were observed. These may represent routine operational activities "
                "or genuine anomalies. Operator judgment is required to distinguish between them."
            ),
            "LOW": (
                "All detected events are LOW severity. These are informational detections that may reflect "
                "normal activity. Review is recommended to confirm no escalation is needed."
            ),
        }
        return explanations.get(risk_level, "Risk assessment requires human operator review.")
