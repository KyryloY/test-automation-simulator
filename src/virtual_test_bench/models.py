from dataclasses import dataclass
from enum import StrEnum


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class Limits:
    lower: float | None = None
    upper: float | None = None


@dataclass(frozen=True)
class TestPlan:
    id: str
    frequency_hz: float
    power_setpoint_w: float
    readings: int
    forward_power_w: Limits
    reflected_power_w: Limits
    guard_band_w: float
    retries: int

    @classmethod
    def from_mapping(cls, mapping: dict[str, object]) -> "TestPlan":
        from .testplan import parse_plan
        return parse_plan(mapping)
