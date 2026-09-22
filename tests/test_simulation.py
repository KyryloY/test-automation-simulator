from virtual_test_bench.drivers import GeneratorDriver, PowerMeterDriver
from virtual_test_bench.simulation import SimulatedBench


def measure_once(seed: int) -> float:
    bench = SimulatedBench(seed=seed)
    generator = GeneratorDriver(bench.manager.open_resource("SIM::RFGEN::INSTR"))
    generator.configure(13_560_000, 100)
    generator.enable_output()
    return PowerMeterDriver(
        bench.manager.open_resource("SIM::POWERMETER::INSTR")
    ).measure_forward_power_w()


def test_same_seed_produces_same_reading():
    assert measure_once(seed=11) == measure_once(seed=11)
