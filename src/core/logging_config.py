import logging
import sys
import os
from pythonjsonlogger import jsonlogger


def setup_logging():
    # If not production, keep standard logging
    if os.getenv("ENVIRONMENT") != "production":
        return

    logger = logging.getLogger()

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logHandler = logging.StreamHandler(sys.stdout)
    # The format string defines what gets included in the JSON output
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    logHandler.setFormatter(formatter)

    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

    # Make third-party loggers less noisy
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
