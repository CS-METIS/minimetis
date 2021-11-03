from typing import Any, Dict, List, Optional
import os
import requests
from metis_lib import service
import logging


class Kong:
    def __init__(self, kong_url: str = f"http://{os.environ.get('DOMAIN', 'localhost')}:8001") -> None:
        self.kong_url = kong_url

    def wait_ready(self, timeout: Optional[float] = None):
        service.wait_respond(self.kong_url, timeout=timeout)

    def create_service_subdomain(
        self,
        name: str,
        target_host: str,
        target_port: int,
        target_protocol: str,
        match_host: str,
        match_path: str,
        strip_path: bool = False,
    ):
        payload = {
            "name": name,
            "host": target_host,
            "port": target_port,
            "protocol": target_protocol,
        }

        resp = requests.post(f"{self.kong_url}/services", json=payload)
        service = resp.json()
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(service)

        payload = {
            "service": {"id": service["id"]},
            "protocols": ["https"],
            "strip_path": strip_path,
            "preserve_host": True,
        }
        methods = []
        if match_host:
            payload["hosts"] = [match_host]
            methods.append("hosts")
        if match_path:
            payload["paths"] = [match_path]
            methods.append("paths")

        resp = requests.post(f"{self.kong_url}/routes", json=payload)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)

    def create_service(
        self,
        name: str,
        host: str,
        port: int,
        path: Optional[str] = None,
        strip_path: bool = False,
        protocol: str = "http",
    ) -> None:
        payload = {
            "name": name,
            "host": host,
            "port": port,
            "protocol": protocol,
        }
        resp = requests.post(f"{self.kong_url}/services", json=payload)
        service = resp.json()
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(service)
        if not path:
            path = name
        payload = {
            "service": {"id": service["id"]},
            "protocols": ["https"],
            "paths": [f"/{path}"],
            "strip_path": strip_path,
        }
        resp = requests.post(f"{self.kong_url}/routes", json=payload)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)

    def get_service_id(self, service_name: str) -> str:
        resp = requests.get(f"{self.kong_url}/services/{service_name}")
        print(
            f"{self.kong_url}/services/{service_name}",
            requests.get(f"{self.kong_url}/services/{service_name}"),
        )
        service = resp.json()
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(service)
        return service["id"]

    def activate_oidc_plugin(
        self,
        service_name: str,
        oidc_provider_url: str,
        oidc_client_id: str,
        oidc_client_secret: str,
        redirect_uri_path: str = None,
    ) -> None:
        payload = {
            "name": "oidc",
            "config.client_id": oidc_client_id,
            "config.client_secret": oidc_client_secret,
            "config.bearer_only": "no",
            "config.realm": "metis",
            "config.introspection_endpoint":
                f"{oidc_provider_url}/auth/realms/metis/protocol/openid-connect/token/introspect",
            "config.discovery": f"{oidc_provider_url}/auth/realms/metis/.well-known/openid-configuration",
            "config.session_secret": "bXkgc2Vzc2lvbiBzZWNyZXQ=",
        }
        if redirect_uri_path:
            payload["config.redirect_uri_path"] = redirect_uri_path
        service_id = self.get_service_id(service_name)
        resp = requests.post(f"{self.kong_url}/services/{service_id}/plugins", data=payload)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)

    def activate_response_transformer_plugin(
        self,
        service_name: str,
        headers_to_remove: List[str],
    ) -> None:
        payload = [("name", "response-transformer")]
        for header in headers_to_remove:
            payload.append(("config.remove.headers", header))
        service_id = self.get_service_id(service_name)
        resp = requests.post(f"{self.kong_url}/services/{service_id}/plugins", data=payload)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)

    def add_certificate(self, certificate_file: str, private_key_file: str, domains: List[str]) -> str:
        with open(certificate_file) as f:
            cert = f.read()
        with open(private_key_file) as f:
            key = f.read()
        payload: Dict[str, Any] = {"cert": cert, "key": key, "snis": ",".join(domains)}
        resp = requests.post(f"{self.kong_url}/certificates", data=payload)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(resp.text)
        cert_id = resp.json()["id"]
        for domain in domains:
            payload = {"name": domain, "certificate": {"id": cert_id}}
            resp = requests.post(f"{self.kong_url}/certificates/{cert_id}/snis", data=payload)
            if resp.status_code < 200 or resp.status_code >= 300:
                raise RuntimeError(resp.text)
        return cert_id

    def delete_routes(self, routes_id: str):
        try:
            requests.delete(f"{self.kong_url}/routes/{routes_id}")
        except None:
            print(f"the routes :{routes_id} does not exist or has already been deleted")

    def get_route_id(self, service_name: str) -> Optional[str]:
        try:
            resp = requests.get(f"{self.kong_url}/services/{service_name}/routes")
            service = resp.json()
            if resp.status_code < 200 or resp.status_code >= 300:
                logging.warning(f"enable to retrieve the route_id of {service_name} because of ")
                return None
            return service["data"][0]["id"]
        except TypeError:
            logging.warning(f"the route for {service_name} does not exist")
        except RuntimeError:
            logging.warning(f"the route for {service_name} does not exist")

    def delete_service(self, service_name: str):
        try:
            requests.delete(f"{self.kong_url}/services/{service_name}")
        except None:
            logging.warning(f"the services :{service_name} does not exist or has already been deleted")
