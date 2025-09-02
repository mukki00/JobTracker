import logging
from logging.handlers import TimedRotatingFileHandler
def setup_logging(name):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = TimedRotatingFileHandler(
            'logger/logger.txt',
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        handler.suffix = "%Y-%m-%d"
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
    return logger