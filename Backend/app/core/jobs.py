"""In-process async job manager with progress reporting.

Analysing a 100-page policy takes 10-60 seconds. Holding an HTTP request open
for that gives the user a spinner with no information and dies to any proxy
timeout. Instead uploads return a job id immediately and the client subscribes to
progress events.

Scope, stated honestly: this is an in-process manager backed by an asyncio queue.
It is the right call for a single-node deployment and it makes the concurrency
model explicit. It does not survive a restart and does not scale across workers;
the swap to Redis/RQ or Celery is behind the same `submit`/`get`/`subscribe`
interface.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

log = logging.getLogger(__name__)


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    kind: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    stage: str = "queued"
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    meta: dict = field(default_factory=dict)
    _subscribers: list[asyncio.Queue] = field(default_factory=list, repr=False)

    def to_dict(self) -> dict:
        return {
            "job_id": self.id,
            "kind": self.kind,
            "status": self.status.value,
            "progress": round(self.progress, 3),
            "stage": self.stage,
            "error": self.error,
            "meta": self.meta,
            "elapsed_s": round((self.finished_at or time.time()) - self.created_at, 2),
        }


class JobManager:
    def __init__(self, concurrency: int = 2, ttl_seconds: int = 3600):
        self._jobs: dict[str, Job] = {}
        self._semaphore = asyncio.Semaphore(concurrency)
        self._tasks: set[asyncio.Task] = set()
        self._ttl = ttl_seconds

    def submit(
        self,
        kind: str,
        coro_factory: Callable[[JobHandle], Awaitable[Any]],
        meta: dict | None = None,
    ) -> Job:
        job = Job(id=uuid.uuid4().hex[:16], kind=kind, meta=meta or {})
        self._jobs[job.id] = job

        async def runner() -> None:
            async with self._semaphore:
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
                await self._publish(job, "started")
                try:
                    job.result = await coro_factory(JobHandle(job, self))
                    job.status = JobStatus.SUCCEEDED
                    job.progress = 1.0
                    job.stage = "done"
                except asyncio.CancelledError:
                    job.status = JobStatus.FAILED
                    job.error = "Cancelled"
                    raise
                except Exception as exc:
                    log.exception("Job %s (%s) failed", job.id, job.kind)
                    job.status = JobStatus.FAILED
                    # Surface the message, never the traceback.
                    job.error = str(exc) or exc.__class__.__name__
                finally:
                    job.finished_at = time.time()
                    await self._publish(job, "finished")
                    self._evict_expired()

        task = asyncio.create_task(runner())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        job = self._jobs[job_id]
        queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        job._subscribers.append(queue)
        # Replay current state so a late subscriber is never stuck at 0%.
        await queue.put({"event": "state", **job.to_dict()})
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        job = self._jobs.get(job_id)
        if job and queue in job._subscribers:
            job._subscribers.remove(queue)

    async def _publish(self, job: Job, event: str) -> None:
        payload = {"event": event, **job.to_dict()}
        for queue in list(job._subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                # A slow client must never apply backpressure to the worker.
                log.debug("Dropping progress event for saturated subscriber on job %s", job.id)

    def _evict_expired(self) -> None:
        cutoff = time.time() - self._ttl
        for job_id, job in list(self._jobs.items()):
            if job.finished_at and job.finished_at < cutoff:
                del self._jobs[job_id]

    async def shutdown(self) -> None:
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)


@dataclass
class JobHandle:
    """Handed to the job body so it can report progress as it goes."""

    job: Job
    manager: JobManager

    async def progress(self, fraction: float, stage: str) -> None:
        self.job.progress = max(0.0, min(1.0, fraction))
        self.job.stage = stage
        log.info("job %s %s %.0f%%", self.job.id, stage, self.job.progress * 100)
        await self.manager._publish(self.job, "progress")


_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _manager
    if _manager is None:
        from app.config import get_settings

        settings = get_settings()
        _manager = JobManager(settings.job_concurrency, settings.job_ttl_seconds)
    return _manager
