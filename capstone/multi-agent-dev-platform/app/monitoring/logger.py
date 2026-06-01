import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
logger.add(
    "logs/workflow.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)