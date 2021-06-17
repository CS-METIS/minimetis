from typing import Optional
from metis_lib.sh import run


def add_repo(name: str, url: str) -> None:
    run(f"helm repo add {name} {url}")


def update_repo():
    run("helm repo update")


def install(
    release: str,
    chart: str,
    namespace: Optional[str] = None,
    values: Optional[str] = None,
) -> str:
    namespace_opt = ""
    if namespace:
        namespace_opt = f" -n {namespace}"
    values_opt = ""
    if values:
        values_opt = f" -f {values}"
    return run(f"helm install {release}{namespace_opt}{values_opt} {chart}")
