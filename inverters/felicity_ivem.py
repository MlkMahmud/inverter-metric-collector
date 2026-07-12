from typing import Dict, List

from inverters.interfaces import (
    Metric,
    ModbusConfig,
    NumericRegisterDefinition,
    RegisterBlock,
    TextRegisterDefinition
)


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

    def __init__(self, config: ModbusConfig):
        self.config = config

    def read_telemetry(self) -> Dict[str, Metric]:
        return {}
