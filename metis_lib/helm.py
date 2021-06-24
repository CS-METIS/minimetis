from typing import Dict, Optional
from metis_lib.sh import run


def add_repo(name: str, url: str) -> None:
    run(f"helm repo add {name} {url}")


def update_repo():
    run("helm repo update")


def install(
    release: str,
    chart: str,
    version: str,
    namespace: Optional[str] = None,
    values: Optional[str] = None,
    set_options: Optional[Dict[str, str]] = None
) -> str:
    namespace_opt = ""
    if namespace:
        namespace_opt = f" -n {namespace}"
    values_opt = ""
    if values:
        values_opt = f" -f {values}"
    set_opts = ""
    if set_options:
        set_opts = f' {" ".join([f"--set {k}={v}" for k, v in set_options.items()])}'
    return run(f"helm install {release}{namespace_opt}{values_opt} {chart} --version {version}{set_opts}")
