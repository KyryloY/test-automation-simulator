import random

from .errors import InstrumentTimeout


class _Resource:
    def __init__(self, bench: "SimulatedBench", name: str) -> None:
        self.bench, self.name, self.errors, self.closed = bench, name, [], False

    def write(self, command: str) -> None:
        parts = command.strip().split()
        head = parts[0].upper() if parts else ""
        if head == "*CLS": self.errors.clear()
        elif self.name.endswith("RFGEN::INSTR") and head == "SOUR:FREQ" and len(parts) >= 2: self.bench.frequency_hz = float(parts[1])
        elif self.name.endswith("RFGEN::INSTR") and head == "SOUR:POW" and len(parts) >= 2: self.bench.power_w = float(parts[1])
        elif self.name.endswith("RFGEN::INSTR") and head == "OUTP" and len(parts) == 2: self.bench.output_on = parts[1].upper() == "ON"
        else: self.errors.append('-113,"Undefined header"')

    def query(self, command: str) -> str:
        if command.upper() == "SYST:ERR?": return self.errors.pop(0) if self.errors else '0,"No error"'
        if command.upper() == "*IDN?": return "VIRTUAL,RF-GENERATOR-1,VG001,0.1" if self.name.endswith("RFGEN::INSTR") else "VIRTUAL,POWER-METER-1,PM001,0.1"
        if self.name.endswith("POWERMETER::INSTR") and command.upper() in {"MEAS:POW?", "MEAS:REFL?"}:
            if self.bench.profile == "meter_timeout": raise InstrumentTimeout("simulated meter timeout")
            if self.bench.profile == "malformed_reply": return "not-a-number"
            if command.upper() == "MEAS:REFL?":
                reflected = self.bench.power_w * (0.10 if self.bench.profile == "load_mismatch" else 0.02)
                if reflected > 5:
                    self.bench.output_on = False
                return f"{reflected:.6f}"
            factor = 0.90 if self.bench.profile == "power_low" else 1.0
            warmup = 0.80 + 0.10 * min(self.bench.reading_count, 2) if self.bench.profile == "warmup" else 1.0
            self.bench.reading_count += 1
            offset = 2.0 if self.bench.profile == "meter_offset" else 0.0
            return f"{self.bench.power_w * factor * warmup + offset + self.bench.random.uniform(-0.2, 0.2):.6f}"
        self.errors.append('-113,"Undefined header"'); return ""

    def close(self) -> None: self.closed = True


class _Manager:
    def __init__(self, bench: "SimulatedBench") -> None: self.bench = bench
    def open_resource(self, name: str) -> _Resource:
        resource = _Resource(self.bench, name)
        self.bench.resources.append(resource)
        return resource


class SimulatedBench:
    def __init__(self, seed: int, profile: str = "nominal") -> None:
        self.random, self.profile = random.Random(seed), profile
        self.frequency_hz, self.power_w, self.output_on, self.reading_count = 0.0, 0.0, False, 0
        self.resources = []
        self.manager = _Manager(self)
