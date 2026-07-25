from typing import Type

import pytest

from inverters import get_inverter_class
from inverters.felicity_ivem import FelicityIvemInverter
from inverters.interfaces import Inverter, InverterModel


class TestGetInverterClass:
    @pytest.mark.parametrize(
        "model,model_class",
        [pytest.param(InverterModel.IVEM12048II, FelicityIvemInverter)],
    )
    def test_returns_mapped_class_for_a_given_model(
        self, model: InverterModel, model_class: Type[Inverter]
    ):
        cls = get_inverter_class(model)
        assert cls == model_class

    def test_raises_a_not_implemented_exception_for_models_that_are_not_in_the_registry(
        self,
    ):
        model = "mock-model"
        expected_err_message = f"Driver for model {model} is missing in registry."

        with pytest.raises(NotImplementedError) as exc_info:
            get_inverter_class(model)  # type: ignore
        assert str(exc_info.value) == expected_err_message
