import os
import subprocess
import urllib.request
import urllib.error
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# NAS_URL = "http://file-server-2.ctdesarrollo.org/logs/logs_SG/logs_bbdd1/2026-07-21_2026-07-27"
NAS_URL = "http://file-server-2.ctdesarrollo.org/logs/dbs_{server_num}_8_0/mysql-slow.log"
WORKSPACE_DIR = os.path.abspath('mysql_perf_metrics')
STAGING_FILE = os.path.join(WORKSPACE_DIR, "mysql-slow.log")
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "reports")

# Ensure the reports directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

NAS_USER = os.getenv("NAS_USER", "")
NAS_PASS = os.getenv("NAS_PASS", "")

# --- Database Configuration for pt-query-digest ---
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "slow_query_history")

def fetch_nas_log(server_num):
    """Downloads the current mysql-slow.log from the NAS using Basic Auth."""
    server_url = NAS_URL.format(server_num=server_num)
    print(f"Downloading slow query log from {server_url}...")
    
    try:
        # Set up HTTP Basic Authentication
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, server_url, NAS_USER, NAS_PASS)
        auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(auth_handler)
        
        # Stream the download directly to the file
        with opener.open(server_url) as response, open(STAGING_FILE, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        print("Download complete.")
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"Failed to reach the NAS: {e.reason}")
        return False
    except Exception as e:
        print(f"An error occurred during download: {e}")
        return False

def process_with_percona(server_num):
    """Feeds the single uncompressed log into pt-query-digest and saves to DB."""
    if not os.path.exists(STAGING_FILE):
        print("No slow query log found in staging. Exiting.")
        return

    print(f"Initiating Percona Toolkit analysis for Server {server_num}...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORTS_DIR, f"prod_slow_queries_BBDD-{server_num}_{timestamp}.txt")

    # DSN base
    dsn_base = f"h={DB_HOST},P={DB_PORT},u={DB_USER},p={DB_PASS},D={DB_NAME}"
    
    # Dynamic table naming based on server number
    review_table = f"query_review_srv{server_num}"
    history_table = f"query_history_srv{server_num}"
    
    dsn_review = f"{dsn_base},t={review_table}"
    dsn_history = f"{dsn_base},t={history_table}"

    try:
        # Command configuration
        cmd = [
            "pt-query-digest",
            "--limit", "100%",
            "--review", dsn_review,
            "--history", dsn_history,
            "--create-review-table",
            "--create-history-table",
            STAGING_FILE
        ]

        with open(report_file, "w") as outfile:
            subprocess.run(
                cmd,
                stdout=outfile,
                check=True,
                text=True
            )
        
        print(f"Success! Report generated: {report_file}")
        print(f"Query history saved to DB '{DB_NAME}' in tables '{review_table}' and '{history_table}'.")
        
        # Cleanup
        os.remove(STAGING_FILE)
        print("Staging area cleaned.")

    except subprocess.CalledProcessError as e:
        print(f"Percona Toolkit failed. Ensure pt-query-digest is installed. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    server_num = input('Select the DB Server to analyze (1 or 2): ')
    if server_num not in ["1", "2"]:
        server_num = "1"
        print('Server not valid. Selecting 1 by default...')
        
    if fetch_nas_log(server_num):
        process_with_percona(server_num)