import os
import requests
from pathlib import Path
from typing import Optional, Type, TypeVar
from distutils.util import strtobool
from metis_lib import docker


def asset_path(plane: str, asset_name: str) -> str:
    p = Path(f"{os.environ.get('METIS_HOME')}/assets/{plane}/{asset_name}")
    if p.is_dir():
        return str(p)
    raise ValueError(f"asset {p} not found")


def admin_service_external_url(name: str) -> str:
    domain = os.environ.get("DOMAIN", "minimetis.dev")
    return f"https://{domain}/{name}"


def admin_service_internal_url(name: str, port: int) -> str:
    ip = docker.get_container_ip(name)
    return f"http://{ip}:{port}/{name}"


T = TypeVar("T")


def get_env(variable_type: Type[T], key: str, default: Optional[str] = None) -> T:
    if variable_type == bool:
        if type(v := os.environ.get(key, default)) == bool:
            return v
        return bool(strtobool(os.environ.get(key, default)))
    return variable_type((os.environ.get(key, default)))


def download(url: str, destination: str):
    r = requests.get(url, allow_redirects=True)
    if 200 <= r.status_code < 300:
        with open(destination, "w") as dst:
            dst.write(str(r.content))
