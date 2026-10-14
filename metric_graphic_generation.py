import os
from nas_log_retrieval import fetch_nas_log
from constants import REPORTS_DIR, CHARTS_DIR
from time_utils import get_analysis_window
from slow_query_report import process_with_percona
from drive_uploader import upload_server_artifacts

# [OBJETIVO 2 - FUTURO]: Importar módulo de Google Drive
# from drive_uploader import create_drive_folder, upload_server_artifacts

# [OBJETIVO 3 - FUTURO]: Importar módulo de Slack
# from slack_notifier import send_slack_notification

for directory in [REPORTS_DIR, CHARTS_DIR]:
    os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    SERVERS = ["1", "2"]
    window = get_analysis_window()
    processed_servers = []

    print(f"=== Starting Weekly Analysis ({window['folder_name']}) ===")

    # [OBJETIVO 2 - PASO A]: Crear carpeta raíz del rango de fechas en Google Drive antes del bucle
    # drive_folder_id = create_drive_folder(window["folder_name"])

    for srv in SERVERS:
        print(f"\n--- Targeting DB Server {srv} ---")
        if fetch_nas_log(srv):
            success, artifacts = process_with_percona(srv, window["since_str"], window["until_str"])
            if success:
                processed_servers.append(srv)
                upload_server_artifacts(srv, window["folder_name"], artifacts)
        else:
            print(f"[Server {srv}] Failed to retrieve log from NAS. Skipping analysis.")

    # [OBJETIVO 3]: Notificar a Slack al finalizar ambos servidores (si al menos uno tuvo éxito)
    if processed_servers:
        pass
        # send_slack_notification(
        #     date_range=window["folder_name"], 
        #     servers=processed_servers, 
        #     drive_link=f"https://drive.google.com/drive/folders/{drive_folder_id}"
        # )
    else:
        print("No servers were successfully processed. Skipping notifications.")
