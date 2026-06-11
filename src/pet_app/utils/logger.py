import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from pet_app.utils.paths import get_logs_dir


def setup_logger(name, level=logging.INFO):
    """Set up a logger with both console and timed rotating file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Timed rotating file handler - rotate daily at midnight
    logs_dir = get_logs_dir()
    log_file = logs_dir / "pet_app.log"

    # TimedRotatingFileHandler: rotate every day at midnight
    # Keep 7 days of backup logs
    file_handler = TimedRotatingFileHandler(
        str(log_file),
        when="midnight",  # Rotate at midnight
        interval=1,  # Every 1 day
        backupCount=7,  # Keep 7 backup files
        encoding="utf-8"
    )

    # Customize backup file naming: pet_app.log.2026-05-23 instead of pet_app.log.1
    file_handler.namer = lambda name: name.replace(".log", "") + ".log"
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger("pet_app")
logger.info("=" * 60)
logger.info("Log rotation enabled: Daily at midnight, keeping 7 days backup")
logger.info("=" * 60)
