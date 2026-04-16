import subprocess
import shutil
import logging
from pathlib import Path
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
    path_to_save: str = typer.Option(".", help="Path for where to save the image, defaults to the current directory")
):
    """Build a container image."""
    path = Path(dockerfile)
    runtime = get_container_runtime()
    if not runtime:
        return
    
    if not path.exists():
        logger.error("Docker file not found! Please specify the path to the Dockerfile")
        return
    
    logger.info("Docker file found...")

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if dry_run:
        typer.echo(f"[dry-run] would run: {runtime} build -f {path} -t {image_name}:{tag} {path_to_save}")
        return

    typer.echo(f"Building {image_name}:{tag}...")
    result = subprocess.run(
        [runtime, 'build', '-f', str(path), '-t', f'{image_name}:{tag}', path_to_save],
    )
    if result.returncode != 0:
        typer.echo("Build failed.", err=True)
        raise typer.Exit(1)
    typer.echo("Build complete.")


@app.command()
def save(
    image_name: str = typer.Option("cloud-automation-platform", help="Image name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    runtime = get_container_runtime()
    if not runtime:
        raise typer.Exit(1)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    full_name = find_image(image_name, runtime)
    if not full_name:
        logger.error("Image does not exist!")
        raise typer.Exit(1)

    if dry_run:
        typer.echo(f"[dry-run] would run: {runtime} save -o {image_name}.tar {full_name}")
        return

    typer.echo(f"Saving {full_name}...")
    result = subprocess.run(
        [runtime, 'save', '-o', f'{image_name}.tar', full_name],
    )
    if result.returncode != 0:
        typer.echo("Save failed.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Saved to {image_name}.tar")



@app.command()
def push(
    image_name: str = typer.Option("cloud-automation-platform", help="Image name"),
    tag: str = typer.Option("latest", help="Image tag"),
    ecr_repo: str = typer.Option("my-ecr-repo", help="ECR repository name"),
    region: str = typer.Option("eusc-de-east-1", help="AWS region"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    accountId: str = typer.Option(None, help="Your AWS account ID (auto-detected if not provided)")
):
    # Before starting checks
    if not shutil.which("aws"):
        logger.error("AWS CLI is not installed. Please install AWS CLI.")
        raise typer.Exit(1)
    
    runtime = get_container_runtime()
    if not runtime:
        raise typer.Exit(1)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    full_name = find_image(image_name, runtime)
    if not full_name:
        logger.error("Image does not exist!")
        raise typer.Exit(1)

    # Auto-detect account ID if not provided
    if not accountId:
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text'],
            capture_output=True, text=True,
        )
        accountId = result.stdout.strip()
        if not accountId:
            typer.echo("Failed to get AWS account ID. Pass --account-id or check credentials.", err=True)
            raise typer.Exit(1)

    ecr_domain = f"{accountId}.dkr.ecr.{region}.amazonaws.eu"
    full_tag = f"{ecr_domain}/{ecr_repo}:{tag}"

    if dry_run:
        typer.echo(f"[dry-run] aws ecr get-login-password --region {region} | {runtime} login --username AWS --password-stdin {ecr_domain}")
        typer.echo(f"[dry-run] {runtime} tag {full_name} {full_tag}")
        typer.echo(f"[dry-run] {runtime} push {full_tag}")
        return

    # Login
    typer.echo("Logging in to ECR...")
    login = subprocess.run(
        f"aws ecr get-login-password --region {region} | {runtime} login --username AWS --password-stdin {ecr_domain}",
        shell=True,
    )
    if login.returncode != 0:
        typer.echo("ECR login failed.", err=True)
        raise typer.Exit(1)

    # Tag
    typer.echo(f"Tagging {full_name} as {full_tag}...")
    tagging = subprocess.run([runtime, 'tag', full_name, full_tag])
    if tagging.returncode != 0:
        typer.echo("Tagging failed.", err=True)
        raise typer.Exit(1)

    # Push
    typer.echo("Pushing...")
    push_result = subprocess.run([runtime, 'push', full_tag])
    if push_result.returncode != 0:
        typer.echo("Push failed.", err=True)
        raise typer.Exit(1)
    
    typer.echo("Push complete.")

    
    


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
