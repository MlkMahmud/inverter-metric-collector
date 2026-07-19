from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, List, Optional, Protocol, Union, runtime_checkable


class InverterModel(StrEnum):
    """Finite list of supported hardware models."""
    IVEM12048II = "IVEM12048II"


@runtime_checkable
class Inverter(Protocol):
    """
    Structural contract for all Inverter implementations.
    Any class implementing these properties and methods fits this protocol.
    """
    config: ModbusConfig
    model: str

    def __init__(self, config: ModbusConfig, model: str) -> None:
        ...

    def read_telemetry(self) -> List[Metric]:
        """Polls the inverter over Modbus and returns structured data."""
        ...


@dataclass(frozen=True)
class Metric:
    key: str
    value: Union[int, float, str]
    is_numeric: bool
    unit: Optional[str] = None


@dataclass(frozen=True)
class ModbusConfig:
    """Data container for Modbus serial connection parameters."""
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    port: str = "/dev/ttyUSB0"
    slave_id: int = 1
    stopbits: int = 1
    timeout: float = 2.0


@dataclass
class RegisterDefinition:
    """Shared attributes for any Modbus register location."""
    key: str
    address: int


class RegisterBlock:
    """Represents a contiguous chunk of Modbus memory registers."""

    def __init__(self, definitions: List[Union[NumericRegisterDefinition, TextRegisterDefinition]]):
        self.definitions = definitions

        self.min_address = min(register.address for register in definitions)
        self.max_address = max(register.address for register in definitions)

    @property
    def count(self) -> int:
        if not self.definitions:
            return 0
        return (self.max_address - self.min_address) + 1

    def parse_block_response(self, raw_words: List[int]) -> List[Metric]:
        metrics: List[Metric] = []
        for reg in self.definitions:
            offset = reg.address - self.min_address
            if offset < len(raw_words):
                metrics.append(reg.parse_word(raw_words[offset]))
        return metrics


@dataclass
class NumericRegisterDefinition(RegisterDefinition):
    """Schema for registers containing analog or mathematical values."""
    unit: str

    is_signed: Optional[bool] = False
    precision: Optional[float] = None

    def _to_int16(self, raw_word: int) -> int:
        if raw_word < 0b1000000000000000:
            return raw_word

        return raw_word - 0b10000000000000000

    def parse_word(self, raw_word: int) -> Metric:
        parsed_value: Union[int, float] = self._to_int16(
            raw_word) if self.is_signed else raw_word

        if self.precision is not None:
            parsed_value = round(parsed_value * self.precision, 2)

        return Metric(
            key=self.key,
            value=parsed_value,
            unit=self.unit,
            is_numeric=True
        )


@dataclass
class TextRegisterDefinition(RegisterDefinition):
    """Schema for registers tracking state codes that translate into string labels."""
    lookup: Dict[int, str]

    def parse_word(self, raw_word: int) -> Metric:
        label = self.lookup.get(raw_word, f"UNKNOWN_{raw_word}")
        return Metric(
            key=self.key,
            value=label,
            is_numeric=False
        )
