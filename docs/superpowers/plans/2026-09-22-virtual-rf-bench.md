# Virtual RF Bench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally runnable, hardware-free RF-generator bench simulator that evaluates a data-driven plan and reports traceable `PASS`, `FAIL`, or `INCONCLUSIVE` results.

**Architecture:** The CLI loads a JSON plan and a named deterministic fault profile, then calls a runner. The runner configures typed drivers over in-process SCPI-like resources, evaluates measurements with pure functions, and persists one structured result as JSON and Markdown.

**Tech Stack:** Python 3.12+, standard library, `pytest`, `pyproject.toml` with setuptools.

**Spec:** `docs/design.md`

## Global Constraints

- Use explicit scalar units (`Hz`, `W`, `%`) in public field names and report labels.
- Model only local simulated resources (`SIM::...`); do not install or claim VISA/PyVISA/SCPI compliance.
- Preserve raw readings, plan, seed, profile and diagnostics in every report.
- A valid out-of-limit measurement is `FAIL`; timeout/malformed transport output after retries is `INCONCLUSIVE`.
- Use seedable synthetic noise and fault profiles; no calibration, uncertainty or safety claim.

## Review Focus

- Invalid plan values (zero readings, reversed limits) must produce a readable validation error; Task 1 tests this.
- An unsupported SCPI-like command must remain observable through `SYST:ERR?`; Task 2 tests FIFO dequeue and empty queue.
- A numeric reply with unsupported units or non-numeric text must never be evaluated as `FAIL`; Task 3 tests parser failure maps to `INCONCLUSIVE`.
- A result inside product limits but outside a nonzero guard band must be `INCONCLUSIVE`; Task 4 tests the tightened boundary.
- Two runs with the same plan/profile/seed must retain equal raw readings; Task 5 tests reproducibility end to end.

---

### Task 1: Package, domain types and plan validation

**Files:**
- Create: `pyproject.toml`, `src/virtual_test_bench/__init__.py`, `src/virtual_test_bench/models.py`, `src/virtual_test_bench/testplan.py`, `tests/test_testplan.py`, `plans/nominal.json`

**Interfaces:**
- Produces `TestPlan.from_mapping(mapping: dict[str, object]) -> TestPlan`.
- Produces immutable `Limits(lower: float | None, upper: float | None)`, `TestPlan`, `Verdict` and `ValidationError`.

- [ ] **Step 1: Write failing validation tests**

```python
def test_plan_rejects_zero_readings() -> None:
    with pytest.raises(ValidationError, match="readings"):
        TestPlan.from_mapping({**valid_mapping(), "readings": 0})

def test_plan_rejects_reversed_limits() -> None:
    invalid = valid_mapping()
    invalid["limits"]["forward_power_w"] = {"lower": 105, "upper": 95}
    with pytest.raises(ValidationError, match="lower"):
        TestPlan.from_mapping(invalid)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_testplan.py -v`  
Expected: FAIL because package/types do not exist.

- [ ] **Step 3: Implement the minimum validated models and nominal plan**

```python
class Verdict(StrEnum):
    PASS = "PASS"; FAIL = "FAIL"; INCONCLUSIVE = "INCONCLUSIVE"

@dataclass(frozen=True)
class Limits:
    lower: float | None = None
    upper: float | None = None

@dataclass(frozen=True)
class TestPlan:
    id: str; frequency_hz: float; power_setpoint_w: float; readings: int
    forward_power_w: Limits; reflected_power_w: Limits; guard_band_w: float; retries: int
```

`from_mapping` must require the documented fields, reject nonpositive readings,
negative retries/guard band, and `lower > upper`, and create `plans/nominal.json`
with 13.56 MHz, 100 W, five readings, 95–105 W forward and ≤5 W reflected limits.

- [ ] **Step 4: Run validation tests**

Run: `pytest tests/test_testplan.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add pyproject.toml src tests plans && git commit -m "feat: add validated test plans"`

### Task 2: Deterministic simulator, resources and typed drivers

**Files:**
- Create: `src/virtual_test_bench/errors.py`, `src/virtual_test_bench/simulation.py`, `src/virtual_test_bench/transport.py`, `src/virtual_test_bench/drivers.py`, `tests/test_transport.py`, `tests/test_simulation.py`

**Interfaces:**
- Consumes `TestPlan`.
- Produces `SimulatedBench(seed: int, profile: str)`, `SimulatedResourceManager.open_resource(name)`, `GeneratorDriver`, `PowerMeterDriver`, `InstrumentTimeout`, and `MalformedResponse`.

- [ ] **Step 1: Write failing resource/seed tests**

```python
def test_unknown_command_is_returned_by_error_queue() -> None:
    resource = SimulatedBench(seed=7).manager.open_resource("SIM::RFGEN::INSTR")
    resource.write("BAD:COMMAND")
    assert resource.query("SYST:ERR?") == '-113,"Undefined header"'
    assert resource.query("SYST:ERR?") == '0,"No error"'

def test_same_seed_produces_same_reading() -> None:
    assert measure_once(seed=11) == measure_once(seed=11)
```

- [ ] **Step 2: Run focused tests to verify failure**

Run: `pytest tests/test_transport.py tests/test_simulation.py -v`  
Expected: FAIL because simulator does not exist.

- [ ] **Step 3: Implement local command surface and profiles**

```python
class SimulatedResource(Protocol):
    def write(self, command: str) -> None: ...
    def query(self, command: str) -> str: ...
    def close(self) -> None: ...

class PowerMeterDriver:
    def measure_forward_power_w(self) -> float: ...
    def measure_reflected_power_w(self) -> float: ...
```

Support `*IDN?`, `*CLS`, `SOUR:FREQ`, `SOUR:POW`, `OUTP`, `MEAS:POW?`,
`MEAS:REFL?`, and `SYST:ERR?`. Use `random.Random(seed)`. Profiles: `nominal`,
`power_low` (delivery factor 0.90), `meter_timeout` (raise only on meter query),
and `malformed_reply` (return `not-a-number` only on meter query). Drivers must
raise `MalformedResponse` when `float(reply)` fails.

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/test_transport.py tests/test_simulation.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src tests && git commit -m "feat: simulate instrument resources"`

### Task 3: Evaluation rules and structured result

**Files:**
- Create: `src/virtual_test_bench/evaluation.py`, `tests/test_evaluation.py`

**Interfaces:**
- Consumes `Limits`, `Verdict`, successful float readings and transport exceptions.
- Produces `MeasurementResult(quantity: str, unit: str, readings: tuple[float, ...], mean: float | None, verdict: Verdict, reason: str, effective_limits: Limits)` and `evaluate_measurement(...)`.

- [ ] **Step 1: Write failing evaluator tests**

```python
def test_out_of_limit_mean_is_fail() -> None:
    result = evaluate_measurement("forward_power", "W", [89.0, 91.0], Limits(95, 105), 0)
    assert result.verdict is Verdict.FAIL
    assert "lower limit" in result.reason

def test_guard_band_boundary_is_inconclusive() -> None:
    result = evaluate_measurement("forward_power", "W", [95.5], Limits(95, 105), 1)
    assert result.verdict is Verdict.INCONCLUSIVE

def test_transport_failure_is_inconclusive() -> None:
    result = inconclusive_measurement("forward_power", "W", "timeout after 2 attempts", Limits(95, 105))
    assert result.verdict is Verdict.INCONCLUSIVE
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_evaluation.py -v`  
Expected: FAIL because evaluator does not exist.

- [ ] **Step 3: Implement pure evaluation**

Compute `statistics.fmean(readings)`. Tighten a finite lower by adding the guard
band and a finite upper by subtracting it. Return `FAIL` outside original
limits, `INCONCLUSIVE` within original but outside effective limits, otherwise
`PASS`. Preserve inputs unchanged in the result.

- [ ] **Step 4: Run evaluator tests**

Run: `pytest tests/test_evaluation.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/virtual_test_bench/evaluation.py tests/test_evaluation.py && git commit -m "feat: evaluate measurement limits"`

### Task 4: Runner, retries and reports

**Files:**
- Create: `src/virtual_test_bench/runner.py`, `src/virtual_test_bench/reporting.py`, `tests/test_runner.py`, `tests/test_reporting.py`

**Interfaces:**
- Consumes `TestPlan`, `SimulatedBench`, drivers, and evaluator.
- Produces `RunResult(plan: TestPlan, seed: int, profile: str, measurements: tuple[MeasurementResult, ...], started_at: str)` and `run_plan(plan, seed, profile) -> RunResult`; `write_reports(result, output_dir) -> tuple[Path, Path]`.

- [ ] **Step 1: Write failing runner tests**

```python
def test_nominal_plan_passes() -> None:
    result = run_plan(load_plan(NOMINAL_PLAN), seed=42, profile="nominal")
    assert {item.verdict for item in result.measurements} == {Verdict.PASS}

def test_low_power_is_fail() -> None:
    result = run_plan(load_plan(NOMINAL_PLAN), seed=42, profile="power_low")
    assert forward(result).verdict is Verdict.FAIL

def test_timeout_is_inconclusive_after_retry() -> None:
    result = run_plan(load_plan(NOMINAL_PLAN), seed=42, profile="meter_timeout")
    assert forward(result).verdict is Verdict.INCONCLUSIVE
    assert "2 attempts" in forward(result).reason
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_runner.py tests/test_reporting.py -v`  
Expected: FAIL because runner/report writer do not exist.

- [ ] **Step 3: Implement lifecycle and persistence**

Runner must issue generator frequency, power and output setup commands; request
the configured count of forward and reflected readings; retry a failed whole
quantity up to `retries + 1` attempts; always send `OUTP OFF` and close both
resources in `finally`. JSON output must use only JSON primitives and include
plan, profile, seed, every raw reading, mean, limits, verdict and reason.
Markdown must include one table with quantity, observed mean, limits, verdict,
and reason, plus the simulation metadata.

- [ ] **Step 4: Run runner/report tests**

Run: `pytest tests/test_runner.py tests/test_reporting.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src tests && git commit -m "feat: run plans and write reports"`

### Task 5: CLI, documentation and end-to-end verification

**Files:**
- Create: `src/virtual_test_bench/cli.py`, `README.md`, `docs/protocol.md`, `tests/test_cli.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces console command `virtual-test-bench --plan plans/nominal.json --profile nominal --seed 42 --output reports` with exit code 0 for all completed simulated runs, while the rendered verdict communicates pass/fail/inconclusive.

- [ ] **Step 1: Write failing CLI/reproducibility tests**

```python
def test_cli_creates_json_and_markdown_reports(tmp_path: Path) -> None:
    code = main(["--plan", str(NOMINAL_PLAN), "--profile", "nominal", "--seed", "42", "--output", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "result.json").exists()
    assert (tmp_path / "summary.md").exists()

def test_same_seed_keeps_raw_readings_equal() -> None:
    first = run_plan(load_plan(NOMINAL_PLAN), 99, "nominal")
    second = run_plan(load_plan(NOMINAL_PLAN), 99, "nominal")
    assert first.measurements[0].readings == second.measurements[0].readings
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_cli.py -v`  
Expected: FAIL because CLI does not exist.

- [ ] **Step 3: Implement command and reader documentation**

Use `argparse` and provide the console script in `pyproject.toml`. README must
state the hardware-free learning boundary, setup steps, nominal invocation,
`power_low` fail invocation, `meter_timeout` inconclusive invocation, `pytest`
command, report contents, and limitations. `docs/protocol.md` must list every
supported command, response and fault profile.

- [ ] **Step 4: Run full suite and manual smoke commands**

Run: `pytest -q`  
Expected: PASS.

Run: `python -m virtual_test_bench.cli --plan plans/nominal.json --profile nominal --seed 42 --output reports/nominal`  
Expected: JSON and Markdown files with `PASS`.

Run: `python -m virtual_test_bench.cli --plan plans/nominal.json --profile power_low --seed 42 --output reports/power_low`  
Expected: report with forward-power `FAIL`.

- [ ] **Step 5: Commit**

Run: `git add pyproject.toml src README.md docs/protocol.md tests && git commit -m "feat: add runnable virtual test bench"`
