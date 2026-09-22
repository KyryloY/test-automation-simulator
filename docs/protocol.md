# SCPI-like protocol reference

This local command subset is an educational analogue, not SCPI or VISA compliance.

| Command | Resource | Response/effect |
| --- | --- | --- |
| `*IDN?` | generator or meter | virtual identity string |
| `*CLS` | generator or meter | clear local error queue |
| `SOUR:FREQ <Hz>` | generator | set frequency |
| `SOUR:POW <W>` | generator | set power setpoint |
| `OUTP ON|OFF` | generator | set output state |
| `MEAS:POW?` | meter | synthetic forward power in W |
| `MEAS:REFL?` | meter | synthetic reflected power in W |
| `SYST:ERR?` | either | FIFO error entry or `0,"No error"` |

Fault profiles are deterministic for a given seed: `nominal`, `power_low`, `meter_timeout`, and `malformed_reply`.
