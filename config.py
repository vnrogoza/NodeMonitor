import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MONITOR_URL = os.getenv("MONITOR_URL", "https://cbr.ru/s/newbik")
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "1"))
REPORT_INTERVAL_MINUTES = int(os.getenv("REPORT_INTERVAL_MINUTES", "2"))
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "monitor.db")
REPORT_TEMPLATE_PATH = BASE_DIR / os.getenv("REPORT_TEMPLATE_PATH", "report_template.html")
REPORT_OUTPUT_PATH = BASE_DIR / os.getenv("REPORT_OUTPUT_PATH", "report.html")
REPORT_HEADER = os.getenv("REPORT_HEADER", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
