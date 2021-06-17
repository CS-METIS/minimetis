from typing import Optional, List
from pathlib import Path
from metis_lib import sh


class Compose:
    def __init__(self, file: str) -> None:
        self.file = file

    def build(self):
        sh.run(f"docker-compose --file {self.file} build")

    def stop(self):
        sh.run(f"docker-compose --file {self.file} stop")

    def rm(self, rm_volumes: bool = False, force: bool = True):
        v_opt = ""
        if rm_volumes:
            v_opt = " -v"
        f_opt = ""
        if f_opt:
            f_opt = " -f"
        sh.run(f"docker-compose --file {self.file} rm{f_opt}{v_opt}")

    def up(self, services: Optional[List[str]]):
        p = Path(self.file)
        if not services:
            sh.run(f"cd {p.parent} && docker-compose --file {p.name} up -d --remove-orphans")
        else:
            sh.run(f"cd {p.parent} && docker-compose --file {p.name} up -d --remove-orphans {' '.join(services)}")

    def exec(self, container: str, cmd: str):
        sh.run(f"docker-compose --file {self.file} exec {container} {cmd}")
