from pathlib import Path

from virtual_test_bench.models import Verdict
from virtual_test_bench.runner import load_plan, run_plan

PLAN = Path("plans/nominal.json")


def forward(result):
    return next(
        item for item in result.measurements if item.quantity == "forward_power"
    )


def test_nominal_plan_passes():
    assert {
        item.verdict for item in run_plan(load_plan(PLAN), 42, "nominal").measurements
    } == {Verdict.PASS}


def test_low_power_is_fail():
    assert forward(run_plan(load_plan(PLAN), 42, "power_low")).verdict is Verdict.FAIL


def test_timeout_is_inconclusive_after_retry():
    assert (
        forward(run_plan(load_plan(PLAN), 42, "meter_timeout")).verdict
        is Verdict.INCONCLUSIVE
    )
