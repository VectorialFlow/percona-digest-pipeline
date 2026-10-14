import os
from nas_log_retrieval import fetch_nas_log
from constants import REPORTS_DIR, CHARTS_DIR
from time_utils import get_analysis_window
from slow_query_report import process_with_percona
from drive_uploader import upload_server_artifacts

for directory in [REPORTS_DIR, CHARTS_DIR]:
    os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    SERVERS = ["1", "2"]
    window = get_analysis_window()
    processed_servers = []

    print(f"=== Starting Weekly Analysis ({window['folder_name']}) ===")

    for srv in SERVERS:
        print(f"\n--- Targeting DB Server {srv} ---")
        if fetch_nas_log(srv):
            success, artifacts = process_with_percona(srv, window["since_str"], window["until_str"])
            if success:
                processed_servers.append(srv)
                upload_server_artifacts(srv, window["folder_name"], artifacts)
        else:
            print(f"[Server {srv}] Failed to retrieve log from NAS. Skipping analysis.")
