import asyncio
import datetime
import logging
import threading
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

from app.core.events.publisher import get_event_publisher

logger = logging.getLogger("sentinel.core.websocket_manager")


class ConnectionManager:
    """
    Manages active WebSocket connections for real-time video analysis and SOC event monitoring.
    Enforces strict job and user isolation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # job_id -> Set of WebSocket connections
        self._job_connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> Set of WebSocket connections
        self._user_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> {job_id, user_id}
        self._socket_meta: Dict[WebSocket, Dict[str, str]] = {}
        # Main asyncio loop reference for thread-safe event dispatch from worker threads
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Automatically hook into EventPublisher
        publisher = get_event_publisher()
        publisher.subscribe(self._on_publisher_event)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register the main FastAPI asyncio event loop."""
        self._loop = loop

    async def connect(self, websocket: WebSocket, job_id: str, user_id: str) -> None:
        """Accept an authenticated WebSocket and register it for real-time updates."""
        await websocket.accept()

        # Capture current event loop if not yet stored
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        with self._lock:
            if job_id not in self._job_connections:
                self._job_connections[job_id] = set()
            self._job_connections[job_id].add(websocket)

            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(websocket)

            self._socket_meta[websocket] = {"job_id": job_id, "user_id": user_id}

        logger.info(
            f"WebSocket connected for job={job_id}, user={user_id}. "
            f"Active subscriptions for job: {len(self._job_connections[job_id])}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a disconnected WebSocket and clean up internal state."""
        with self._lock:
            meta = self._socket_meta.pop(websocket, None)
            if meta:
                job_id = meta["job_id"]
                user_id = meta["user_id"]

                if job_id in self._job_connections:
                    self._job_connections[job_id].discard(websocket)
                    if not self._job_connections[job_id]:
                        del self._job_connections[job_id]

                if user_id in self._user_connections:
                    self._user_connections[user_id].discard(websocket)
                    if not self._user_connections[user_id]:
                        del self._user_connections[user_id]

                logger.info(f"WebSocket disconnected and cleaned up for job={job_id}, user={user_id}.")

    async def broadcast_to_job(self, job_id: str, message: Dict[str, Any]) -> None:
        """Broadcast a formatted payload to all clients listening to a specific job."""
        with self._lock:
            sockets = list(self._job_connections.get(job_id, set()))

        if not sockets:
            return

        dead_sockets = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to WebSocket (job {job_id}): {e}")
                dead_sockets.append(ws)

        if dead_sockets:
            for ws in dead_sockets:
                self.disconnect(ws)

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Broadcast a formatted payload to all connections owned by a specific user."""
        with self._lock:
            sockets = list(self._user_connections.get(user_id, set()))

        if not sockets:
            return

        dead_sockets = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to WebSocket (user {user_id}): {e}")
                dead_sockets.append(ws)

        if dead_sockets:
            for ws in dead_sockets:
                self.disconnect(ws)

    def _on_publisher_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        job_id: str,
        user_id: str,
    ) -> None:
        """
        Handler invoked by EventPublisher. Dispatches to active WebSockets
        thread-safely through the registered asyncio event loop.
        """
        payload = {
            "type": event_type,
            "data": data,
            "job_id": job_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        # If we have an active loop running, dispatch the coroutine
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_to_job(job_id, payload),
                self._loop,
            )
        else:
            # Fallback: check if running in async context
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.broadcast_to_job(job_id, payload))
            except RuntimeError:
                pass


_global_manager: Optional[ConnectionManager] = None
_manager_lock = threading.Lock()


def get_connection_manager() -> ConnectionManager:
    """Retrieve or initialize the singleton ConnectionManager."""
    global _global_manager
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = ConnectionManager()
    return _global_manager
