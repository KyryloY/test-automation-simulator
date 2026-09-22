from dataclasses import dataclass
from statistics import fmean

from .models import Limits, Verdict


@dataclass(frozen=True)
class MeasurementResult:
    quantity: str
    unit: str
    readings: tuple[float, ...]
    mean: float | None
    verdict: Verdict
    reason: str
    effective_limits: Limits
    attempts: int = 1
    attempt_records: tuple[dict[str, object], ...] = ()


def inconclusive_measurement(quantity: str, unit: str, reason: str, limits: Limits, attempts: int = 1, attempt_records: tuple[dict[str, object], ...] = ()) -> MeasurementResult:
    return MeasurementResult(quantity, unit, (), None, Verdict.INCONCLUSIVE, reason, limits, attempts, attempt_records)


def evaluate_measurement(quantity: str, unit: str, readings: list[float], limits: Limits, guard_band_w: float) -> MeasurementResult:
    mean = fmean(readings)
    if limits.lower is not None and mean < limits.lower:
        return MeasurementResult(quantity, unit, tuple(readings), mean, Verdict.FAIL, "below lower limit", limits)
    if limits.upper is not None and mean > limits.upper:
        return MeasurementResult(quantity, unit, tuple(readings), mean, Verdict.FAIL, "above upper limit", limits)
    effective = Limits(None if limits.lower is None else limits.lower + guard_band_w,
                       None if limits.upper is None else limits.upper - guard_band_w)
    if (effective.lower is not None and mean < effective.lower) or (effective.upper is not None and mean > effective.upper):
        return MeasurementResult(quantity, unit, tuple(readings), mean, Verdict.INCONCLUSIVE, "guard-band boundary", effective)
    return MeasurementResult(quantity, unit, tuple(readings), mean, Verdict.PASS, "within limits", effective)
