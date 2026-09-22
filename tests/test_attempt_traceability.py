from virtual_test_bench.runner import load_plan, run_plan


def test_timeout_preserves_one_record_per_retry_attempt():
    result = run_plan(load_plan("plans/nominal.json"), 1, "meter_timeout")
    forward = next(item for item in result.measurements if item.quantity == "forward_power")
    assert len(forward.attempt_records) == 2
    assert [record["error"] for record in forward.attempt_records] == ["simulated meter timeout", "simulated meter timeout"]
