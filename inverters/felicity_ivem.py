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
                        0: "power_on",
                        1: "standby",
                        2: "bypass",
                        3: "battery",
                        4: "fault",
                        5: "line",
                        6: "charging",
                    },
                ),
                TextRegisterDefinition(
                    address=0x1102,
                    key="battery_charging_state",
                    lookup={
                        0: "no_charge",
                        1: "constant_current",
                        2: "constant_voltage",
                        3: "float",
                    },
                ),
                TextRegisterDefinition(
                    address=0x1103,
                    key="fault_code",
                    lookup={
                        1: "bus_voltage_too_high",
                        2: "bus_voltage_too_low",
                        3: "bus_soft_start_fail",
                        4: "inverter_soft_start_fail",
                        5: "over_current_or_surge_detected_by_software",
                        6: "over_current_or_surge_detected_by_hardware",
                        7: "output_voltage_too_low",
                        8: "output_voltage_too_high",
                        9: "output_short_circuited",
                        10: "overload_timeout",
                        11: "battery_voltage_too_high",
                        12: "over_current_at_dc_or_dc_circuit",
                        13: "pv_voltage_too_high",
                        14: "short_circuited_at_pv_port",
                        15: "pv_power_is_abnormal",
                        16: "over_current_at_pv_port",
                        17: "fan_is_locked",
                        18: "over_temperature_at_pv_circuit",
                        19: "over_temperature_at_convert_l_circuit",
                        20: "over_temperature_at_inv_circuit",
                        21: "inner_temperature_is_over_limit",
                        22: "dc_dc_current_sensor_failed",
                        23: "no_2_dc_dc_current_sensor_failed",
                        24: "inverter_current_sensor_failed",
                        25: "op_current_sensor_failed",
                        26: "sharing_current_sensor_failed",
                        27: "ac_input_output_wires_are_inversely_connected",
                        28: "single_unit_is_installed_to_parallel_system",
                        29: "dc_dc_soft_start_fail",
                        31: "over_temperature_at_convert_h_circuit",
                        32: "over_temperature_at_llc_tx",
                        33: "over_current_at_llc_circuit",
                        34: "dc_dc_hardware_overflows",
                        35: "over_voltage_in_bus",
                        40: "can_data_loss",
                        41: "host_data_loss",
                        42: "synchronization_data_loss",
                        43: "current_feedback_into_inverter_detected",
                        44: "firmware_version_of_each_inverter_is_not_the_same",
                        45: "output_current_of_each_inverter_is_different",
                        46: "ac_output_mode_setting_is_different",
                        47: "generator_current_sensor_failed",
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
                TextRegisterDefinition(address=0x1138, key="bms_fault_code", lookup={}),
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
