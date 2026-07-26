from random import randint
from typing import Dict, List

import pytest

from inverters import ModbusConfig
from inverters.interfaces import (
    Metric,
    NumericRegisterDefinition,
    RegisterBlock,
    RegisterDefinition,
    TextRegisterDefinition,
)


class TestModbusConfig:
    def test_is_initialized_with_the_correct_default_values(self):
        config = ModbusConfig()

        assert config.baudrate == 9600
        assert config.bytesize == 8
        assert config.parity == "N"
        assert config.port == "/dev/ttyUSB0"
        assert config.retries == 3
        assert config.slave_id == 1
        assert config.stopbits == 1
        assert config.timeout == 2.0

    def test_is_initialized_with_the_provided_values(self):
        baudrate = 1200
        bytesize = 10
        parity = "T"
        port = "/dev/ttyUSB1"
        retries = 1
        slave_id = 2
        stopbits = 2
        timeout = 3.0

        config = ModbusConfig(
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            port=port,
            retries=retries,
            slave_id=slave_id,
            stopbits=stopbits,
            timeout=timeout,
        )

        assert config.baudrate == baudrate
        assert config.bytesize == bytesize
        assert config.parity == parity
        assert config.port == port
        assert config.retries == retries
        assert config.slave_id == slave_id
        assert config.stopbits == stopbits
        assert config.timeout == timeout


class TestRegisterBlock:
    _definitions: List[NumericRegisterDefinition | TextRegisterDefinition] = [
        NumericRegisterDefinition(address=x, key=f"address {x}", unit="%")
        for x in range(1, 100, randint(1, 5))
    ]

    _max_addr = max(d.address for d in _definitions)
    _min_addr = min(d.address for d in _definitions)

    def test_constructor_initializes_object_without_errors(self):
        addr1, addr2 = 1, 2

        cls = RegisterBlock(
            definitions=[
                NumericRegisterDefinition(address=addr1, key="address 1", unit="%"),
                NumericRegisterDefinition(address=addr2, key="address 2", unit="%"),
            ]
        )

        assert isinstance(cls, RegisterBlock)

        assert cls.max_address == addr2
        assert cls.min_address == addr1

    def test_constructor_correctly_calculates_the_count_of_addresses_to_read_when_definitions_list_is_non_empty(
        self,
    ):
        expected_count = (self._max_addr - self._min_addr) + 1
        cls = RegisterBlock(definitions=self._definitions)

        assert cls.count == expected_count

    def test_constructor_correctly_calculates_the_count_of_addresses_to_read_when_definitions_list_is_empty(
        self,
    ):
        cls = RegisterBlock(definitions=[])

        assert cls.count == 0

    def test_parse_block_response(self):
        count = self._max_addr - self._min_addr + 1
        raw_words = [randint(1, 1000) for _ in range(count)]

        cls = RegisterBlock(definitions=self._definitions)
        metrics = cls.parse_block_response(raw_words)

        def sort_fn(d: RegisterDefinition) -> int:
            return d.address

        sorted_definitions = sorted(cls.definitions, key=sort_fn)
        assert len(metrics) == len(cls.definitions)

        for i in range(len(sorted_definitions)):
            defn = sorted_definitions[i]
            metric = metrics[i]
            offset = defn.address - self._min_addr

            assert defn.key == metric.key
            assert metric.value == raw_words[offset]


class TestNumericRegisterDefinition:
    def test_parse_word(self):
        raw_word = 95
        defn = NumericRegisterDefinition(
            address=0x1101, key="state_of_charge", unit="V"
        )

        metric = defn.parse_word(raw_word)

        assert isinstance(metric, Metric)
        assert metric.value == raw_word

    def test_parse_word_correctly_applies_precision(self):
        raw_word = 5537
        defn = NumericRegisterDefinition(
            address=0x2201, key="battery_voltage", unit="V", precision=0.01
        )

        metric = defn.parse_word(raw_word)
        assert isinstance(metric, Metric)
        assert metric.value == 55.37

    @pytest.mark.parametrize(
        "raw_word,expected_value",
        [
            pytest.param(65310, -226, id="negative value"),
            pytest.param(400, 400, id="positive value"),
        ],
    )
    def test_parse_word_correctly_applies_sign(
        self, raw_word: int, expected_value: int
    ):
        defn = NumericRegisterDefinition(
            address=0x2201,
            is_signed=True,
            key="battery_power",
            unit="W",
        )

        metric = defn.parse_word(raw_word)
        assert isinstance(metric, Metric)
        assert metric.value == expected_value


class TestTextRegisterDefinition:
    def test_parse_word_maps_raw_word_to_label_using_lookup_table(self):
        lookup: Dict[int, str] = {0: "off", 1: "on"}

        defn = TextRegisterDefinition(
            address=0x234,
            key="power",
            lookup=lookup,
        )

        metric = defn.parse_word(1)
        assert isinstance(metric, Metric)
        assert metric.value == "on"

    def test_parse_word_maps_unknown_values_to_unknown_constant(self):
        lookup: Dict[int, str] = {0: "off", 1: "on"}

        defn = TextRegisterDefinition(
            address=0x234,
            key="power",
            lookup=lookup,
        )

        metric = defn.parse_word(2)
        assert isinstance(metric, Metric)
        assert metric.value == "UNKNOWN_2"
