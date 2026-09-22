from virtual_test_bench.simulation import SimulatedBench


def test_unknown_command_is_returned_by_error_queue():
    resource = SimulatedBench(seed=7).manager.open_resource("SIM::RFGEN::INSTR")
    resource.write("BAD:COMMAND")
    assert resource.query("SYST:ERR?") == '-113,"Undefined header"'
    assert resource.query("SYST:ERR?") == '0,"No error"'
