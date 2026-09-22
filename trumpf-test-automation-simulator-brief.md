# Project brief: virtual test bench for TRUMPF test automation

## How to use this document

Give this document to an AI assistant at the beginning of a **new, separate repository**. It is a project brief, not an implementation plan. The assistant must research the domain, propose an appropriately scoped simulation problem, and obtain approval for the design before writing production code.

The aim is a credible portfolio project that supports an application for a test-automation role. It must be technically honest: it demonstrates deliberate learning and Python engineering, **not** prior hands-on industrial laboratory experience.

## Vacancy that motivates the project

- Employer: TRUMPF Hüttinger, Stutensee, Germany
- Role: [Test Automation Engineer (w/m/d) Messplatz- & Testautomatisierung — R00042382](https://trumpf.wd3.myworkdayjobs.com/de-DE/TRUMPF_Graduates_and_Professionals/job/Stutensee/Test-Automation-Engineer--w-m-d--Messplatz----Testautomatisierung_R00042382?utm_source=kununu)
- Status when this brief was created: advertised about seven days earlier (22 September 2026); full-time; fixed term of two years.

TRUMPF Hüttinger develops DC, medium- and high-frequency, and solid-state microwave generators. The job description says the engineer will:

- develop, maintain, and extend Python-based automated test scripts and test frameworks;
- connect measurement instruments to test environments through VISA, GPIB, and Ethernet;
- conduct measurements and functional tests according to test plans and specifications;
- automatically evaluate and document results; and
- diagnose and improve test infrastructure with development and systems-architecture teams.

The stated technical foundations are applied Python and automated-test concepts; basic metrology (instruments, measurement error, calibration); serial, GPIB, and Ethernet-based protocols; and willingness to learn high-frequency and microwave technology. The posting does **not** demand a stated minimum number of years of laboratory experience.

## Candidate context and truthfulness boundary

The candidate is a Diplom-Ingenieur in Information and Measurement Systems (KPI, 2002; German-recognised degree at Master level). Relevant academic subjects included metrology and measurement technology, measurement transducers, analogue and digital instruments, electronics, electrical signals and circuits, digital signal processing, microprocessor systems, information-measurement systems, automatic control, reliability, and theory of experiment.

Professionally, the candidate has recent, substantial Python automation experience: a production automation platform with around 118 Python modules, integrations, data-quality checks, `pytest`, CI/CD, and documentation. He has **not** recently operated a physical measurement bench or used VISA/GPIB-connected instruments in production.

Therefore, the repository and its README must use precise language such as “virtual laboratory”, “simulated instrument”, “learning project”, and “hardware-free test bench”. Do not imply calibration authority, certification, safety approval, real RF measurements, or industrial instrument experience.

## Project outcome

Create a small but realistic **virtual measurement bench** that shows the full software workflow expected in the vacancy:

```text
test plan / specification
        ↓
Python test runner ── command protocol ── simulated instruments + simulated DUT
        ↓                                      ↓
limits, tolerances, retries               readings, noise, faults
        ↓
automatic verdict and traceable report
```

The system runs locally with no physical hardware. It should emulate the important *behaviour* of an instrument-controlled measurement setup rather than reproduce every feature of a real device.

## Mandatory first phase: research before design or coding

Start by producing a concise research note. Prefer primary documentation and clearly label assumptions. Investigate:

1. **SCPI:** what it is, command/query patterns, error queues, status responses, and why it is often used with programmable instruments.
2. **VISA and PyVISA:** the relationship between VISA resource addressing, backends, and Python control code; identify a credible way to use or mimic this interface locally.
3. **GPIB, serial, and Ethernet:** their differing roles in a test bench. The project need not implement all physical transports, but must explain what it simulates and why.
4. **Metrology basics:** repeatability, systematic error, random noise, uncertainty/error terminology, traceability, calibration, test limits, and guard bands. Do not present the project as a calibration system.
5. **Test automation patterns:** separation of instrument driver, DUT model, test-plan data, test execution, result evaluation, and report generation; deterministic tests for simulated faults.
6. **Domain orientation:** basic concepts needed to model a modest RF/microwave or power-electronics device without unsafe or exaggerated claims (for example frequency, output power, load mismatch/reflected power, warm-up, interlock, and setpoint tolerance).

Suggested starting references (verify them and add better primary sources where needed):

- [PyVISA documentation](https://pyvisa.readthedocs.io/)
- [IVI Foundation: VISA specifications and resources](https://www.ivifoundation.org/)
- [Keysight SCPI programming guide](https://www.keysight.com/us/en/lib/resources/training-materials/tutorials/learn-scpi-programming-867435.html)
- [NIST: uncertainty of measurement](https://www.nist.gov/pml/nist-technical-note-1297)

Deliverable of this phase: `docs/domain-research.md`, with sources, a glossary, explicit assumptions, and a short “what we will not simulate” section. Stop for design approval after presenting it.

## Select the simulation problem deliberately

After research, offer 2–3 options, score them for relevance, realism, implementation risk, testability, and portfolio clarity, then recommend one. Keep the first version narrow.

Candidate directions:

| Option | Virtual setup | Example measurements | Main trade-off |
|---|---|---|---|
| A | Programmable DC power supply + electronic load + voltmeter | voltage regulation, current limit, ripple/noise proxy, warm-up | easiest metrology story; less close to the RF/microwave context |
| B | RF/microwave generator + power meter + load/DUT | frequency and output-power tolerance, reflected-power threshold, interlock | closest to TRUMPF Hüttinger; requires carefully simplified domain model |
| C | Generic device-under-test with sensor and digital I/O | functional states, timing, limit checks, communication failures | versatile and testable; less distinctive |

Recommendation unless research shows a better educational choice: **Option B**, modelled as a deliberately simplified RF generator test bench. It should be clear that it is a software model, not an engineering model of a real generator or a safety-relevant RF system.

## Expected scope of the approved first release

The chosen design should include these capabilities, with exact interfaces chosen only after the research/design phase:

- A simulated VISA-like resource or adapter with SCPI-like commands and queries, including a documented error response.
- At least two instruments or components (for example a signal/generator model and a power-meter model) plus a simulated DUT/load.
- Deterministic simulation controls: seedable noise, configurable systematic offset, warm-up or drift, communication timeout, malformed/unsupported command, and at least one DUT fault.
- A data-driven test plan/specification with nominal values, tolerances, units, number of readings, and a clear verdict rule.
- Python test execution that performs setup, measurement, evaluation, teardown, and failure handling.
- Automated result evaluation with pass/fail/inconclusive states and diagnostic reasons; results must retain raw readings and configuration metadata.
- A readable report (for example JSON plus an HTML or Markdown summary) that links each verdict to its limit and observed values.
- Unit and integration tests using `pytest`, including normal operation, out-of-tolerance measurement, simulated instrument failure, and reproducibility of deterministic faults.
- Clear README instructions: setup, run a happy-path test, inject a fault, run tests, and understand the limitations.

## Non-goals for the first release

- No physical instruments, USB/GPIB adapters, oscilloscopes, RF hardware, or costly equipment.
- No claim of accurate physics, calibrated values, regulatory compliance, or safe operating conditions.
- No GUI unless it directly improves the explanation; a CLI and generated report are sufficient.
- No unnecessary microservices, cloud deployment, authentication, database server, or machine-learning component.
- No attempt to implement the full VISA or SCPI standard.

## Architecture and quality expectations

Keep the codebase modular. A future reader should be able to change the instrument simulation without rewriting result evaluation or test-plan definitions. Aim for boundaries similar to:

- `instruments/`: command transport abstraction and individual simulated instrument drivers;
- `dut/`: the simplified DUT/load behaviour;
- `testplan/`: schema and examples for limits and test steps;
- `runner/`: orchestration, retries, lifecycle, and error handling;
- `evaluation/`: units, tolerances, verdicts, and diagnostics;
- `reporting/`: persisted raw data and human-readable summary;
- `tests/`: unit and integration tests;
- `docs/`: research, design decisions, protocol reference, and limitations.

Use type hints, meaningful exceptions, structured logging where it helps diagnosis, and explicit units. Treat a timeout or corrupted response differently from a genuine out-of-spec measurement. The report must make this distinction visible.

## Required design checkpoint

Before implementation, write `docs/design.md` covering:

1. selected scenario and why it won;
2. model assumptions and all intentional simplifications;
3. component diagram and data flow;
4. command subset and examples;
5. test-plan schema and evaluation rules;
6. injected faults and expected handling;
7. test strategy and acceptance criteria;
8. phased implementation plan, with the smallest demonstrable vertical slice first.

Present this design for review and wait for approval before coding.

## Definition of done

The project is complete when a reviewer can clone it, run one documented command, observe a passing virtual test, inject at least one known fault, observe a meaningful failed/inconclusive result, and run an automated test suite. The README must make it obvious both how the project relates to the TRUMPF role and where the simulation ends.

## Suggested repository positioning

Suggested title: **Virtual Test Bench: Python, SCPI-like Instrument Control and Automated Measurement Evaluation**.

Suggested one-sentence description: “A hardware-free learning project that simulates an instrument-controlled measurement bench, executes Python test plans, evaluates tolerances, and produces traceable reports.”

