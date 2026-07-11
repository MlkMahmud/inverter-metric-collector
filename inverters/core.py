from typing import Dict, Type

from felicity_ivem import FelicityIvemInverter
from interfaces import Inverter

_INVERTER_MODEL_CLASS_MAP: Dict[str, Type[Inverter]] = {
    "IVEM_12048-II": FelicityIvemInverter
}


def get_inverter_class(model: str) -> Type[Inverter]:
    inverter_class = _INVERTER_MODEL_CLASS_MAP.get(model.lower(), None)

    if inverter_class:
        return inverter_class

    raise NotImplementedError(
        f"Inverter model {model} has not been implemented")
