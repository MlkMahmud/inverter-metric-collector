from typing import Dict, List, Type

from pydantic import ValidationError
from structlog import get_logger

from .generic import GenericPublisher
from .homeassistant import HomeAssistantPublisher
from .interfaces import Publisher, PublisherConfig, Publishers

logger = get_logger(__name__)

_PUBLISHER_MAP: Dict[Publishers, Type[Publisher[PublisherConfig]]] = {
    Publishers.GENERIC: GenericPublisher,
    Publishers.HOME_ASSISTANT: HomeAssistantPublisher,
}


def _create_publisher(config_str: str) -> Publisher[PublisherConfig]:
    try:
        config = PublisherConfig.model_validate_json(config_str, extra="allow")
        publisher_class = _get_publisher(Publishers(config.name))

        return publisher_class(config)

    except ValidationError as e:
        logger.error("Publisher configuration is not valid", config=config_str)
        raise e


def _get_publisher(name: Publishers) -> Type[Publisher[PublisherConfig]]:
    publisher = _PUBLISHER_MAP.get(name, None)

    if not publisher:
        logger.error("Publisher lookup failed", publisher_name=name)
        raise NotImplementedError(f"Publisher '{name}' is not listed in registry")

    return publisher


def create_publishers(configs: List[str]) -> List[Publisher[PublisherConfig]]:
    publishers: List[Publisher[PublisherConfig]] = []

    for config in configs:
        publisher = _create_publisher(config)
        publishers.append(publisher)

    return publishers
