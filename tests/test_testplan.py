import pytest

from virtual_test_bench.testplan import TestPlan, ValidationError


def valid_mapping():
    return {"id": "nominal", "frequency_hz": 13_560_000, "power_setpoint_w": 100,
            "readings": 5, "limits": {"forward_power_w": {"lower": 95, "upper": 105}, "reflected_power_w": {"upper": 5}},
            "guard_band_w": 0, "retries": 1}


def test_plan_rejects_zero_readings():
    with pytest.raises(ValidationError, match="readings"):
        TestPlan.from_mapping({**valid_mapping(), "readings": 0})


def test_plan_rejects_reversed_limits():
    value = valid_mapping()
    value["limits"]["forward_power_w"] = {"lower": 105, "upper": 95}
    with pytest.raises(ValidationError, match="lower"):
        TestPlan.from_mapping(value)
