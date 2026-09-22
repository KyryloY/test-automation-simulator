import math

import pytest

from virtual_test_bench.testplan import ValidationError, parse_plan


def valid_plan():
    return {"id": "p", "frequency_hz": 1, "power_setpoint_w": 1, "readings": 1, "limits": {"forward_power_w": {"lower": 0, "upper": 2}, "reflected_power_w": {"upper": 1}}, "guard_band_w": 0, "retries": 0}


@pytest.mark.parametrize("field,value", [("frequency_hz", 0), ("power_setpoint_w", -1), ("frequency_hz", math.nan)])
def test_plan_rejects_nonpositive_or_nonfinite_operating_values(field, value):
    plan = valid_plan(); plan[field] = value
    with pytest.raises(ValidationError):
        parse_plan(plan)
