"""
Prompt builder for the AI Incident Intelligence layer.

Constructs a privacy-respecting, role-constrained prompt from IncidentContext.
The prompt explicitly forbids:
  - Identity attribution
  - Criminal intent inference
  - Autonomous enforcement recommendations
  - Certainty claims about observed behavior
"""
import json
from app.ai.base import IncidentContext


_SYSTEM_PREAMBLE = """You are a Security Operations Center (SOC) analysis assistant tool.
Your role is to help HUMAN operators understand patterns in automatically detected security events.

STRICT CONSTRAINTS — you MUST follow these exactly:
1. You assist human operators. You do NOT make enforcement decisions.
2. You do NOT identify, name, or attribute criminal intent to any individual.
3. You do NOT claim certainty about intent or actions — only describe observable detections.
4. You do NOT recommend contacting authorities directly.
5. You MUST include a human-review disclaimer in every report.
6. All recommendations must be framed as suggested human review actions, not autonomous actions.
7. Output ONLY valid JSON — no markdown fences, no extra text before or after the JSON object."""


def build_incident_prompt(context: IncidentContext) -> str:
    """
    Build a structured, privacy-safe prompt from an IncidentContext.
    Returns the full prompt string to send to the AI provider.
    """
    # Format event list for the prompt
    events_text = []
    for i, evt in enumerate(context.events, 1):
        parts = [
            f"  Event {i}:",
            f"    Type: {evt.event_type}",
            f"    Severity: {evt.severity}",
            f"    Title: {evt.title}",
            f"    Description: {evt.description}",
            f"    Timestamp: {evt.start_timestamp:.1f}s",
        ]
        if evt.duration_seconds is not None:
            parts.append(f"    Duration: {evt.duration_seconds:.1f}s")
        if evt.confidence is not None:
            parts.append(f"    Detection Confidence: {evt.confidence:.0%}")
        if evt.class_name:
            parts.append(f"    Detected Object Class: {evt.class_name}")
        if evt.rule_name:
            parts.append(f"    Triggered Rule: {evt.rule_name}")
        if evt.zone_name:
            parts.append(f"    Zone: {evt.zone_name}")
        events_text.append("\n".join(parts))

    # Build context block
    context_block = f"""INCIDENT CONTEXT:
Camera: {context.camera_name or 'Unknown'}
Location: {context.camera_location or 'Unknown'}
Video Source: {context.job_original_filename or 'N/A'}
Video Duration: {f"{context.job_duration_seconds:.1f}s" if context.job_duration_seconds else "Unknown"}
Security Zones Involved: {', '.join(context.zone_names) if context.zone_names else 'None specified'}
Total Events Detected: {context.total_events}
Event Type Breakdown: {json.dumps(context.event_type_counts)}
Severity Breakdown: {json.dumps(context.severity_counts)}

DETECTED EVENTS:
{chr(10).join(events_text)}"""

    schema_block = """{
  "summary": "<2-3 sentence factual description of the detected events, using passive voice, no identity claims>",
  "timeline": [
    {
      "timestamp_label": "<e.g. 0:12>",
      "event_type": "<event type string>",
      "description": "<one sentence factual description of the detection>"
    }
  ],
  "risk_level": "<one of: LOW | MEDIUM | HIGH | CRITICAL>",
  "risk_explanation": "<2-3 sentences explaining why this risk level was assigned based only on observable patterns>",
  "recommendations": [
    "<Specific human review action item — must start with an action verb like Review, Verify, Check, Notify, Document>",
    "<Another action item>"
  ],
  "disclaimer": "This AI-generated report is a tool to assist human security operators. It does not constitute evidence, does not identify individuals, and must not be used as the sole basis for any enforcement, legal, or security action. All findings require human verification and judgment."
}"""

    return f"""{_SYSTEM_PREAMBLE}

{context_block}

Analyze the above security events and respond with ONLY a valid JSON object matching this exact schema:
{schema_block}

Rules for your response:
- "summary": factual only, passive voice, no identity or intent claims
- "timeline": one entry per event, ordered chronologically
- "risk_level": assign based on severity distribution and event patterns
- "recommendations": 3-6 items, each a concrete human review action
- "disclaimer": copy the disclaimer text verbatim from the schema
- Output ONLY the JSON object. No markdown. No commentary."""
