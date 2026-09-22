import json
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path

from .drivers import GeneratorDriver, PowerMeterDriver
from .errors import InstrumentTimeout, MalformedResponse
from .evaluation import MeasurementResult, evaluate_measurement, inconclusive_measurement
from .models import TestPlan
from .simulation import SimulatedBench


@dataclass(frozen=True)
class RunResult:
    plan: TestPlan
    seed: int
    profile: str
    measurements: tuple[MeasurementResult, ...]
    started_at: str
    simulation: dict[str, object]


def load_plan(path: str | Path) -> TestPlan:
    return TestPlan.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def run_plan(plan: TestPlan, seed: int, profile: str) -> RunResult:
    bench = SimulatedBench(seed, profile)
    generator = GeneratorDriver(bench.manager.open_resource("SIM::RFGEN::INSTR"))
    meter = PowerMeterDriver(bench.manager.open_resource("SIM::POWERMETER::INSTR"))
    generator.configure(plan.frequency_hz, plan.power_setpoint_w); generator.enable_output()
    results = []
    try:
        for quantity, reader, limits in (("forward_power", meter.measure_forward_power_w, plan.forward_power_w), ("reflected_power", meter.measure_reflected_power_w, plan.reflected_power_w)):
            for attempt in range(1, plan.retries + 2):
                try:
                    readings = [reader() for _ in range(plan.readings)]
                    results.append(evaluate_measurement(quantity, "W", readings, limits, plan.guard_band_w))
                    break
                except (InstrumentTimeout, MalformedResponse) as error:
                    if attempt == plan.retries + 1:
                        results.append(inconclusive_measurement(quantity, "W", f"{error} after {attempt} attempts", limits, attempt))
    finally:
        generator.disable_output()
        generator.resource.close()
        meter.resource.close()
    return RunResult(plan, seed, profile, tuple(results), datetime.now(UTC).isoformat().replace("+00:00", "Z"), {"seed": seed, "profile": profile, "noise_w": 0.2, "systematic_offset_w": 0.0, "load_mismatch_coefficient": 0.02})
