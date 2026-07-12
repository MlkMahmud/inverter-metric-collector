from typing import List

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException

from structlog import get_logger

from inverters.interfaces import (Metric, ModbusConfig,
                                  NumericRegisterDefinition, RegisterBlock,
                                  TextRegisterDefinition)
from utils import retry

logger = get_logger()


class FelicityIvemInverter:
    _REGISTER_BLOCKS: List[RegisterBlock] = [
        RegisterBlock(
            start_address=0x1101,
            definitions=[
                TextRegisterDefinition(
                    address=0x1101,
                    key="working_mode",
                    lookup={
                        0: "power_on", 1: "standby", 2: "bypass",
                        3: "battery", 4: "fault", 5: "line", 6: "charging"
                    }
                ),
                TextRegisterDefinition(
                    address=0x1102,
                    key="battery_charging_state",
                    lookup={}
                ),
                TextRegisterDefinition(
                    address=0x1103,
                    key="fault_code",
                    lookup={}
                ),
                TextRegisterDefinition(
                    address=0x1104,
                    key="power_flow_message",
                    lookup={}
                )
            ]
        ),
        RegisterBlock(
            start_address=0x1108,
            definitions=[
                NumericRegisterDefinition(
                    address=0x1108,
                    key="battery_voltage",
                    unit="V"
                ),
                NumericRegisterDefinition(
                    address=0x1109,
                    key="battery_current",
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x110A,
                    key="battery_power",
                    unit="W"
                )
            ]
        ),
        RegisterBlock(
            start_address=0x1111,
            definitions=[
                NumericRegisterDefinition(
                    address=0x1111, key="ac_output_voltage", unit="V"
                )
            ]
        ),
        RegisterBlock(
            start_address=0x1117,
            definitions=[
                NumericRegisterDefinition(
                    address=0x1117, key="ac_input_voltage", unit="V"
                )
            ]
        ),
        RegisterBlock(
            start_address=0x1119,
            definitions=[
                NumericRegisterDefinition(
                    address=0x1119, key="ac_input_frequency", unit="Hz"
                )
            ]
        ),
        RegisterBlock(
            start_address=0x111E,
            definitions=[
                NumericRegisterDefinition(
                    address=0x111E, key="ac_output_active_power", unit="W"
                ),
                NumericRegisterDefinition(
                    address=0x111F, key="ac_output_apparent_power", unit="VA"
                ),
                NumericRegisterDefinition(
                    address=0x1120, key="load_percentage", unit="%"
                )
            ]
        ),
        RegisterBlock(
            start_address=0x1126,
            definitions=[
                NumericRegisterDefinition(
                    address=0x1126, key="pv_input_voltage", unit="V"
                ),
            ]
        ),
        RegisterBlock(
            start_address=0x112A,
            definitions=[
                NumericRegisterDefinition(
                    address=0x112A, key="pv_input_power", unit="W"
                ),
            ]
        ),
        RegisterBlock(
            start_address=0x1132,
            definitions=[
                NumericRegisterDefinition(
                    address=0x1132, key="battery_percentage", unit="%"
                )
            ]
        )
    ]

    def __init__(self, config: ModbusConfig, model: str):
        self.config = config
        self.model = model

        self.modbus_client = ModbusSerialClient(
            baudrate=self.config.baudrate,
            bytesize=self.config.bytesize,
            parity=self.config.parity,
            port=self.config.port,
            stopbits=self.config.stopbits,
            timeout=self.config.timeout,
        )

    def _establish_connection(self):
        logger.info(
            "Opening serial port interface transaction line", port=self.config.port)

        is_connected = retry(
            fn=self.modbus_client.connect,
            delay=3,
            retries=3,
        )

        if not is_connected:
            raise ConnectionError(
                f"Failed to open Modbus serial connection link on port {self.config.port}. "
                "Check physical cable mapping, permissions, or system device availability."
            )

        logger.info(
            "Modbus serial network interface online",
            port=self.config.port
        )

    def read_telemetry(self) -> List[Metric]:
        metrics: List[Metric] = []

        if not self.modbus_client.connected:
            self._establish_connection()

        for block in self._REGISTER_BLOCKS:
            try:
                response = self.modbus_client.read_holding_registers(
                    address=block.start_address,
                    count=block.count,
                    device_id=self.config.slave_id
                )

                metrics.extend(block.parse_block_response(response.registers))

            except ModbusIOException as e:
                logger.error(
                    "Failed to read register blocks",
                    start_address=block.start_address,
                    count=block.count,
                    error=e
                )

        return metrics
