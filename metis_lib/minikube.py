from pathlib import Path
from typing import Optional
from metis_lib import sh


def build_image(dockerfile: str, tag: str, contextdir: Optional[str] = None):
    p = Path(dockerfile)
    if not p.is_file():
        raise ValueError(f"{p} is not a file")
    if contextdir is None:
        contextdir = p.parent
    sh.run(
        f"docker build {contextdir} -t {tag} -f {dockerfile}"
    )
