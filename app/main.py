
import time
import shutil
import logging

import psutil
from fastapi import FastAPI, Response, HTTPException
from prometheus_client import (
    Gauge,
    Counter,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logging.basicConfig(
    filename="logs/monitor.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = FastAPI(
    title="Platform Health Monitor",
    description="Linux system health and resource monitoring API",
    version="1.0.0",
)

CPU_LIMIT = 90
MEMORY_LIMIT = 90
DISK_LIMIT = 90

CPU = Gauge("platform_cpu_usage_percent", "CPU usage percentage")
MEMORY = Gauge("platform_memory_usage_percent", "Memory usage percentage")
DISK = Gauge("platform_disk_usage_percent", "Disk usage percentage")
ERRORS = Counter("platform_check_errors_total", "Failed health checks")


def collect_metrics():
    cpu = psutil.cpu_percent(interval=0.2)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    disk_percent = disk.used / disk.total * 100

    CPU.set(cpu)
    MEMORY.set(memory.percent)
    DISK.set(disk_percent)

    return {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_available_mb": round(memory.available / 1024**2, 2),
        "disk_percent": round(disk_percent, 2),
        "disk_free_gb": round(disk.free / 1024**3, 2),
    }


@app.get("/")
def home():
    return {
        "project": "Platform Health Monitor",
        "message": "Monitoring service is running",
    }


@app.get("/health")
def health():
    try:
        metrics = collect_metrics()
        issues = []

        if metrics["cpu_percent"] >= CPU_LIMIT:
            issues.append("High CPU usage")

        if metrics["memory_percent"] >= MEMORY_LIMIT:
            issues.append("High memory usage")

        if metrics["disk_percent"] >= DISK_LIMIT:
            issues.append("High disk usage")

        status = "degraded" if issues else "healthy"

        logging.info("Health check completed: %s", status)

        return {
            "status": status,
            "issues": issues,
            "metrics": metrics,
            "timestamp": time.time(),
        }

    except Exception:
        ERRORS.inc()
        logging.exception("Health check failed")
        raise HTTPException(status_code=503, detail="Health check failed")


@app.get("/api/v1/system")
def system_metrics():
    try:
        return collect_metrics()
    except Exception:
        ERRORS.inc()
        logging.exception("System metrics collection failed")
        raise HTTPException(status_code=503, detail="Metric collection failed")


@app.get("/metrics")
def prometheus_metrics():
    collect_metrics()
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )