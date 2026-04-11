import time
from datetime import datetime, timezone

import psutil
from fastapi import FastAPI
from pydantic import BaseModel

APP_START_TIME = time.monotonic()
psutil.cpu_percent()
BYTES_PER_GB = 1024 ** 3

app = FastAPI(title="Simple app")


class HealthCheck(BaseModel):
    status: str = "OK"


class Metrics(BaseModel):
    uptime_seconds: float
    timestamp: str
    cpu_usage: float
    free_ram_percent: float
    disk_free_gb: float
    cpu_count: int
    total_ram: int
    load_average: list[float]
    network_io_sent_mb: float
    network_io_recv_mb: float


class DataResponse(BaseModel):
    status: str = "OK"
    metrics: Metrics


def _collect_metrics() -> Metrics:
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    load_average = psutil.getloadavg()
    net = psutil.net_io_counters()
    return Metrics(
        uptime_seconds=round(time.monotonic() - APP_START_TIME, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        cpu_usage=psutil.cpu_percent(interval=0.1),
        free_ram_percent=round(ram.available * 100 / ram.total, 2),
        disk_free_gb=round(disk.free / BYTES_PER_GB, 2),
        cpu_count=psutil.cpu_count(),
        total_ram=psutil.virtual_memory().total / (1024 ** 3),
        load_average=[round(avg, 2) for avg in load_average],
        network_io_sent_mb=round(net.bytes_sent / (1024 ** 2), 2),
        network_io_recv_mb=round(net.bytes_recv / (1024 ** 2), 2),
    )


@app.get("/health")
def health():
    return HealthCheck(status="OK")


@app.get("/data", response_model=DataResponse)
def data():
    return DataResponse(metrics=_collect_metrics())

