from argparse import Namespace
from unittest.mock import MagicMock, call, patch

import pytest
from pytest_snapshot.plugin import Snapshot

from inverters.felicity_ivem import FelicityIvemInverter
from inverters.interfaces import ModbusConfig


class TestFelicityIvemInverter:
    @pytest.fixture(autouse=True)
    def mock_logger(self):
        with patch("inverters.felicity_ivem.core.logger") as m:
            m.error = MagicMock()
            m.info = MagicMock()
            yield m

    @pytest.fixture
    def mock_modbus_config(self):
        return ModbusConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            bytesize=8,
            parity="N",
            retries=3,
            stopbits=1,
            timeout=2,
            slave_id=1,
        )

    @pytest.fixture
    def mock_modbus_serial_client(self):
        client = MagicMock()
        client.connect = MagicMock(return_value=True)
        client.read_holding_registers = MagicMock(
            return_value=Namespace(isError=lambda: False, registers=[0] * 10)
        )
        return client

    @pytest.fixture
    def mock_modbus_serial_client_cls(self, mock_modbus_serial_client: MagicMock):
        with patch("inverters.felicity_ivem.core.ModbusSerialClient") as cls:
            cls.return_value = mock_modbus_serial_client
            yield cls

    @pytest.fixture(autouse=True)
    def mock_retry(self):
        with patch("inverters.felicity_ivem.core.retry") as m:
            m.return_value = True
            yield m

    @pytest.fixture
    def inverter(
        self, mock_modbus_config: ModbusConfig, mock_modbus_serial_client: MagicMock
    ):
        inv = FelicityIvemInverter(config=mock_modbus_config, model="IVEM-5K")
        inv.modbus_client = mock_modbus_serial_client
        return inv

    def test_init_configures_modbus_client(
        self,
        mock_modbus_config: ModbusConfig,
        mock_modbus_serial_client_cls: MagicMock,
    ):
        inverter = FelicityIvemInverter(config=mock_modbus_config, model="IVEM-5K")

        mock_modbus_serial_client_cls.assert_called_once_with(
            baudrate=mock_modbus_config.baudrate,
            bytesize=mock_modbus_config.bytesize,
            parity=mock_modbus_config.parity,
            port=mock_modbus_config.port,
            retries=mock_modbus_config.retries,
            stopbits=mock_modbus_config.stopbits,
            timeout=mock_modbus_config.timeout,
        )

        assert inverter.model == "IVEM-5K"
        assert inverter.config == mock_modbus_config

    def test_register_blocks_integrity(self, inverter: FelicityIvemInverter):
        blocks = inverter._REGISTER_BLOCKS  # type: ignore
        assert len(blocks) == 9

        keys = [defn.key for block in blocks for defn in block.definitions]
        assert len(keys) == len(set(keys)), "Duplicate register keys detected"

        addresses = [defn.address for block in blocks for defn in block.definitions]
        assert len(addresses) == len(
            set(addresses)
        ), "Duplicate register addresses detected"

    def test_register_blocks_snapshot(
        self, inverter: FelicityIvemInverter, snapshot: Snapshot
    ):
        actual_blocks = [vars(block) for block in inverter._REGISTER_BLOCKS]  # type: ignore
        snapshot.assert_match(str(actual_blocks), "felicity_ivem_register_blocks.txt")

    def test_establish_connection_success(
        self, inverter: FelicityIvemInverter, mock_retry: MagicMock
    ):
        inverter._establish_connection()  # type: ignore

        mock_retry.assert_called_once_with(
            fn=inverter.modbus_client.connect,
            delay=3,
            retries=3,
        )

    def test_establish_connection_failure_raises_exception(
        self, inverter: FelicityIvemInverter, mock_retry: MagicMock
    ):
        mock_retry.return_value = False

        with pytest.raises(ConnectionError) as exc_info:
            inverter._establish_connection()  # type: ignore

        assert "Failed to open Modbus serial connection link" in str(exc_info.value)

    def test_read_telemetry_calls_establish_connection_if_disconnected(
        self,
        inverter: FelicityIvemInverter,
        mock_modbus_serial_client: MagicMock,
        mock_retry: MagicMock,
    ):
        mock_modbus_serial_client.connected = False
        metrics = inverter.read_telemetry()

        mock_retry.assert_called_once_with(
            fn=inverter.modbus_client.connect,
            delay=3,
            retries=3,
        )
        assert metrics is not None

    def test_read_telemetry_does_not_call_establish_connection_if_already_connected(
        self,
        inverter: FelicityIvemInverter,
        mock_retry: MagicMock,
    ):
        metrics = inverter.read_telemetry()

        mock_retry.assert_not_called()
        assert metrics is not None

    def test_read_telemetry_reads_all_blocks(
        self,
        inverter: FelicityIvemInverter,
        mock_modbus_config: ModbusConfig,
        mock_modbus_serial_client: MagicMock,
    ):
        blocks = inverter._REGISTER_BLOCKS  # type: ignore
        metrics = inverter.read_telemetry()

        definitions_list = [
            definition for definition in [block.definitions for block in blocks]
        ]

        mock_modbus_serial_client.read_holding_registers.assert_has_calls(
            [
                call(
                    address=block.min_address,
                    count=block.count,
                    device_id=mock_modbus_config.slave_id,
                )
                for block in blocks
            ]
        )

        assert len(metrics) == len(
            [
                definition
                for definitions in definitions_list
                for definition in definitions
            ]
        )

    def test_read_telemetry_handles_read_errors_gracefully(
        self,
        inverter: FelicityIvemInverter,
        mock_logger: MagicMock,
        mock_modbus_config: ModbusConfig,
        mock_modbus_serial_client: MagicMock,
    ):
        blocks = inverter._REGISTER_BLOCKS  # type: ignore

        # simulate success for all but last register block
        side_effect = [
            Namespace(isError=lambda: False, registers=[0] * 10)
            for _ in range(len(blocks) - 1)
        ]

        side_effect.append(Namespace(isError=lambda: True, exception_code=2))
        mock_modbus_serial_client.read_holding_registers.side_effect = side_effect

        definitions_list = [
            # exclude all register definitions from last register block since read op failed
            definition
            for definition in [block.definitions for block in blocks[:-1]]
        ]

        metrics = inverter.read_telemetry()

        mock_modbus_serial_client.read_holding_registers.assert_has_calls(
            [
                call(
                    address=block.min_address,
                    count=block.count,
                    device_id=mock_modbus_config.slave_id,
                )
                for block in blocks
            ]
        )

        mock_logger.error.assert_called_once_with(
            "Failed to read register block", block=blocks[-1], error_code=2
        )

        assert len(metrics) == len(
            [
                definition
                for definitions in definitions_list
                for definition in definitions
            ]
        )
