from typing import Any, List, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from inverters import Metric


@runtime_checkable
class Publisher(Protocol):
    def __init__(self, config: PublisherConfig) -> None:
        ...

    def publish(self, metrics: List[Metric]) -> Any:
        ...


class PublisherConfig(BaseModel):
    name: str

    model_config = ConfigDict(frozen=True)
