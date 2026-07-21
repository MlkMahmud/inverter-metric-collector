from enum import StrEnum
from typing import Any, List, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, ConfigDict

from inverters import Metric


class PublisherConfig(BaseModel):
    name: str

    model_config = ConfigDict(frozen=True)


ConfigType = TypeVar("ConfigType", bound=PublisherConfig, covariant=True)


@runtime_checkable
class Publisher(Protocol[ConfigType]):
    def __init__(self, config: ConfigType) -> None: ...

    def publish(self, metrics: List[Metric]) -> Any: ...


class Publishers(StrEnum):
    GENERIC = "generic"
    HOME_ASSISTANT = "homeassistant"
