# Design: virtual RF-generator measurement bench (version 1)

**Status:** approved for implementation by the repository owner on 2026-09-22.  
**Scope:** local, hardware-free learning project. It is not a model of a
TRUMPF product, a calibrated bench, or a safe RF system.

## 1. Selected scenario

Version 1 simulates a programmable RF generator connected to a virtual load
and observed through a virtual power meter. A data-driven test plan commands a
frequency and forward-power setpoint, waits for a defined warm-up condition,
takes repeated readings, evaluates synthetic acceptance limits, and creates a
traceable report.

This option was selected because it demonstrates SCPI-like instrument control,
VISA-shaped addressing, test-plan execution, diagnostics, and RF-oriented
terms relevant to the target role. The model remains deliberately narrow:
forward/reflected power are scalar simulated quantities, not physical RF
measurements.

## 2. Assumptions and simplifications

- One in-process bench; no hardware, network socket, VISA runtime, discovery,
  concurrency, or real transport.
- Commands form a documented SCPI-like subset only. It is not a SCPI, IEEE
  488.2, VISA, or PyVISA implementation.
- The generator model stores requested frequency and power, output state, and
  an interlock state. It produces a deterministic warm-up/drift factor.
- The load exposes a configurable mismatch coefficient. The model derives
  non-negative reflected power from it; it is not an impedance/VSWR model.
- The power meter applies configurable systematic offset and seedable random
  noise to readings. Its values have no calibration or uncertainty claim.
- A reflected-power threshold can latch the virtual generator interlock. This
  is a software test condition, never a real safety mechanism.
- Limits and optional guard bands are synthetic test-plan acceptance rules.
  `PASS`/`FAIL` are not conformity decisions.

## 3. Components and data flow

```text
test-plan YAML/JSON
        |
        v
CLI -> runner -> typed instrument drivers -> SIM:: resources -> generator/load/meter models
        |              |                           |
        |              +-- SCPI-like command/query -+-- raw responses, error queue, faults
        v
evaluation -> structured run result -> JSON report + Markdown summary
```

### Boundaries

- `instruments/transport.py`: `VisaLikeResource` protocol, simulated resource
  manager, timeouts, unsupported-command errors, malformed-reply fault.
- `instruments/generator.py` and `instruments/power_meter.py`: typed driver
  methods; they are the only layer that formats/parses commands.
- `dut/load.py`: load mismatch and DUT fault profiles; it knows no test limits.
- `simulation/`: seeded noise, offset, warm-up and virtual-clock state.
- `testplan/`: validated schema/data objects and shipped example plan.
- `runner/`: lifecycle, retries, raw-attempt capture and teardown.
- `evaluation/`: acceptance/guard-band decisions and diagnostic messages.
- `reporting/`: JSON persistence and Markdown rendering from the run result.
- `cli.py`: run a plan, choose a deterministic fault profile, and choose an
  output directory.

## 4. Command subset

Each resource has `write(command)`, `query(command)` and `close()`. The local
manager exposes `SIM::RFGEN::INSTR` and `SIM::POWERMETER::INSTR`.

| Command | Resource | Result |
| --- | --- | --- |
| `*IDN?` | either | deterministic comma-separated identity |
| `*CLS` | either | clears local error/status state |
| `SOUR:FREQ <value> HZ` | generator | sets frequency |
| `SOUR:POW <value> W` | generator | sets forward-power setpoint |
| `OUTP ON|OFF` | generator | enables/disables simulated output |
| `MEAS:POW?` | power meter | one forward-power reading in W |
| `MEAS:REFL?` | power meter | one reflected-power reading in W |
| `SYST:ERR?` | either | pops oldest error, then `0,"No error"` |

Unsupported or malformed commands enqueue an SCPI-inspired error such as
`-113,"Undefined header"`. The runner translates a resource timeout or a
malformed numeric response into an I/O diagnostic, not a measurement failure.

## 5. Test-plan schema and evaluation

A version-1 plan is a JSON object with:

```yaml
id: rf-output-power-at-nominal-load
frequency_hz: 13560000
power_setpoint_w: 100
readings: 5
limits:
  forward_power_w: {lower: 95, upper: 105}
  reflected_power_w: {upper: 5}
guard_band_w: 0
retries: 1
```

The runner takes all requested readings after configuration. For each quantity,
the evaluator records raw readings and arithmetic mean. A valid mean inside
the acceptance interval is `PASS`; a valid mean outside it is `FAIL` and names
the limit. An optional positive guard band tightens the effective interval; a
measurement that is inside the original limit but outside the tightened band is
reported as `INCONCLUSIVE` with `guard-band boundary` reason. A timeout,
unsupported/malformed response, or exhausted retry produces `INCONCLUSIVE`.

The report contains the unmodified plan, simulation configuration (including
seed), raw readings/attempts, observed summaries, effective limits, verdicts,
timestamps, and diagnostics.

## 6. Faults and handling

| Fault profile | Deterministic effect | Expected verdict |
| --- | --- | --- |
| `nominal` | noise around an in-limit result | `PASS` |
| `power_low` | generator delivery factor lowers forward power | `FAIL` |
| `load_mismatch` | reflected power crosses its upper limit/interlock threshold | `FAIL` or `INCONCLUSIVE` if interlock prevents measurement, documented by the plan |
| `meter_timeout` | configured measurement query raises timeout | `INCONCLUSIVE` after retry exhaustion |
| `malformed_reply` | configured query returns non-numeric response | `INCONCLUSIVE` |
| `unsupported_command` | resource enqueues `-113` | driver/transport unit test confirms error queue behaviour |

Initial implementation will use `power_low` for the documented fail demo and
`meter_timeout` for the documented inconclusive demo. This keeps verdict
semantics unambiguous.

## 7. Test strategy and acceptance criteria

Unit tests cover command parsing/error queue, deterministic noise for a fixed
seed, warm-up/load calculations, individual limit/guard-band decisions, and
report rendering. Integration tests run the complete nominal plan, an
out-of-tolerance `power_low` plan, a timeout profile, and two identical seeded
runs that must retain the same raw readings.

Version 1 is accepted when a fresh clone can:

1. install the documented Python development dependencies;
2. run one CLI command that yields a `PASS` report;
3. run a documented fault command yielding a meaningful `FAIL`, and another
   yielding `INCONCLUSIVE`;
4. run `pytest` successfully; and
5. understand the hardware-free limitations from the README and reports.

## 8. Phased implementation plan

1. Establish packaging, test configuration and typed domain/result models.
2. Build the smallest vertical slice: generator + power meter resources, a
   fixed nominal plan, evaluation, JSON/Markdown output, one CLI command, and
   an end-to-end passing test.
3. Add repeat readings, seedable noise/offset/warm-up and traceable metadata.
4. Add fault profiles, retries, `FAIL`/`INCONCLUSIVE` distinctions and tests.
5. Finish README, protocol reference, example plans and verification.

No physical-hardware adapter is part of this release. A future extension may
wrap a real PyVISA resource behind the typed driver boundary without changing
the runner/evaluation/reporting contracts.
