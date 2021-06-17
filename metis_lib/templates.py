import string
from pathlib import Path
from metis_lib.utils import asset_path


def get(template_name: str) -> str:
    p = Path(asset_path("templates", ""))
    tpl = p / f"{template_name}.yml"
    if tpl.is_file():
        return str(tpl)
    tpl = p / f"{template_name}.yaml"
    if tpl.is_file():
        return str(tpl)
    raise ValueError(f"template {template_name} is found in {p}")


def substitute(template_url: str, **kwargs) -> str:
    with open(template_url) as tpl:
        content = tpl.read()
        return string.Template(content).substitute(kwargs)
