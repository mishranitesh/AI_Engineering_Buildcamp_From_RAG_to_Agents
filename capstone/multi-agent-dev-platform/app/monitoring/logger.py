import sys
from loguru import logger
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / "logs"

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
logger.add(
    str(LOG_DIR / "workflow.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)