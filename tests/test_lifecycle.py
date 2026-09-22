from virtual_test_bench.runner import load_plan, run_plan
from virtual_test_bench.simulation import SimulatedBench


def test_run_closes_generator_and_meter_resources(monkeypatch):
    bench = SimulatedBench(1)
    monkeypatch.setattr("virtual_test_bench.runner.SimulatedBench", lambda seed, profile: bench)
    run_plan(load_plan("plans/nominal.json"), 1, "nominal")
    assert all(resource.closed for resource in bench.resources)
