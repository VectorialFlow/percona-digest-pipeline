import os
from dotenv import load_dotenv

load_dotenv()

# --- DIR Paths --- 
WORKSPACE_DIR = "./mysql_perf_metrics"
STAGING_FILE = os.path.join(WORKSPACE_DIR, "mysql-slow.log")
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "reports")
CHARTS_DIR = os.path.join(WORKSPACE_DIR, "charts")

# --- NAS Configuration --- 
NAS_URL = os.getenv("NAS_URL", "")
NAS_USER = os.getenv("NAS_USER", "")
NAS_PASS = os.getenv("NAS_PASS", "")

# --- Database Configuration for pt-query-digest ---
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "slow_query_history")

# --- Server selection ---
TARGET_SERVER = os.getenv("TARGET_SERVER", "1")