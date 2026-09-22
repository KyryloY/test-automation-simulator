# Domain research: virtual instrument-controlled measurement bench

**Status:** research note for design review (hardware-free learning project)  
**Research date:** 2026-09-22

## Purpose and boundary

This note frames a small, credible software simulation for a test-automation
portfolio project. It models selected behaviours of programmable instruments
and a DUT; it does **not** model a real TRUMPF product, a calibrated
measurement system, RF safety behaviour, or a physical transport.

The useful learning target is the software workflow: a test plan configures
instruments, obtains readings, distinguishes invalid communication from a
genuine out-of-limit result, and produces a traceable verdict. Any numerical
values later used in the simulation are synthetic engineering assumptions, not
measurements or device specifications.

## 1. SCPI in the proposed simulator

SCPI (Standard Commands for Programmable Instruments) is a textual command
language used by many programmable instruments. A controller writes commands
to change or initiate an instrument state and sends a query (normally ending in
`?`) when it needs a response. For example, an instrument may return its
identity for `*IDN?`, while a source-specific command may set frequency or
output power. The exact command tree remains vendor and instrument specific.

The simulator should implement only a small documented, SCPI-like subset:

```text
*IDN?                 -> VIRTUAL,RF-GENERATOR-1,VG001,0.1
*CLS                  -> clears simulator status/error queue
SOUR:FREQ 13.56MHZ    -> sets requested frequency
SOUR:POW 100W         -> sets requested forward-power setpoint
OUTP ON               -> enables simulated output
MEAS:POW?             -> returns one power-meter reading in W
MEAS:REFL?            -> returns one reflected-power reading in W
SYST:ERR?             -> returns and removes the oldest queued error
```

This is intentionally a protocol *analogue*, not a claim of compliance with
SCPI or IEEE 488.2. It includes behaviours that matter to a test runner:

- Command/query distinction and one textual response per supported query.
- An identity query, reset/clear-status behaviour, explicit settings and
  measurement queries.
- An ordered error queue. An unsupported command can enqueue `-113,"Undefined
  header"`; `SYST:ERR?` then returns the oldest error and eventually
  `0,"No error"`.
- Small status support if needed for the runner, such as `*ESR?` and `*STB?`.
  It will be documented as simplified because real register semantics and
  service requests vary in detail by device.

Keysight documentation illustrates the conventional patterns: `*IDN?` returns
manufacturer/model/serial/firmware fields; `*CLS` clears error and status
state; `*ESR?` reads and clears an event register; and `SYST:ERR?` reads queued
errors. Its SCPI guidance also shows the common negative `-100` to `-199`
command-error family. [Keysight instrument-programming guide](https://helpfiles.keysight.com/csg/m9384/Content/Prog/Programming%20the%20Instrument.htm)
[Keysight programming guide, error messages](https://www.keysight.com/us/en/assets/9018-40093/programming-guides/9018-40093.pdf)

## 2. VISA, PyVISA and resource addressing

VISA is an instrument-I/O API abstraction. It gives a client a consistent
session/resource model while an implementation deals with the physical or
network interface. A VISA resource name identifies both an interface and a
resource; examples in the ecosystem include `GPIB0::10::INSTR`,
`ASRL1::INSTR`, and `TCPIP0::host::inst0::INSTR`. The current IVI Foundation
VISA Library Specification is the primary reference for the API and resource
model. [IVI Foundation VISA Library Specification (2024)](https://www.ivifoundation.org/downloads/VISA/vpp43_2024-01-04.pdf)

PyVISA is Python's frontend over a VISA backend. Its default `@ivi` backend
uses an installed IVI-VISA implementation (for example, one from NI, Keysight,
Rohde & Schwarz, or Tektronix); separately, `pyvisa-py` provides a pure-Python
backend for supported message-based resources. Thus application-level Python
can use a `ResourceManager`, open a resource, then call methods such as
`write()` and `query()` without encoding transport details in each test.
[PyVISA: backends](https://pyvisa.readthedocs.io/en/1.14.1/advanced/backends.html)
[PyVISA: backend configuration](https://pyvisa.readthedocs.io/en/1.14.1/introduction/configuring.html)
[PyVISA-py supported resources](https://pyvisa.readthedocs.io/projects/pyvisa-py/en/latest/)

### Local approach

For version 1, use a project-owned `VisaLikeResource` protocol with
`write(command)`, `query(command)`, `close()`, a resource name, and defined
timeout/parse exceptions. A `SimulatedResourceManager` maps deliberately
VISA-shaped local addresses such as `SIM::RFGEN::INSTR` and
`SIM::POWERMETER::INSTR` to simulated resources.

This has two advantages: no VISA runtime or hardware is needed, and the
runner is written against a recognisable, narrow I/O boundary. An optional
later adapter can wrap a real PyVISA resource behind the same application
protocol. The project will not falsely advertise this local adapter as a
PyVISA backend or as an implementation of VISA.

## 3. GPIB, serial and Ethernet: what is and is not simulated

These terms describe ways controllers and instruments communicate; SCPI and
VISA sit at different layers.

| Interface | Typical role | What version 1 models |
| --- | --- | --- |
| GPIB / IEEE 488 | Legacy/widely used shared instrument bus; VISA often exposes it as a `GPIB...::INSTR` resource. | Only a VISA-shaped address and the possibility of an I/O timeout. No bus arbitration, electrical signalling, or adapters. |
| Serial / RS-232 | Point-to-point byte stream, frequently used on older or simpler instruments. | A framing/timeout failure class only; no baud rate, parity, or physical serial port. |
| Ethernet / LAN | Network-connected instrument control, commonly TCP/IP and sometimes raw sockets. | An in-process resource, with deterministic connection/response timeout faults. No sockets, discovery, DNS, or security model. |

The abstraction helps explain how a test runner can remain largely unchanged
when a lab replaces a GPIB-connected instrument with a LAN one. It does not
claim interchangeability of real device drivers, timing, trigger lines, or
vendor setup.

## 4. Metrology concepts and their use here

The simulation should keep the terms separate:

| Term | Meaning in this project |
| --- | --- |
| Measurand | The quantity being evaluated, e.g. simulated forward output power at a specified frequency and load state. |
| Repeatability | Variation among repeated readings under the same simulated conditions. Represented by seedable random noise. |
| Systematic effect / offset | A consistent shift, e.g. a configurable power-meter offset. It is distinct from random variation. |
| Measurement error | Difference between a result and the (generally unknowable) true measurand. It is not interchangeable with uncertainty. |
| Measurement uncertainty | A quantified dispersion associated with a measurement result. The project records simple simulated contributors but does not calculate or assert accredited uncertainty. |
| Calibration and traceability | Calibration relates an instrument indication to reference values; traceability is an unbroken documented chain to references. Neither exists in this simulator. |
| Test limit / tolerance | Product or test-plan acceptance boundaries, e.g. setpoint ±5 %. They are specifications, not uncertainty intervals. |
| Guard band | A deliberately tightened acceptance boundary to manage decision risk near a limit. It can be demonstrated as a configurable test-plan rule, not justified as a real conformity decision. |

NIST stresses that error and uncertainty must not be confused: the true value
is generally unknown, while uncertainty can be evaluated. Its guidance also
distinguishes statistical (Type A) and other-information (Type B) contributors
and requires documentation when reporting a measurement result with
uncertainty. [NIST TN 1297, terminology](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-d1-terminology)
[NIST TN 1297, Type B evaluation](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-4-type-b-evaluation-standard-uncertainty)
[NIST TN 1297, reporting](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-7-reporting-uncertainty)

For the first release, the verdict is therefore a **test-plan acceptance
decision**, not a statement of calibration, measurement uncertainty, product
conformity, or safety. Raw readings, simulated seed/offset/noise settings, and
the exact limits will be persisted so a reader can reproduce the simulation.

## 5. Test-automation design patterns to carry into design

The following boundaries keep the simulation replaceable and tests
deterministic:

1. **Transport/resource** parses commands, records an error queue, and models
   I/O failure. It knows no acceptance limits.
2. **Instrument drivers** expose typed actions such as setting frequency or
   reading power, and translate between typed values and command strings.
3. **DUT/load model** owns the simplified physical behaviour: warm-up,
   mismatch/reflection, and faults. It must not decide a test verdict.
4. **Test plan** is data, containing nominal values, units, allowed limits,
   sampling count, retry policy, and guard-band policy.
5. **Runner** performs setup, measurement, teardown and failure handling,
   retaining every attempt.
6. **Evaluator** turns valid readings into `PASS` or `FAIL`; it turns a timeout,
   malformed reply, or exhausted retry policy into `INCONCLUSIVE` with a
   diagnostic reason.
7. **Reporter** persists raw data/configuration and renders a human-readable
   summary. It does not recalculate an undocumented verdict.

Seeded pseudo-random noise and injected faults belong in explicit configuration,
not monkeypatch-only tests. This makes a specific seed/fault profile replayable
in both integration tests and the documented CLI demonstration.

## 6. Modest RF/power domain orientation

The educational model can use an RF generator feeding a load, with a power
meter reporting forward and reflected power:

- **Frequency** is the configured operating frequency; it matters because a
  real source, load and measurement chain can be frequency-sensitive.
- **Forward power** is the simplified source-to-load power quantity used for
  the primary tolerance check.
- **Reflected power** is a simplified indicator of load mismatch. A high value
  can trigger the simulated interlock and makes a useful fault scenario.
- **Warm-up/drift** represents state-dependent readings after enabling output;
  it is a simple deterministic curve, not thermal or RF physics.
- **Interlock** is modelled as a software state that inhibits output after a
  configured condition. It is not a safety mechanism and must never be
  described as one.
- **Setpoint tolerance** is an acceptance band from the synthetic test plan,
  not a claim about a real generator's specification.

The proposed model will preserve basic conservation intuition by keeping the
reported reflected power non-negative and bounded relative to a configured
forward-power value. It will not model impedance transformations, VSWR,
harmonics, electromagnetic fields, thermal design, matching networks, or real
protection systems.

## 7. Explicit assumptions for design

- The target audience is a reviewer for a Python test-automation role, not an
  RF validation authority.
- One process executes one virtual bench locally; concurrency and shared-lab
  scheduling are out of scope.
- Measurements are scalar values in explicit units (`Hz`, `W`, `%`) and use a
  documented normalisation/conversion policy.
- Noise, offset, drift and faults are deliberately synthetic and reproducible
  from test-plan/simulation configuration.
- A malformed command/reply or communication timeout cannot become a product
  `FAIL`; it produces `INCONCLUSIVE` unless a documented retry succeeds.
- An in-limit measurement produces `PASS`; a valid out-of-limit measurement
  produces `FAIL` with the violated limit and observed summary.

## What we will not simulate

- A real VISA backend, PyVISA backend, physical GPIB/serial/Ethernet transport,
  instrument discovery, or vendor driver compatibility.
- Any complete SCPI/IEEE 488.2 implementation, all status registers, triggering
  semantics, binary blocks, or service requests.
- Accurate RF, microwave, electrical, thermal, or control-system physics.
- Calibration certificates, traceability chains, uncertainty budgets,
  regulatory compliance, safe operating limits, or safety interlocks.
- Actual TRUMPF Hüttinger devices, proprietary commands, product specifications,
  measurements, or test plans.

## Design consequences

The research supports a narrow virtual RF-generator bench as the leading
option: it demonstrates instrument-style command control, state/fault
handling, limits, reporting and the job's RF orientation without pretending to
model a laboratory. The next checkpoint is to compare this option explicitly
with a DC power bench and generic digital-I/O DUT, then obtain approval for a
small design before implementation.
