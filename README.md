# Virtual Test Bench: Python, SCPI-like Instrument Control and Automated Measurement Evaluation

A hardware-free learning project that simulates an instrument-controlled RF measurement bench, executes Python test plans, evaluates synthetic tolerances, and produces traceable reports.

It demonstrates software architecture for test automation; it does **not** operate physical instruments, implement VISA/SCPI, measure RF power, provide calibration, or make safety/compliance claims.

## Run

Install [uv](https://docs.astral.sh/uv/) and run:

```powershell
uv run --with pytest python -m virtual_test_bench.cli --plan plans/nominal.json --profile nominal --seed 42 --output reports/nominal
```

The command produces `result.json` with the plan, seed, raw readings and verdicts, plus `summary.md` for a quick review.

Try deterministic fault profiles:

```powershell
uv run --with pytest python -m virtual_test_bench.cli --plan plans/nominal.json --profile power_low --seed 42 --output reports/power-low
uv run --with pytest python -m virtual_test_bench.cli --plan plans/nominal.json --profile meter_timeout --seed 42 --output reports/meter-timeout
uv run --with pytest pytest -q
```

`power_low` yields a valid out-of-tolerance `FAIL`; `meter_timeout` yields `INCONCLUSIVE`, deliberately distinct from an out-of-spec measurement.

## Scope

The virtual generator accepts a documented SCPI-like subset and the virtual power meter reports synthetic forward/reflected-power values. The test runner configures the resources, takes repeated readings, preserves raw data, applies limits/guard bands, and renders reports. See [domain research](docs/domain-research.md), [design](docs/design.md), and [protocol reference](docs/protocol.md).
