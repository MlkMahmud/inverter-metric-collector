from typing import Dict, Type
from logging import getLogger

from felicity_ivem import FelicityIvemInverter
from interfaces import Inverter, InverterModel

logger = getLogger(__name__)

_INVERTER_MODEL_CLASS_MAP: Dict[InverterModel, Type[Inverter]] = {
    InverterModel.IVEM12048II: FelicityIvemInverter
}


def get_inverter_class(model: InverterModel) -> Type[Inverter]:
    target_class = _INVERTER_MODEL_CLASS_MAP.get(model, None)

    if not target_class:
        logger.error(
            "Driver lookup failed. Model enum '%s' has no mapped class.", model.name)
        raise NotImplementedError(
            f"Driver for model {model.value} is missing in registry.")
    return target_class
