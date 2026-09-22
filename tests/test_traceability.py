import json

from virtual_test_bench.reporting import write_reports
from virtual_test_bench.runner import load_plan, run_plan


def test_report_retains_timestamp_and_simulation_configuration(tmp_path):
    result = run_plan(load_plan("plans/nominal.json"), 42, "nominal")
    json_path, _ = write_reports(result, tmp_path)
    payload = json.loads(json_path.read_text())
    assert payload["started_at"].endswith("Z")
    assert payload["simulation"]["seed"] == 42
    assert payload["simulation"]["profile"] == "nominal"
