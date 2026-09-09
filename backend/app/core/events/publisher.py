import abc
import datetime
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("sentinel.core.events.publisher")


class EventPublisher(abc.ABC):
    """
    Abstract Base Class for publishing real-time security events and session telemetry.
    Allows swappable implementations (InMemory for Phase 7, Redis/Kafka in future).
    """

    @abc.abstractmethod
    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        job_id: str,
        user_id: str,
    ) -> None:
        """Publish a security event message (security_event, event_updated)."""
        pass

    @abc.abstractmethod
    def publish_status(
        self,
        job_id: str,
        user_id: str,
        status_data: Dict[str, Any],
    ) -> None:
        """Publish real-time telemetry or job lifecycle updates (status_update, heartbeat)."""
        pass

    @abc.abstractmethod
    def subscribe(
        self,
        callback: Callable[[str, Dict[str, Any], str, str], None],
    ) -> None:
        """Subscribe a handler (e.g. WebSocket connection manager)."""
        pass

    @abc.abstractmethod
    def unsubscribe(
        self,
        callback: Callable[[str, Dict[str, Any], str, str], None],
    ) -> None:
        """Unsubscribe a handler."""
        pass


class InMemoryEventPublisher(EventPublisher):
    """
    Thread-safe in-memory event publisher for Phase 7.
    Dispatches events to registered listeners synchronously or via safe callbacks.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: List[Callable[[str, Dict[str, Any], str, str], None]] = []

    def subscribe(
        self,
        callback: Callable[[str, Dict[str, Any], str, str], None],
    ) -> None:
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)
                logger.debug(f"Subscribed callback to EventPublisher. Total: {len(self._subscribers)}")

    def unsubscribe(
        self,
        callback: Callable[[str, Dict[str, Any], str, str], None],
    ) -> None:
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
                logger.debug(f"Unsubscribed callback from EventPublisher. Total: {len(self._subscribers)}")

    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        job_id: str,
        user_id: str,
    ) -> None:
        with self._lock:
            callbacks = list(self._subscribers)

        for cb in callbacks:
            try:
                cb(event_type, data, job_id, user_id)
            except Exception as e:
                logger.error(f"Error in EventPublisher subscriber callback: {e}", exc_info=True)

    def publish_status(
        self,
        job_id: str,
        user_id: str,
        status_data: Dict[str, Any],
    ) -> None:
        self.publish(
            event_type="status_update",
            data=status_data,
            job_id=job_id,
            user_id=user_id,
        )


_global_publisher: Optional[EventPublisher] = None
_publisher_lock = threading.Lock()


def get_event_publisher() -> EventPublisher:
    """Retrieve or initialize the singleton EventPublisher."""
    global _global_publisher
    if _global_publisher is None:
        with _publisher_lock:
            if _global_publisher is None:
                _global_publisher = InMemoryEventPublisher()
    return _global_publisher
