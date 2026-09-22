from virtual_test_bench.evaluation import evaluate_measurement, inconclusive_measurement
from virtual_test_bench.models import Limits, Verdict


def test_out_of_limit_mean_is_fail():
    result = evaluate_measurement(
        "forward_power", "W", [89.0, 91.0], Limits(95, 105), 0
    )
    assert result.verdict is Verdict.FAIL
    assert "lower limit" in result.reason


def test_guard_band_boundary_is_inconclusive():
    result = evaluate_measurement("forward_power", "W", [95.5], Limits(95, 105), 1)
    assert result.verdict is Verdict.INCONCLUSIVE


def test_transport_failure_is_inconclusive():
    result = inconclusive_measurement(
        "forward_power", "W", "timeout after 2 attempts", Limits(95, 105)
    )
    assert result.verdict is Verdict.INCONCLUSIVE
