import string
from typing import Dict, Optional
from metis_lib.sh import run
import tempfile


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
    set_options: Optional[Dict[str, str]] = None,
    **kwargs
) -> str:
    namespace_opt = ""
    if namespace:
        namespace_opt = f" -n {namespace}"
    values_opt = ""
    if values:
        tmp = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
        with open(values) as f:
            obj = f.read()
            if kwargs:
                obj = string.Template(obj).substitute(kwargs)
            tmp.write(str.encode(obj))
            tmp.close()
        values_opt = f" -f {tmp.name}"
    set_opts = ""
    if set_options:
        set_opts = f' {" ".join([f"--set {k}={v}" for k, v in set_options.items()])}'
    return run(f"helm install {release}{namespace_opt}{values_opt} {chart} --version {version}{set_opts}")
