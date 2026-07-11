from typing import Dict, Union

from .interfaces import ModbusConfig


class FelicityIvemInverter:
    def __init__(self, config: ModbusConfig):
        self.config = config

    def read_telemetry(self) -> Dict[str, Union[int, float]]:
        return {}
