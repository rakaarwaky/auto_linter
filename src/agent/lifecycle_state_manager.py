"""Agent lifecycle — startup, shutdown, health management."""

from __future__ import annotations
import logging
import time
from typing import Any

logger = logging.getLogger("agent.lifecycle")


class AgentState:
    """Track agent lifecycle state."""

    def __init__(self) -> None:
        self.started = False
        self.start_time: float | None = None
        self._status = "initializing"

    @property
    def uptime(self) -> float:
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    @property
    def status(self) -> str:
        return self._status

    def mark_started(self) -> None:
        self.started = True
        self.start_time = time.time()
        self._status = "running"
        logger.info("Agent started (uptime tracking enabled)")

    def mark_stopped(self) -> None:
        self._status = "stopped"
        logger.info("Agent stopped")

    def mark_degraded(self) -> None:
        self._status = "degraded"

    def health(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "uptime_seconds": round(self.uptime, 1),
            "started": self.started,
        }


_state = AgentState()


def get_state() -> AgentState:
    return _state
