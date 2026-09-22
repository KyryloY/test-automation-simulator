from virtual_test_bench.models import Verdict
from virtual_test_bench.runner import load_plan, run_plan


def test_timeout_records_each_configured_retry_attempt():
    result = run_plan(load_plan("plans/nominal.json"), 42, "meter_timeout")
    forward = next(item for item in result.measurements if item.quantity == "forward_power")
    assert forward.verdict is Verdict.INCONCLUSIVE
    assert forward.attempts == 2
