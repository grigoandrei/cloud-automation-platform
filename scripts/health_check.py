import logging
from datetime import datetime, timedelta

import boto3
import requests
import typer
from botocore.exceptions import ClientError, NoCredentialsError

from errors import format_aws_error, credential_error

app = typer.Typer(help="Health checks for cloud-automation-platform")
logger = logging.getLogger(__name__)


def check_health_endpoint(endpoint: str) -> bool:
    url = f"{endpoint}/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.json().get("status") == "OK":
            typer.echo("  /health: OK")
            return True
        typer.echo(f"  /health: FAIL (status={response.status_code})", err=True)
        return False
    except requests.RequestException as e:
        typer.echo(f"  /health: FAIL ({e})", err=True)
        return False


def check_data_endpoint(endpoint: str) -> bool:
    url = f"{endpoint}/data"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            typer.echo(f"  /data: FAIL (status={response.status_code})", err=True)
            return False
        data = response.json()
        metrics = data.get("metrics", {})
        required_keys = [
            "uptime_seconds", "timestamp", "cpu_usage",
            "free_ram_percent", "disk_free_gb",
        ]
        missing = [k for k in required_keys if k not in metrics]
        if missing:
            typer.echo(f"  /data: FAIL (missing keys: {missing})", err=True)
            return False
        typer.echo(f"  /data: OK (cpu={metrics['cpu_usage']}%, ram_free={metrics['free_ram_percent']}%)")
        return True
    except requests.RequestException as e:
        typer.echo(f"  /data: FAIL ({e})", err=True)
        return False


def check_ecs_tasks(cluster: str, service: str, region: str) -> bool:
    try:
        ecs = boto3.client("ecs", region_name=region)
        response = ecs.describe_services(cluster=cluster, services=[service])
        if not response.get("services"):
            typer.echo("  ECS service: FAIL (service not found)", err=True)
            return False
        svc = response["services"][0]
        running = svc["runningCount"]
        desired = svc["desiredCount"]
        if running == desired:
            typer.echo(f"  ECS tasks: OK ({running}/{desired} running)")
            return True
        typer.echo(f"  ECS tasks: WARN ({running}/{desired} running)", err=True)
        return False
    except NoCredentialsError as e:
        typer.echo(f"  ECS tasks: FAIL ({credential_error(e, None)})", err=True)
        return False
    except ClientError as e:
        typer.echo(f"  ECS tasks: FAIL ({format_aws_error(e, None)})", err=True)
        return False


def check_cw_cpu(cluster: str, service: str, region: str) -> float | None:
    try:
        cw = boto3.client("cloudwatch", region_name=region)
        response = cw.get_metric_statistics(
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
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            typer.echo("  CW CPU: NO DATA")
            return None
        latest = max(datapoints, key=lambda d: d["Timestamp"])
        cpu = latest["Average"]
        typer.echo(f"  CW CPU: {cpu:.1f}%")
        return cpu
    except NoCredentialsError as e:
        typer.echo(f"  CW CPU: FAIL ({credential_error(e, None)})", err=True)
        return None
    except ClientError as e:
        typer.echo(f"  CW CPU: FAIL ({format_aws_error(e, None)})", err=True)
        return None


def check_cw_memory(cluster: str, service: str, region: str) -> float | None:
    try:
        cw = boto3.client("cloudwatch", region_name=region)
        response = cw.get_metric_statistics(
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
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            typer.echo("  CW Memory: NO DATA")
            return None
        latest = max(datapoints, key=lambda d: d["Timestamp"])
        mem = latest["Average"]
        typer.echo(f"  CW Memory: {mem:.1f}%")
        return mem
    except NoCredentialsError as e:
        typer.echo(f"  CW Memory: FAIL ({credential_error(e, None)})", err=True)
        return None
    except ClientError as e:
        typer.echo(f"  CW Memory: FAIL ({format_aws_error(e, None)})", err=True)
        return None


def check_recent_task_failures(cluster: str, service: str, region: str) -> list:
    try:
        ecs = boto3.client("ecs", region_name=region)
        stopped = ecs.list_tasks(cluster=cluster, serviceName=service, desiredStatus="STOPPED")
        task_arns = stopped.get("taskArns", [])
        if not task_arns:
            typer.echo("  Recent failures: NONE")
            return []
        tasks = ecs.describe_tasks(cluster=cluster, tasks=task_arns)
        failures = []
        for task in tasks.get("tasks", []):
            reason = task.get("stoppedReason", "Unknown")
            stopped_at = task.get("stoppedAt", "Unknown")
            failures.append({"reason": reason, "stopped_at": str(stopped_at)})
        if failures:
            typer.echo(f"  Recent failures: {len(failures)} task(s) stopped")
            for f in failures:
                typer.echo(f"    - {f['reason']} (at {f['stopped_at']})")
        return failures
    except NoCredentialsError as e:
        typer.echo(f"  Recent failures: FAIL ({credential_error(e, None)})", err=True)
        return []
    except ClientError as e:
        typer.echo(f"  Recent failures: FAIL ({format_aws_error(e, None)})", err=True)
        return []


@app.command()
def run(
    endpoint: str = typer.Option(..., help="Base URL of the service (e.g. http://localhost:8080)"),
    cluster: str = typer.Option("cloud-automation-cluster", help="ECS cluster name"),
    service: str = typer.Option("cloud-automation-service", help="ECS service name"),
    region: str = typer.Option("eusc-de-east-1", help="AWS region"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    typer.echo("=== API Checks ===")
    health_ok = check_health_endpoint(endpoint)
    data_ok = check_data_endpoint(endpoint)

    typer.echo("\n=== ECS Checks ===")
    tasks_ok = check_ecs_tasks(cluster, service, region)
    check_recent_task_failures(cluster, service, region)

    typer.echo("\n=== CloudWatch Metrics ===")
    check_cw_cpu(cluster, service, region)
    check_cw_memory(cluster, service, region)

    typer.echo("")
    if health_ok and data_ok and tasks_ok:
        typer.echo("All checks passed.")
    else:
        typer.echo("Some checks failed.", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
