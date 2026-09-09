from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.models.security_rule import SecurityEventSeverity, SecurityEventType, SecurityRule
from app.models.security_zone import SecurityZone, ZoneType


@dataclass
class RuleDefinition:
    """In-memory validated representation of an active SecurityRule and associated Zone."""
    id: str
    name: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    threshold_value: Optional[float] = None
    threshold_seconds: Optional[float] = None
    minimum_confidence: float = 0.5
    class_filters: List[str] = field(default_factory=list)
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    zone_coordinates: List[Dict[str, float]] = field(default_factory=list)

    @classmethod
    def from_orm(cls, rule: SecurityRule) -> "RuleDefinition":
        """Construct RuleDefinition from SQLAlchemy SecurityRule ORM object."""
        zone_id = None
        zone_name = None
        zone_type = None
        zone_coords = []

        if rule.zone:
            zone_id = rule.zone.id
            zone_name = rule.zone.name
            zone_type = rule.zone.zone_type
            zone_coords = rule.zone.coordinates or []

        classes = []
        if rule.class_filters:
            if isinstance(rule.class_filters, list):
                classes = [str(c).lower().strip() for c in rule.class_filters]

        return cls(
            id=rule.id,
            name=rule.name,
            event_type=rule.event_type,
            severity=rule.severity,
            threshold_value=rule.threshold_value,
            threshold_seconds=rule.threshold_seconds,
            minimum_confidence=rule.minimum_confidence if rule.minimum_confidence is not None else 0.5,
            class_filters=classes,
            zone_id=zone_id,
            zone_name=zone_name,
            zone_type=zone_type,
            zone_coordinates=zone_coords,
        )

    def matches_class(self, class_name: str) -> bool:
        """Check if an object's class matches the rule's class filter whitelist."""
        if not self.class_filters:
            return True
        return class_name.lower().strip() in self.class_filters
