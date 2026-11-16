"""Startup tasks (model loading, warm-up) and the readiness state behind `/readyz`."""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal

from app.core.logging import get_logger
from app.core.metrics import READY

log = get_logger(__name__)

ComponentState = Literal["pending", "ready", "failed"]


@dataclass(frozen=True)
class StartupTask:
    """A named unit of startup work, e.g. "asr_model"."""

    name: str
    run: Callable[[], Awaitable[None]]


@dataclass
class Readiness:
    components: dict[str, ComponentState] = field(default_factory=dict)
    startup_complete: bool = False

    @property
    def ready(self) -> bool:
        return self.startup_complete and all(s == "ready" for s in self.components.values())


async def run_startup_tasks(tasks: Sequence[StartupTask], readiness: Readiness) -> None:
    """Run tasks in order. A failure is recorded and keeps the service not-ready."""
    for task in tasks:
        readiness.components[task.name] = "pending"
    for task in tasks:
        try:
            await task.run()
        except Exception:
            readiness.components[task.name] = "failed"
            log.exception("startup_task_failed", task=task.name)
        else:
            readiness.components[task.name] = "ready"
            log.info("startup_task_ready", task=task.name)
    readiness.startup_complete = True
    READY.set(1 if readiness.ready else 0)
    log.info("startup_complete", ready=readiness.ready)
