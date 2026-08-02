from typing import List

from pymodbus.client import ModbusSerialClient
from structlog import get_logger

from inverters.interfaces import (
    Metric,
    ModbusConfig,
    NumericRegisterDefinition,
    RegisterBlock,
    TextRegisterDefinition,
)
from utils import retry

logger = get_logger()


class FelicityIvemInverter:
    _REGISTER_BLOCKS: List[RegisterBlock] = [
        RegisterBlock(
            definitions=[
                TextRegisterDefinition(
                    address=0x1101,
                    key="working_mode",
                    lookup={
                        0: "Power On",
                        1: "Standby",
                        2: "Bypass",
                        3: "Battery",
                        4: "Fault",
                        5: "Line",
                        6: "Charging",
                    },
                ),
                TextRegisterDefinition(
                    address=0x1102,
                    key="battery_charging_state",
                    lookup={
                        0: "No Charge",
                        1: "Constant Current",
                        2: "Constant Voltage",
                        3: "Float",
                    },
                ),
                TextRegisterDefinition(
                    address=0x1103,
                    key="fault_code",
                    lookup={
                        1: "BUS Voltage Too High",
                        2: "BUS Voltage Too Low",
                        3: "BUS Soft Start Fail",
                        4: "Inverter Soft Start Fail",
                        5: "Over Current or Surge Detected by Software",
                        6: "Over Current or Surge Detected by Hardware",
                        7: "Output Voltage Too Low",
                        8: "Output Voltage Too High",
                        9: "Output Short Circuited",
                        10: "Overload Timeout",
                        11: "Battery Voltage Too High",
                        12: "Over Current at DC/DC Circuit",
                        13: "PV Voltage Too High",
                        14: "Short Circuited at PV Port",
                        15: "PV Power is Abnormal",
                        16: "Over Current at PV Port",
                        17: "Fan is Locked",
                        18: "Over Temperature at PV Circuit",
                        19: "Over Temperature at Convert L Circuit",
                        20: "Over Temperature at INV Circuit",
                        21: "Inner Temperature is Over Limit",
                        22: "DCDC Current Sensor Failed",
                        23: "No 2 DCDC Current Sensor Failed",
                        24: "Inverter Current Sensor Failed",
                        25: "OP Current Sensor Failed",
                        26: "Sharing Current Sensor Failed",
                        27: "AC Input Output Wires are Inversely Connected",
                        28: "Single Unit is Installed to Parallel System",
                        29: "DC/DC Soft Start Fail",
                        31: "Over Temperature at Convert H Circuit",
                        32: "Over Temperature at LLC TX",
                        33: "Over Current at LLC Circuit",
                        34: "DC/DC Hardware Overflows",
                        35: "Over Voltage in BUS",
                        40: "CAN Data Loss",
                        41: "Host Data Loss",
                        42: "Synchronization Data Loss",
                        43: "Current Feedback Into Inverter Detected",
                        44: "Firmware Version of Each Inverter is Not The Same",
                        45: "Output Current of Each Inverter is Different",
                        46: "AC Output Mode Setting is Different",
                        47: "Generator Current Sensor Failed",
                    },
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x110A, is_signed=True, key="battery_power", unit="W"
                ),
                NumericRegisterDefinition(
                    address=0x110C,
                    key="inverter_voltage",
                    precision=0.1,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x110D,
                    is_signed=True,
                    key="inverter_current",
                    precision=0.1,
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x110E,
                    key="inverter_frequency",
                    precision=0.01,
                    unit="Hz",
                ),
                NumericRegisterDefinition(
                    address=0x110F,
                    is_signed=True,
                    key="inverter_power",
                    unit="W",
                ),
                NumericRegisterDefinition(
                    address=0x1110,
                    key="inverter_apparent_power",
                    unit="VA",
                ),
                NumericRegisterDefinition(
                    address=0x1111, key="ac_output_voltage", precision=0.1, unit="V"
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x1117, key="ac_input_voltage", precision=0.1, unit="V"
                ),
                NumericRegisterDefinition(
                    address=0x1119, key="ac_input_frequency", precision=0.01, unit="Hz"
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x111E, is_signed=True, key="load_power", unit="W"
                ),
                NumericRegisterDefinition(
                    address=0x111F, key="ac_output_apparent_power", unit="VA"
                ),
                NumericRegisterDefinition(
                    address=0x1120, key="load_percentage", unit="%"
                ),
                NumericRegisterDefinition(
                    address=0x1121,
                    is_signed=True,
                    key="transformer_temperature",
                    unit="°C",
                ),
                NumericRegisterDefinition(
                    address=0x1122,
                    is_signed=True,
                    key="inverter_temperature",
                    unit="°C",
                ),
                NumericRegisterDefinition(
                    address=0x1123, is_signed=True, key="battery_temperature", unit="°C"
                ),
                NumericRegisterDefinition(
                    address=0x1124, key="bus_voltage", precision=0.1, unit="V"
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x1126, key="pv1_voltage", precision=0.1, unit="V"
                ),
                NumericRegisterDefinition(
                    address=0x1129,
                    is_signed=True,
                    key="pv1_current",
                    precision=0.1,
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x112A, is_signed=True, key="pv1_power", unit="W"
                ),
                NumericRegisterDefinition(
                    address=0x112B, is_signed=True, key="scc_temperature", unit="°C"
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x1132, key="bms_state_of_charge", unit="%"
                ),
                NumericRegisterDefinition(
                    address=0x1133,
                    key="bms_cv_voltage",
                    precision=0.1,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x1134,
                    key="bms_float_voltage",
                    precision=0.1,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x1135,
                    key="bms_cutoff_voltage",
                    precision=0.1,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x1136,
                    key="bms_max_charge_current",
                    precision=0.1,
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x1137,
                    key="bms_max_discharge_current",
                    precision=0.1,
                    unit="A",
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x1159,
                    key="pv2_voltage",
                    precision=0.1,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x115A,
                    is_signed=True,
                    key="pv2_current",
                    precision=0.1,
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x115B,
                    is_signed=True,
                    key="pv2_power",
                    unit="W",
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x1200, key="battery_line_voltage", precision=0.1, unit="V"
                ),
                NumericRegisterDefinition(
                    address=0x1201,
                    key="battery_charge_discharge_limit_voltage",
                    precision=0.1,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x1202,
                    key="battery_max_charge_current_limit",
                    precision=0.1,
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x1203,
                    key="battery_max_discharge_current_limit",
                    precision=0.1,
                    unit="A",
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                NumericRegisterDefinition(
                    address=0x120C,
                    is_signed=True,
                    key="battery_current",
                    precision=0.1,
                    unit="A",
                ),
                NumericRegisterDefinition(
                    address=0x120D,
                    key="battery_voltage",
                    precision=0.01,
                    unit="V",
                ),
                NumericRegisterDefinition(
                    address=0x1210,
                    key="battery_state_of_charge",
                    precision=0.1,
                    unit="%",
                ),
                NumericRegisterDefinition(
                    address=0x1211,
                    key="battery_state_of_health",
                    precision=0.1,
                    unit="%",
                ),
            ]
        ),
        RegisterBlock(
            definitions=[
                TextRegisterDefinition(
                    address=0x2129,
                    key="ac_output_frequency",
                    lookup={0: "50Hz", 1: "60Hz"},
                ),
                TextRegisterDefinition(
                    address=0x212A,
                    key="output_source_priority",
                    lookup={
                        0: "Utility First",
                        1: "Solar First",
                        2: "Solar Battery Utility",
                    },
                ),
                TextRegisterDefinition(
                    address=0x212B,
                    key="application_mode",
                    lookup={0: "APL", 1: "UPS"},
                ),
                TextRegisterDefinition(
                    address=0x212C,
                    key="charging_source_priority",
                    lookup={
                        1: "Solar First",
                        2: "Solar and Utility First",
                        3: "Solar Only",
                    },
                ),
            ]
        ),
    ]

    def __init__(self, config: ModbusConfig, model: str):
        self.config = config
        self.model = model

        self.modbus_client = ModbusSerialClient(
            baudrate=self.config.baudrate,
            bytesize=self.config.bytesize,
            parity=self.config.parity,
            port=self.config.port,
            retries=self.config.retries,
            stopbits=self.config.stopbits,
            timeout=self.config.timeout,
        )

    def _establish_connection(self):
        logger.info(
            "Opening serial port interface transaction line", port=self.config.port
        )

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

        logger.info("Modbus serial network interface online", port=self.config.port)

    def read_telemetry(self) -> List[Metric]:
        metrics: List[Metric] = []

        if not self.modbus_client.connected:
            self._establish_connection()

        for block in self._REGISTER_BLOCKS:
            response = self.modbus_client.read_holding_registers(
                address=block.min_address,
                count=block.count,
                device_id=self.config.slave_id,
            )

            if response.isError():
                logger.error(
                    "Failed to read register block",
                    block=block,
                    error_code=response.exception_code,
                )
                continue

            metrics.extend(block.parse_block_response(response.registers))

        return metrics
