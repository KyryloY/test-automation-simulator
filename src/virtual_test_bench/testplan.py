from typing import Any

from .models import Limits, TestPlan


class ValidationError(ValueError):
    pass


def _limits(value: Any, name: str) -> Limits:
    if not isinstance(value, dict):
        raise ValidationError(f"limits.{name} must be an object")
    lower, upper = value.get("lower"), value.get("upper")
    lower = float(lower) if lower is not None else None
    upper = float(upper) if upper is not None else None
    if lower is not None and upper is not None and lower > upper:
        raise ValidationError(f"limits.{name}.lower must not exceed upper")
    return Limits(lower, upper)


def parse_plan(mapping: dict[str, object]) -> TestPlan:
    try:
        readings = int(mapping["readings"])
        retries = int(mapping["retries"])
        guard_band_w = float(mapping["guard_band_w"])
        limits = mapping["limits"]
        if not isinstance(limits, dict):
            raise ValidationError("limits must be an object")
        if readings <= 0:
            raise ValidationError("readings must be positive")
        if retries < 0 or guard_band_w < 0:
            raise ValidationError("retries and guard_band_w must be non-negative")
        return TestPlan(str(mapping["id"]), float(mapping["frequency_hz"]),
                        float(mapping["power_setpoint_w"]), readings,
                        _limits(limits.get("forward_power_w"), "forward_power_w"),
                        _limits(limits.get("reflected_power_w"), "reflected_power_w"),
                        guard_band_w, retries)
    except KeyError as error:
        raise ValidationError(f"missing required field: {error.args[0]}") from error
    except (TypeError, ValueError) as error:
        if isinstance(error, ValidationError):
            raise
        raise ValidationError(str(error)) from error
