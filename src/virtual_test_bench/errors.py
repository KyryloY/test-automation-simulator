class InstrumentTimeout(TimeoutError):
    """A simulated response timeout."""


class MalformedResponse(ValueError):
    """A simulated instrument reply cannot be parsed."""
