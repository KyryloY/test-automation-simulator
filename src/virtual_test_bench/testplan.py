import math
from typing import Any

from .models import Limits, TestPlan


class ValidationError(ValueError):
    pass


def _number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValidationError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{name} must be numeric") from error
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValidationError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _limits(value: Any, name: str) -> Limits:
    if not isinstance(value, dict):
        raise ValidationError(f"limits.{name} must be an object")
    lower = _number(value["lower"], f"limits.{name}.lower") if value.get("lower") is not None else None
    upper = _number(value["upper"], f"limits.{name}.upper") if value.get("upper") is not None else None
    if lower is not None and upper is not None and lower > upper:
        raise ValidationError(f"limits.{name}.lower must not exceed upper")
    return Limits(lower, upper)


def parse_plan(mapping: dict[str, object]) -> TestPlan:
    try:
        readings, retries = int(mapping["readings"]), int(mapping["retries"])
        guard_band_w = _number(mapping["guard_band_w"], "guard_band_w")
        limits = mapping["limits"]
        if not isinstance(limits, dict): raise ValidationError("limits must be an object")
        if readings <= 0 or isinstance(mapping["readings"], bool): raise ValidationError("readings must be positive")
        if retries < 0 or isinstance(mapping["retries"], bool) or guard_band_w < 0: raise ValidationError("retries and guard_band_w must be non-negative")
        return TestPlan(str(mapping["id"]), _number(mapping["frequency_hz"], "frequency_hz", positive=True), _number(mapping["power_setpoint_w"], "power_setpoint_w", positive=True), readings, _limits(limits.get("forward_power_w"), "forward_power_w"), _limits(limits.get("reflected_power_w"), "reflected_power_w"), guard_band_w, retries)
    except KeyError as error:
        raise ValidationError(f"missing required field: {error.args[0]}") from error