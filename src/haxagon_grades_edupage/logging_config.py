from __future__ import annotations

import os
import sys
from typing import Optional

from loguru import logger

_CONFIGURED = False


def setup_logging(level: Optional[str] = None):
    global _CONFIGURED
    if _CONFIGURED:
        return logger

    resolved_level = level or os.environ.get("HAXAGON_LOG_LEVEL", "INFO")

    logger.remove()
    logger.add(sys.stdout, level=resolved_level, enqueue=True, backtrace=False, diagnose=False)

    _CONFIGURED = True
    return logger
