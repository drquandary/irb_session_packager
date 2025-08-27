"""Configuration for irb_session_packager."""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
APP_DIR = PROJECT_ROOT / "app"

# Application settings
APP_NAME = "Irb Session Packager"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8000"))

# Data settings
SAMPLE_DATA_FILE = DATA_DIR / "sample_data.csv"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
