from typing import Optional
import requests
from metis_lib import service


class Portainer:
    def __init__(self, username: str, password: str, portainer_url: str = "http://localhost:9000") -> None:
        self.username = username
        self.password = password
        self.portainer_url = portainer_url

    def _wait_agent_ready(self, agent_address: str, timeout: Optional[float] = None):
        service.wait_respond(f"https://{agent_address}/ping", timeout=timeout)

    def wait_ready(self, timeout: Optional[float] = None):
        service.wait_respond(self.portainer_url, timeout=timeout)

    def get_token(self):
        payload = {"Username": self.username, "Password": self.password}
        resp = requests.post(f"{self.portainer_url}/api/auth", json=payload)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)
        return resp.json()["jwt"]

    def register_docker_endpoint(self, name: str):
        payload = {"Name": name, "EndpointCreationType": 1}
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        resp = requests.post(self.portainer_url, json=payload, headers=headers)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)

    def register_kubernetes_endpoint(
        self, agent_address: str, name: str, timeout: Optional[float] = None
    ):
        self._wait_agent_ready(agent_address, timeout=timeout)
        payload = {
            "Name": name,
            "EndpointCreationType": 2,
            "URL": f"tcp://{agent_address}",
            "TLSSkipVerify": True,
            "TLS": True,
            "TLSSkipClientVerify": True,
        }
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        resp = requests.post(self.portainer_url, json=payload, headers=headers)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)
