from typing import Dict, Type

from structlog import get_logger

from inverters.felicity_ivem import FelicityIvemInverter
from inverters.interfaces import Inverter, InverterModel

logger = get_logger()

_INVERTER_MODEL_CLASS_MAP: Dict[InverterModel, Type[Inverter]] = {
    InverterModel.IVEM12048II: FelicityIvemInverter
}


def get_inverter_class(model: InverterModel) -> Type[Inverter]:
    target_class = _INVERTER_MODEL_CLASS_MAP.get(model, None)

    if not target_class:
        logger.error(f"Driver lookup failed. Model enum '{model}' has no mapped class.")
        raise NotImplementedError(
            f"Driver for model {model.value} is missing in registry."
        )
    return target_class
