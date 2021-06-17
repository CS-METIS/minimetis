from typing import Optional
from metis_lib import sh
import json
from pathlib import Path


def build_image(dockerfile: str, tag: str, contextdir: Optional[str] = None):
    p = Path(dockerfile)
    if not p.is_file():
        raise ValueError(f"{p} is not a file")
    if contextdir is None:
        contextdir = p.parent
    sh.run(
        f"docker build {contextdir} -t {tag} -f {dockerfile}"
    )


def get_container_ip(container: str) -> str:
    content = sh.call(f"docker inspect {container}")
    obj = json.loads(content)
    networks = obj[0]["NetworkSettings"]["Networks"]
    for network in networks:
        return networks[network]["IPAddress"]
    raise ValueError(f"container {container} ip not found")
