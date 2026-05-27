"""Filesystem locations for persisted EduPage authentication state."""

import os
import sys
from pathlib import Path

APP_DIR_NAME = "edu_page_automat"
AUTH_FILE_NAME = "auth.json"
AUTH_FILE_ENV_VAR = "EDUPAGE_AUTH_FILE"


def get_auth_file_path() -> Path:
    """Return the user-level path used for persisted Playwright storage state."""
    override = os.environ.get(AUTH_FILE_ENV_VAR)
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base_dir / APP_DIR_NAME / AUTH_FILE_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME / AUTH_FILE_NAME

    state_home = os.environ.get("XDG_STATE_HOME")
    base_dir = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return base_dir / APP_DIR_NAME / AUTH_FILE_NAME
