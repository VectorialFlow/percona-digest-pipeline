import os
import subprocess
from datetime import datetime
from graphic_generation import generate_graphics
from constants import STAGING_FILE, REPORTS_DIR, DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

def process_with_percona(server_num, since_str, until_str):
    """Feeds the log into pt-query-digest for both Text and JSON output."""
    if not os.path.exists(STAGING_FILE):
        print(f"[Server {server_num}] No slow query log found in staging. Exiting.")
        return False

    print(f"Initiating Percona Toolkit analysis for Server {server_num}...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_txt = os.path.join(REPORTS_DIR, f"prod_slow_queries_BBDD-{server_num}_{timestamp}.txt")
    report_json = os.path.join(REPORTS_DIR, f"prod_slow_queries_BBDD-{server_num}_{timestamp}.json")

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
                    # "--review", dsn_review,
                    # "--history", dsn_history,
                    # "--create-review-table",
                    # "--create-history-table",
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
        
        chart_paths = generate_graphics(report_json, server_num, timestamp)
        
        artifacts = [report_txt] + chart_paths
        
        return True, artifacts

    except subprocess.CalledProcessError as e:
        print(f"Percona Toolkit failed. Ensure pt-query-digest is installed. Error: {e}")
        return False, []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False, []
    finally:
        if os.path.exists(STAGING_FILE):
            os.remove(STAGING_FILE)
            print(f"[Server {server_num}] Staging area cleaned.")