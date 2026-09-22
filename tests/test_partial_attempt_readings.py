from virtual_test_bench.runner import load_plan, run_plan


def test_interlock_timeout_retains_reading_captured_before_failure():
    result = run_plan(load_plan("plans/nominal.json"), 1, "load_mismatch")
    reflected = next(
        item for item in result.measurements if item.quantity == "reflected_power"
    )
    assert reflected.attempt_records[0]["readings"] == [10.0]
    assert reflected.attempt_records[0]["error"] == "virtual interlock latched"
