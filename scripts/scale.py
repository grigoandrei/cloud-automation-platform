from datetime import datetime, timedelta
import boto3
import logging
import typer

app = typer.Typer(help="Scale ECS tasks based on CW logs for cloud-automation-platform")
logger = logging.getLogger(__name__)

cloudwatch = boto3.client("cloudwatch", region_name="eusc-de-east-1")

def get_cpu_utilization(cluster: str, service: str) -> float | None:
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
    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    # Get the most recent datapoint
    latest = max(datapoints, key=lambda d: d["Timestamp"])
    return latest["Average"]


