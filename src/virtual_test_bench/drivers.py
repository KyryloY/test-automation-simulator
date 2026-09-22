from .errors import MalformedResponse


class GeneratorDriver:
    def __init__(self, resource) -> None: self.resource = resource
    def configure(self, frequency_hz: float, power_w: float) -> None:
        self.resource.write(f"SOUR:FREQ {frequency_hz}"); self.resource.write(f"SOUR:POW {power_w}")
    def enable_output(self) -> None: self.resource.write("OUTP ON")
    def disable_output(self) -> None: self.resource.write("OUTP OFF")


class PowerMeterDriver:
    def __init__(self, resource) -> None: self.resource = resource
    def _measure(self, command: str) -> float:
        try: return float(self.resource.query(command))
        except ValueError as error: raise MalformedResponse("non-numeric instrument reply") from error
    def measure_forward_power_w(self) -> float: return self._measure("MEAS:POW?")
    def measure_reflected_power_w(self) -> float: return self._measure("MEAS:REFL?")
