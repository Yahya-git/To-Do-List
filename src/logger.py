import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    logger = logging.getLogger("src.main")
    logger.setLevel(logging.DEBUG)
    file_handler = RotatingFileHandler("app.log", maxBytes=10000000, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
