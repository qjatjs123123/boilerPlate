import logging

logger = logging.getLogger("app")


def log_event(event: str, **context: object) -> None:
    """비즈니스 이벤트 구조화 로깅 — log_event("post_created", post_id=...)"""
    parts = ", ".join(f"{key}={value}" for key, value in context.items())
    logger.info("%s - %s", event, parts)


def log_exception(event: str, exception: Exception, **context: object) -> None:
    """예외 로깅 — 스택 트레이스 포함"""
    parts = ", ".join(f"{key}={value}" for key, value in context.items())
    logger.exception("%s - %s (%s: %s)", event, parts, type(exception).__name__, exception)
