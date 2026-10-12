FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    percona-toolkit \
    libdbd-mysql-perl \
    libdbi-perl \
    libterm-readkey-perl \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/mysql_perf_metrics/reports /app/mysql_perf_metrics/charts

ENTRYPOINT ["python", "main.py"]