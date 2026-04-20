from datetime import datetime, timedelta
import boto3
import logging
import typer

app = typer.Typer(help="Scale ECS tasks based on CW logs for cloud-automation-platform")
logger = logging.getLogger(__name__)

SECONDS_IN_A_DAY = 86400

cloudwatch = boto3.client("cloudwatch")

response = cloudwatch.get_metric_statistics(
    Namespace = 'AWS/ECS',
    Dimensions = [
        {
            'Name' : 'app',
            "Value": "CPUUtilization"
        },
        {
            'Name': 'app',
            'Value': "MemoryUtilization"
        }
    ],
    MetricName = 'ScaleMetric',
    StartTime = datetime.now() - timedelta(days=7),
    EndTime = datetime.now(),
    Period = SECONDS_IN_A_DAY,
    Statistics = [
        'Average'
    ],
    Unit = 'Bytes'
)

