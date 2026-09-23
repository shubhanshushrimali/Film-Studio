"""Job states. A clip cannot skip the human check."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class JobStatus(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


_NEXT: dict[JobStatus, set[JobStatus]] = {
    JobStatus.RECEIVED: {JobStatus.VALIDATED, JobStatus.FAILED},
    JobStatus.VALIDATED: {JobStatus.QUEUED, JobStatus.FAILED},
    JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.RUNNING: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.AWAITING_APPROVAL,
        JobStatus.CANCELLED,
    },
    JobStatus.AWAITING_APPROVAL: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.FAILED: {JobStatus.RETRYING},
    JobStatus.RETRYING: {JobStatus.QUEUED},
    JobStatus.COMPLETED: set(),
    JobStatus.CANCELLED: set(),
}


class BadMove(RuntimeError):
    pass


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.RECEIVED
    tries: int = 0
    history: list[tuple[str, str]] = field(default_factory=list)

    def move(self, status: JobStatus) -> None:
        if status not in _NEXT[self.status]:
            raise BadMove(f"Cannot go from {self.status.value} to {status.value}")
        if status == JobStatus.RETRYING:
            self.tries += 1
            if self.tries > 3:
                raise BadMove("Stopped after 3 tries. A person must decide.")
        self.history.append((self.status.value, datetime.now(timezone.utc).isoformat()))
        self.status = status
