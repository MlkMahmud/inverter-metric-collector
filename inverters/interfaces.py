from dataclasses import dataclass
from typing import Any, Dict, Protocol, runtime_checkable


@dataclass
class ModbusConfig:
    """Data container for Modbus serial connection parameters."""
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: float = 2.0
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    device_id: int = 1


@runtime_checkable
class Inverter(Protocol):
    """
    Structural contract for all Inverter implementations.
    Any class implementing these properties and methods fits this protocol.
    """
    config: ModbusConfig

    def __init__(self, config: ModbusConfig) -> None:
        ...

    def read_telemetry(self) -> Dict[str, Any]:
        """Polls the inverter over Modbus and returns structured data."""
        ...

