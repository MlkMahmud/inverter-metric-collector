from logging import getLogger
from typing import List

from inverters import Metric

from .interfaces import PublisherConfig

logger = getLogger("publisher.generic")


class GenericPublisher:
    def __init__(self, config: PublisherConfig):
        self.config = config

    def publish(self, metrics: List[Metric]):
        for metric in metrics:
            if metric.is_numeric:
                logger.info(f"[{metric.key}]: {metric.value}{metric.unit}")
            else:
                logger.info(f"[{metric.key}]: {metric.value}")
