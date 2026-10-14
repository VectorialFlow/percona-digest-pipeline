import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from constants import CHARTS_DIR


def generate_graphics(json_path, server_num, timestamp):
    """Parses Percona JSON output and generates performance charts."""
    print("Generating performance graphics...")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Extract the Top 5 worst queries from the JSON payload
        records = []
        for query in data.get('classes', [])[:5]:
            checksum = query.get('checksum', 'Unknown')[:8]  # Short hash for labels
            metrics = query.get('metrics', {})
            
            records.append({
                'Query Hash': checksum,
                'Exec Time (95%)': float(metrics.get('Query_time', {}).get('pct_95', 0)),
                'Lock Time (95%)': float(metrics.get('Lock_time', {}).get('pct_95', 0)),
                'Rows Examined (95%)': float(metrics.get('Rows_examined', {}).get('pct_95', 0)),
                'Rows Sent (95%)': float(metrics.get('Rows_sent', {}).get('pct_95', 0))
            })
            
        if not records:
            print("No query data found in JSON to graph.")
            return

        df = pd.DataFrame(records)
        df.set_index('Query Hash', inplace=True)

        # Chart 1: Execution Time Only
        fig, ax = plt.subplots(figsize=(10, 6))
        # Removed Lock Time and simplified to a single color
        df[['Exec Time (95%)']].plot(kind='bar', ax=ax, color=['#1f77b4'])
        plt.title(f"Top 5 Bottlenecks: Execution Time (Server {server_num})")
        plt.ylabel("Seconds (95th Percentile)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart1_path = os.path.join(CHARTS_DIR, f"exec_time_BBDD-{server_num}_{timestamp}.png")
        plt.savefig(chart1_path)
        plt.close()

        # Chart 2: Rows Examined vs Rows Sent (Highlights Buffer Pool/Index efficiency)
        fig, ax = plt.subplots(figsize=(10, 6))
        df[['Rows Examined (95%)', 'Rows Sent (95%)']].plot(kind='bar', ax=ax, color=['#ff7f0e', '#2ca02c'])
        plt.title(f"Top 5 Bottlenecks: Index Efficiency (Server {server_num})")
        plt.ylabel("Row Count (95th Percentile)")
        plt.yscale('log') # Log scale because examined rows often dwarf sent rows
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart2_path = os.path.join(CHARTS_DIR, f"row_metrics_BBDD-{server_num}_{timestamp}.png")
        plt.savefig(chart2_path)
        plt.close()

        print(f"Graphics saved to {CHARTS_DIR}")
        return [chart1_path, chart2_path]

    except Exception as e:
        print(f"Failed to generate graphics: {e}")