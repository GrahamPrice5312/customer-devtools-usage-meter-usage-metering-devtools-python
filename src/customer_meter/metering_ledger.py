from collections import defaultdict
from enum import StrEnum
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field


class EventKind(StrEnum):
    BUILD = "build"
    RELEASE = "release"
    DIAGNOSTIC = "diagnostic"


class UsageEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    kind: EventKind
    units: int = Field(ge=1, le=1_000_000)


class MeterResult(BaseModel):
    customer_id: str
    event_id: str
    applied: bool
    total_units: int


class CustomerUsage(BaseModel):
    customer_id: str
    total_units: int
    by_kind: dict[EventKind, int]


class MeteringLedger:
    """Process-local ledger used to make the cutover decision visible."""

    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()
        self._totals: dict[str, dict[EventKind, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._lock = Lock()

    def record(self, customer_id: str, event: UsageEvent) -> MeterResult:
        identity = (customer_id, event.event_id)
        with self._lock:
            if identity in self._seen:
                return MeterResult(
                    customer_id=customer_id,
                    event_id=event.event_id,
                    applied=False,
                    total_units=sum(self._totals[customer_id].values()),
                )
            self._seen.add(identity)
            self._totals[customer_id][event.kind] += event.units
            return MeterResult(
                customer_id=customer_id,
                event_id=event.event_id,
                applied=True,
                total_units=sum(self._totals[customer_id].values()),
            )

    def usage(self, customer_id: str) -> CustomerUsage:
        with self._lock:
            by_kind = dict(self._totals[customer_id])
            return CustomerUsage(
                customer_id=customer_id,
                total_units=sum(by_kind.values()),
                by_kind=by_kind,
            )
