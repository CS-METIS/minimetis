import json
from typing import Optional
import os
from dataclasses import dataclass

from keycloak.keycloak_admin import KeycloakAdmin  # type: ignore

from keycloak.exceptions import raise_error_from_response, KeycloakGetError  # type: ignore

from metis_lib import service

URL_ADMIN_CLIENT_REALM_SCOPE_MAPPINGS = (
    "admin/realms/{realm-name}/clients/{id}/scope-mappings/realm"
)


@dataclass
class Mapper:
    mapper_name: str
    mapper_property: str


class Keycloak:
    def __init__(
        self, url: str, username: str, password: str, timeout: Optional[float] = None
    ) -> None:
        service.wait_respond(url, timeout=timeout)
        self.keycloak_admin = KeycloakAdmin(
            server_url=url,
            username=username,
            password=password,
            realm_name="master",
            verify=True,
        )

    def create_realm(self, realm_name: str) -> None:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.create_realm(
            {
                "realm": realm_name,
                "displayName": realm_name,
                "enabled": True,
                "sslRequired": "ALL",
            }
        )

    def create_realm_role(self, realm_name: str, role_name: str) -> None:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        keycloak_admin.create_realm_role({"name": role_name})
        keycloak_admin.realm_name = "master"

    def create_client_role(
        self, realm_name: str, client_name: str, role_name: str
    ) -> None:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        client_id = keycloak_admin.get_client_id(client_name)
        keycloak_admin.create_client_role(
            client_role_id=client_id, payload={"name": role_name, "clientRole": True}
        )
        keycloak_admin.realm_name = "master"

    def create_user(
        self,
        realm_name: str,
        email: str,
        username: str,
        password: str,
        firstname: str = "",
        lastname: str = "",
        verify_email: bool = False,
    ) -> None:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name

        keycloak_admin.create_user(
            {
                "email": email,
                "emailVerified": verify_email,
                "firstName": firstname,
                "lastName": lastname,
                "username": username,
                "enabled": True,
                "credentials": [
                    {"type": "password", "temporary": False, "value": password}
                ],
            }
        )
        keycloak_admin.realm_name = "master"

    def assign_realm_role_to_user(
        self, realm_name: str, username: str, role_name: str
    ) -> None:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        role = keycloak_admin.get_realm_role(role_name)
        user_id = keycloak_admin.get_user_id(username)
        keycloak_admin.assign_realm_roles(user_id=user_id, client_id=None, roles=[role])
        keycloak_admin.realm_name = "master"

    def assign_client_role_to_user(self, realm_name: str, client_name: str, username: str, role_name: str):
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        client_id = keycloak_admin.get_client_id(client_name)
        role = keycloak_admin.get_client_role(client_id=client_id, role_name=role_name)
        user_id = keycloak_admin.get_user_id(username)
        keycloak_admin.assign_client_role(user_id, client_id, [role])
        keycloak_admin.realm_name = "master"

    def add_realm_role_to_client_scope(
        self, realm: str, client_name: str, role_name: str
    ) -> None:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm
        role = keycloak_admin.get_realm_role(role_name)
        client_id = keycloak_admin.get_client_id(client_name)
        params_path = {"realm-name": realm, "id": client_id}
        data_raw = keycloak_admin.raw_post(
            URL_ADMIN_CLIENT_REALM_SCOPE_MAPPINGS.format(**params_path),
            data=json.dumps([role]),
        )
        keycloak_admin.realm_name = "master"
        return raise_error_from_response(
            data_raw, KeycloakGetError, expected_codes=[204]
        )

    def create_client(
        self,
        realm_name: str,
        name: str,
        root_url: str = f"https://{os.environ.get('DOMAIN', 'localhost')}",
        redirected_uri: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        if redirected_uri is None:
            redirected_uri = f"/{name}/*"
        if base_url is None:
            base_url = f"/{name}/*"

        keycloak_admin.create_client(
            {
                "name": name,
                "clientId": name,
                "rootUrl": root_url,
                "protocol": "openid-connect",
                "fullScopeAllowed": False,
                "publicClient": False,
                "redirectUris": [redirected_uri],
                "adminUrl": "",
                "baseUrl": base_url
            }
        )
        keycloak_admin.realm_name = "master"

    def get_client_secret(self, realm_name: str, client_name: str) -> str:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        client_id = keycloak_admin.get_client_id(client_name)
        secrets = keycloak_admin.get_client_secrets(client_id)
        keycloak_admin.realm_name = "master"
        return secrets["value"]

    def get_client_id(self, realm_name: str, client_name: str) -> str:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        client_id = keycloak_admin.get_client_id(client_name)
        keycloak_admin.realm_name = "master"
        return client_id

    def add_mapper_to_client(
        self, realm_name: str, client_name: str, mapper_name: str, mapper_property: str
    ):
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        client_id = keycloak_admin.get_client_id(client_name)
        payload = {
            "name": mapper_name,
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": mapper_property,
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
            },
        }

        keycloak_admin.add_mapper_to_client(client_id=client_id, payload=payload)
        keycloak_admin.realm_name = "master"

    def get_client(self, realm_name: str, client_name: str) -> str:
        keycloak_admin = self.keycloak_admin
        keycloak_admin.refresh_token()
        keycloak_admin.realm_name = realm_name
        client_id = keycloak_admin.get_client_id(client_name)
        return keycloak_admin.get_client(client_id)
