from datetime import datetime, timedelta

def get_analysis_window():
    """Calculate the 7-day window only once to ensure consistency between both servers and Drive"""
    now = datetime.now()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_date = today_midnight - timedelta(days=7)
    end_date = today_midnight - timedelta(seconds=1)
    
    return {
        "since_str": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "until_str": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "folder_name": f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    }