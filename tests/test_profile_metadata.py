from virtual_test_bench.runner import load_plan, run_plan


def test_offset_profile_reports_its_actual_offset():
    result = run_plan(load_plan("plans/nominal.json"), 1, "meter_offset")
    assert result.simulation["systematic_offset_w"] == 2.0


def test_mismatch_profile_reports_its_actual_coefficient():
    result = run_plan(load_plan("plans/nominal.json"), 1, "load_mismatch")
    assert result.simulation["load_mismatch_coefficient"] == 0.10
