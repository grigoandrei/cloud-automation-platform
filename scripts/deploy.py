import subprocess
import shutil
import logging

import typer

app = typer.Typer(help="Deploy CLI for cloud-automation-platform")
logger = logging.getLogger(__name__)


def get_container_runtime() -> str | None:
    for runtime in ('podman', 'docker'):
        if shutil.which(runtime):
            return runtime
    logger.error("Neither docker nor podman found. Install one of them.")
    return None


def find_image(image_name: str, runtime: str) -> str | None:
    results = subprocess.run(
        [runtime, 'images', '--format', '{{.Repository}}'],
        capture_output=True, text=True,
    )
    for line in results.stdout.splitlines():
        if image_name in line:
            return line
    return None


@app.command()
def build(
    image_name: str = typer.Option("cloud-automation-platform", help="Image name"),
    tag: str = typer.Option("latest", help="Image tag"),
    dockerfile: str = typer.Option("docker/Dockerfile", help="Path to Dockerfile"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Build a container image."""
    pass


@app.command()
def save(
    image_name: str = typer.Option("cloud-automation-platform", help="Image name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Save a container image to a .tar file."""
    pass


@app.command()
def push(
    image_name: str = typer.Option("cloud-automation-platform", help="Image name"),
    tag: str = typer.Option("latest", help="Image tag"),
    ecr_repo: str = typer.Option("my-ecr-repo", help="ECR repository name"),
    region: str = typer.Option("eusc-de-east-1", help="AWS region"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Push a container image to ECR."""
    pass


@app.command()
def deploy(
    image_name: str = typer.Option("cloud-automation-platform", help="Image name"),
    tag: str = typer.Option("latest", help="Image tag"),
    dockerfile: str = typer.Option("docker/Dockerfile", help="Path to Dockerfile"),
    ecr_repo: str = typer.Option("my-ecr-repo", help="ECR repository name"),
    region: str = typer.Option("eusc-de-east-1", help="AWS region"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Full pipeline: build, tag, and push to ECR."""
    pass


if __name__ == "__main__":
    app()
