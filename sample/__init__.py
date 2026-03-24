import logging

logger = logging.getLogger(__name__)


def square(n: int) -> int:
    logger.info("n=%d", n)
    return n * n
