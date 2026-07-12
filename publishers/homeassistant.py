from typing import List

from pydantic import ConfigDict

from inverters import Metric

from .interfaces import PublisherConfig


class HomeAssistantPublisherConfig(PublisherConfig):
    mqqt_url: str

    model_config = ConfigDict(extra="forbid", frozen=True)


class HomeAssistantPublisher:
    def __init__(self, config: HomeAssistantPublisherConfig) -> None:
        self.config = config

    def publish(self, metrics: List[Metric]) -> None:
        return
