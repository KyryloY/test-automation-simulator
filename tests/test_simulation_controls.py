from virtual_test_bench.drivers import GeneratorDriver, PowerMeterDriver
from virtual_test_bench.simulation import SimulatedBench


def configured_meter(profile: str):
    bench = SimulatedBench(seed=1, profile=profile)
    generator = GeneratorDriver(bench.manager.open_resource("SIM::RFGEN::INSTR"))
    generator.configure(13_560_000, 100)
    generator.enable_output()
    return bench, PowerMeterDriver(
        bench.manager.open_resource("SIM::POWERMETER::INSTR")
    )


def test_offset_profile_shifts_forward_power_reading():
    _, nominal = configured_meter("nominal")
    _, offset = configured_meter("meter_offset")
    assert offset.measure_forward_power_w() - nominal.measure_forward_power_w() == 2.0


def test_warmup_profile_increases_between_readings():
    _, meter = configured_meter("warmup")
    assert meter.measure_forward_power_w() < meter.measure_forward_power_w()


def test_mismatch_profile_latches_virtual_interlock():
    bench, meter = configured_meter("load_mismatch")
    assert meter.measure_reflected_power_w() > 5
    assert bench.output_on is False
