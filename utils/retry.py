import time
from random import randint
from typing import Callable, TypeVar

from structlog import get_logger

T = TypeVar("T")

logger = get_logger().bind(module="utils.retry")


def retry[T](
    fn: Callable[[], T],
    delay: int = 3,
    retries: int = 3,
) -> T:
    actual_delay = max(1, delay)
    total_attempts = 1 + max(0, retries)

    for attempt in range(1, total_attempts + 1):
        is_final_attempt = attempt == total_attempts
        try:
            return fn()
        except Exception as e:
            if is_final_attempt:
                logger.error(
                    f"Function execution failed permanently after {attempt} total attempts",
                    error=e,
                )
                raise e

            jitter = randint(1, 5)
            backoff = (actual_delay * (2**attempt)) + jitter

            logger.warning(
                f"Function execution failed. Retrying in {backoff} seconds...",
                attempt=attempt,
                total_allowed_attempts=total_attempts,
                error=e,
            )
            time.sleep(backoff)
            continue

    raise RuntimeError("Retry loop exhausted unexpectedly.")
