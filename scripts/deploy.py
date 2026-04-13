import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)

def get_container_runtime() -> str | None:
    for runtime in ('podman', 'docker'):
        if shutil.which(runtime):
            return runtime
    logger.error("Neither docker nor podman found. Install one of them.")
    return None



def find_image(image_name: str) -> bool: 
    runtime = get_container_runtime()
    if runtime:
        results = subprocess.run([runtime, 'images', '--format', '{{.Repository}}'],
        capture_output=True, text=True
        )
        if any(image_name in line for line in results.stdout.splitlines()):
            return True
    return False

def save_image(image_name: str) -> None:
    runtime = get_container_runtime()
    if not runtime:
        return
    if find_image(image_name=image_name):
        try:
            subprocess.run([runtime, 'save', '-o', f'{image_name}.tar', image_name], check=True)
        except Exception as e:
            logger.error(f"Error encountered: {e}")



