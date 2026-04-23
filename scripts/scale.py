from datetime import datetime, timedelta
import time
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
import typer

from errors import format_aws_error, credential_error

app = typer.Typer(help="Scale ECS tasks based on CW logs for cloud-automation-platform")
logger = logging.getLogger(__name__)

cloudwatch = boto3.client("cloudwatch", region_name="eusc-de-east-1")

def get_cpu_utilization(cluster: str, service: str) -> float | None:
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/ECS",
            Dimensions=[
                {"Name": "ClusterName", "Value": cluster},
                {"Name": "ServiceName", "Value": service},
            ],
            MetricName="CPUUtilization",
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Period=60,
            Statistics=["Average"],
            Unit="Percent",
        )
    except NoCredentialsError as e:
        logger.error(credential_error(e, None))
        return None
    except ClientError as e:
        logger.error(format_aws_error(e, None))
        return None
    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    latest = max(datapoints, key=lambda d: d["Timestamp"])
    return latest["Average"]

def get_memory_utilization(cluster: str, service: str) -> float | None:
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/ECS",
            Dimensions=[
                {"Name": "ClusterName", "Value": cluster},
                {"Name": "ServiceName", "Value": service},
            ],
            MetricName="MemoryUtilization",
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Period=60,
            Statistics=["Average"],
            Unit="Percent",
        )
    except NoCredentialsError as e:
        logger.error(credential_error(e, None))
        return None
    except ClientError as e:
        logger.error(format_aws_error(e, None))
        return None
    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    latest = max(datapoints, key=lambda d: d["Timestamp"])
    return latest["Average"]

def evaluate(cpu: float | None, memory: float | None, cpu_up: float, cpu_down: float) -> str:
    if cpu is not None and cpu > cpu_up:
        return "SCALE_UP"
    if cpu is not None and cpu < cpu_down:
        return "SCALE_DOWN"
    return "NO_CHANGE"

def apply_scaling(action: str, cluster: str, service: str, min_tasks: int, max_tasks: int):
    try:
        ecs = boto3.client("ecs", region_name="eusc-de-east-1")
        current = ecs.describe_services(cluster=cluster, services=[service])
        desired = current["services"][0]["desiredCount"]

        if action == "SCALE_UP":
            desired = min(desired + 1, max_tasks)
            logger.info(f"Scaling up to {desired} tasks")
        elif action == "SCALE_DOWN":
            desired = max(desired - 1, min_tasks)
            logger.info(f"Scaling down to {desired} tasks")
        else:
            return
        
        ecs.update_service(cluster=cluster, service=service, desiredCount=desired)
    except NoCredentialsError as e:
        logger.error(credential_error(e, None))
        return None
    except ClientError as e:
        logger.error(format_aws_error(e, None))
        return None

@app.command()
def run(
    cluster: str = typer.Option(..., help="ECS cluster name"),
    service: str = typer.Option(..., help="ECS service name"),
    interval: int = typer.Option(60, help="Polling interval in seconds"),
    cooldown: int = typer.Option(300, help="Cooldown in seconds after a scaling action"),
    cpu_up: float = typer.Option(70.0, help="CPU threshold to scale up"),
    cpu_down: float = typer.Option(30.0, help="CPU threshold to scale down"),
    min_tasks: int = typer.Option(1, help="Minimum number of tasks"),
    max_tasks: int = typer.Option(5, help="Maximum number of tasks"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Log decisions without applying"),
):
    last_scaled = 0
    while True:
        cpu = get_cpu_utilization(cluster, service)
        memory = get_memory_utilization(cluster, service)
        action = evaluate(cpu, memory, cpu_up, cpu_down)
        if action != "NO_CHANGE" and time.time() - last_scaled > cooldown:
            if not dry_run:
                apply_scaling(action, cluster, service, min_tasks, max_tasks)
            else:
                typer.echo(f"[dry-run] would {action}")
            last_scaled = time.time()
        time.sleep(interval)


