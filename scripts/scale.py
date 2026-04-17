
import logging
import typer

app = typer.Typer(help="Scale ECS tasks based on CW logs for cloud-automation-platform")
logger = logging.getLogger(__name__)