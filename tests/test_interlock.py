import pytest

from virtual_test_bench.drivers import GeneratorDriver, PowerMeterDriver
from virtual_test_bench.errors import InstrumentTimeout
from virtual_test_bench.simulation import SimulatedBench


def test_latched_interlock_blocks_subsequent_power_measurement():
    bench = SimulatedBench(1, "load_mismatch")
    generator = GeneratorDriver(bench.manager.open_resource("SIM::RFGEN::INSTR"))
    meter = PowerMeterDriver(bench.manager.open_resource("SIM::POWERMETER::INSTR"))
    generator.configure(13_560_000, 100); generator.enable_output()
    meter.measure_reflected_power_w()
    with pytest.raises(InstrumentTimeout, match="interlock"):
        meter.measure_forward_power_w()
