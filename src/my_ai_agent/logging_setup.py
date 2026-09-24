import logging
from logging.handlers import RotatingFileHandler

from my_ai_agent.settings import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "logs"


def setup_logging(level: int = logging.INFO) -> None:
    """Log to logs/sanctuary.log (rotated at 1 MB, 3 backups) so the chat UI stays clean."""
    LOG_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(
        LOG_DIR / "sanctuary.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    # Third-party HTTP clients are chatty at INFO.
    for noisy in ["httpx", "httpcore", "urllib3", "googleapiclient", "google_genai"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
