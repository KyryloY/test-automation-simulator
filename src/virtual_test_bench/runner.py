import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .drivers import GeneratorDriver, PowerMeterDriver
from .errors import InstrumentTimeout, MalformedResponse
from .evaluation import (
    MeasurementResult,
    evaluate_measurement,
    inconclusive_measurement,
)
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
    generator_resource = bench.manager.open_resource("SIM::RFGEN::INSTR")
    meter_resource = bench.manager.open_resource("SIM::POWERMETER::INSTR")
    generator = GeneratorDriver(generator_resource)
    meter = PowerMeterDriver(meter_resource)
    results: list[MeasurementResult] = []
    output_enabled = False

    try:
        generator.configure(plan.frequency_hz, plan.power_setpoint_w)
        generator.enable_output()
        output_enabled = True

        for quantity, reader, limits in (
            ("forward_power", meter.measure_forward_power_w, plan.forward_power_w),
            (
                "reflected_power",
                meter.measure_reflected_power_w,
                plan.reflected_power_w,
            ),
        ):
            attempt_records: list[dict[str, object]] = []
            for attempt in range(1, plan.retries + 2):
                readings: list[float] = []
                try:
                    for _ in range(plan.readings):
                        readings.append(reader())
                    results.append(
                        evaluate_measurement(
                            quantity, "W", readings, limits, plan.guard_band_w
                        )
                    )
                    break
                except (InstrumentTimeout, MalformedResponse) as error:
                    attempt_records.append(
                        {
                            "attempt": attempt,
                            "readings": readings,
                            "error": str(error),
                        }
                    )
                    if attempt == plan.retries + 1:
                        results.append(
                            inconclusive_measurement(
                                quantity,
                                "W",
                                f"{error} after {attempt} attempts",
                                limits,
                                attempt,
                                tuple(attempt_records),
                            )
                        )
    finally:
        if output_enabled:
            generator.disable_output()
        generator_resource.close()
        meter_resource.close()

    return RunResult(
        plan,
        seed,
        profile,
        tuple(results),
        datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        bench.simulation_config,
    )
