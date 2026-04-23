from datetime import datetime, timedelta
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


