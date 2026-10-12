import sys
import os
import subprocess
from datetime import datetime, timedelta
from nas_log_retrieval import fetch_nas_log
from graphic_generation import generate_graphics
from constants import STAGING_FILE, REPORTS_DIR, CHARTS_DIR, DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME, TARGET_SERVER

for directory in [REPORTS_DIR, CHARTS_DIR]:
    os.makedirs(directory, exist_ok=True)

def process_with_percona(server_num):
    """Feeds the log into pt-query-digest for both Text and JSON output."""
    if not os.path.exists(STAGING_FILE):
        print("No slow query log found in staging. Exiting.")
        return

    print(f"Initiating Percona Toolkit analysis for Server {server_num}...")
    
    now = datetime.now()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_date = today_midnight - timedelta(days=7)
    end_date = today_midnight - timedelta(seconds=1)
    
    # 7 days window calculation
    since_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    until_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_txt = os.path.join(REPORTS_DIR, f"prod_slow_queries_BBDD-{server_num}_{timestamp}.txt")
    report_json = os.path.join(REPORTS_DIR, f"prod_slow_queries_BBDD-{server_num}_{timestamp}.json")

    # DSN definitions for Percona history and review tables
    dsn_base = f"h={DB_HOST},P={DB_PORT},u={DB_USER},p={DB_PASS},D={DB_NAME}"
    review_table = f"query_review_srv{server_num}"
    history_table = f"query_history_srv{server_num}"
    dsn_review = f"{dsn_base},t={review_table}"
    dsn_history = f"{dsn_base},t={history_table}"

    try:
        # 1. Run Percona and generate JSON format explicitly via --output
        # No DB flags here to avoid double-inserting the history records
        with open(report_json, "w") as json_out:
            subprocess.run(
                [
                    "pt-query-digest", 
                    "--limit", "100%", 
                    "--no-version-check", 
                    "--output", "json",
                    "--since", since_str,
                    "--until", until_str,
                    STAGING_FILE
                ],
                stdout=json_out,
                check=True,
                text=True
            )
        
        # 2. Run again for the human-readable text report AND Database insertion
        with open(report_txt, "w") as txt_out:
            subprocess.run(
                [
                    "pt-query-digest", 
                    "--limit", "100%", 
                    "--no-version-check",
                    "--review", dsn_review,
                    "--history", dsn_history,
                    "--create-review-table",
                    "--create-history-table",
                    "--since", since_str,
                    "--until", until_str,
                    STAGING_FILE
                ],
                stdout=txt_out,
                check=True,
                text=True
            )
        
        print(f"Success! Reports generated:\n- {report_txt}\n- {report_json}")
        print(f"Query history saved to DB '{DB_NAME}' in tables '{review_table}' and '{history_table}'.")
        
        generate_graphics(report_json, server_num, timestamp)
        
        os.remove(STAGING_FILE)
        print("Staging area cleaned.")

    except subprocess.CalledProcessError as e:
        print(f"Percona Toolkit failed. Ensure pt-query-digest is installed. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

CONFIG_FILE_PATH = "/etc/config/target_server"

def get_server_num():
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read config file ({e}). Defaulting to server 1...")

    # Local Test
    return TARGET_SERVER

if __name__ == "__main__":
    server_num = get_server_num()

    # Strictly value selection
    if server_num not in ["1", "2"]:
        print(f"Invalid server selection ('{server_num}'). Defaulting to 1...")
        server_num = "1"

    print(f"Successfully loaded: Targeting DB Server {server_num}")

    if fetch_nas_log(server_num):
        process_with_percona(server_num)
