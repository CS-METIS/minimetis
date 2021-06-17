import json
import os
from keycloak import KeycloakAdmin
from keycloak.exceptions import raise_error_from_response, KeycloakGetError

import requests

password = os.environ.get("METIS_ADMIN_PASSWORD", "metis@admin01")
root_url = "http://localhost"
kong_url = "http://localhost:8001"
keycloak_url = "http://localhost/keycloak/auth/"

URL_ADMIN_CLIENT_REALM_SCOPE_MAPPINGS = (
    "admin/realms/{realm-name}/clients/{id}/scope-mappings/realm"
)


def add_realm_level_roles_to_client_scope(keycloak_admin, client_id, payload):
    params_path = {"realm-name": keycloak_admin.realm_name, "id": client_id}
    data_raw = keycloak_admin.raw_post(
        URL_ADMIN_CLIENT_REALM_SCOPE_MAPPINGS.format(**params_path),
        data=json.dumps(payload),
    )
    return raise_error_from_response(data_raw, KeycloakGetError, expected_codes=[204])


def create_kong_service(name: str, host: str, port: int, strip_path: bool = False):
    payload = {
        "name": name,
        "host": host,
        "port": port,
        "protocol": "http",
    }
    resp = requests.post(f"{kong_url}/services", json=payload)
    service = resp.json()
    if resp.status_code < 200 or resp.status_code >= 300:
        raise RuntimeError(service)
    payload = {
        "service": {"id": service["id"]},
        "protocols": ["http"],
        "paths": [f"/{host}"],
        "strip_path": strip_path,
    }
    resp = requests.post(f"{kong_url}/routes", json=payload)
    route = resp.json()
    if resp.status_code < 200 or resp.status_code >= 300:
        raise RuntimeError(route)


def get_kong_service_id(kong_url, service_name):
    resp = requests.get(f"{kong_url}/services/{service_name}")
    service = resp.json()
    if resp.status_code < 200 or resp.status_code >= 300:
        raise RuntimeError(service)
    return service["id"]


def activate_kong_service_oidc_plugin(kong_url, kong_service_name, keycloak_client_id, keycloak_client_secret):
    payload = {
        "name": "oidc",
        "config.client_id": keycloak_client_id,
        "config.client_secret": keycloak_client_secret,
        "config.bearer_only": "no",
        "config.realm": "metis",
        "config.introspection_endpoint": "http://keycloak:8080/keycloak/auth/realms/metis/protocol/openid-connect/token/introspect",
        "config.discovery": "http://keycloak:8080/keycloak/auth/realms/metis/.well-known/openid-configuration",
    }
    service_id = get_kong_service_id(kong_url, kong_service_name)
    resp = requests.post(f"{kong_url}/services/{service_id}/plugins", data=payload)
    service = resp.json()
    if resp.status_code < 200 or resp.status_code >= 300:
        raise RuntimeError(service)


def keycloak_configure_realm(realm_name: str) -> KeycloakAdmin:

    keycloak_admin = KeycloakAdmin(
        server_url=keycloak_url,
        username="admin",
        password=password,
        realm_name="master",
        verify=True,
    )
    keycloak_admin.create_realm(
        {"realm": "metis", "displayName": "metis", "enabled": True}
    )

    keycloak_admin.realm_name = "metis"
    keycloak_admin.create_realm_role({"name": "metis-admin"})

    role = keycloak_admin.get_realm_role("metis-admin")

    keycloak_admin.create_user(
        {
            "email": "admin@metis.com",
            "emailVerified": False,
            "firstName": "Doe",
            "lastName": "John",
            "username": "metis-admin",
            "enabled": True,
            "credentials": [
                {"type": "password", "temporary": False, "value": password}
            ],
            "realmRoles": ["metis-admin"],
        }
    )
    user_id = keycloak_admin.get_user_id("metis-admin")
    keycloak_admin.assign_realm_roles(user_id=user_id, client_id=None, roles=[role])
    return keycloak_admin


def keycloak_create_client(keycloak_admin: KeycloakAdmin, name: str) -> str:
    role = keycloak_admin.get_realm_role("metis-admin")

    keycloak_admin.create_client(
        {
            "name": "konga",
            "clientId": "konga",
            "rootUrl": root_url,
            "protocol": "openid-connect",
            "baseUrl": "/konga/",
            "fullScopeAllowed": False,
            "publicClient": False,
            "redirectUris": ["/konga/*"],
        }
    )
    client_id = keycloak_admin.get_client_id("konga")

    add_realm_level_roles_to_client_scope(keycloak_admin, client_id, [role])

    secrets = keycloak_admin.get_client_secrets(client_id)
    return secrets['value']


if __name__ == '__main__':
    keycloak_admin = keycloak_configure_realm("metis")
    create_kong_service("Keycloak", "keycloak", 8080, strip_path=False)

    secrets = keycloak_create_client('gitlab')
    create_kong_service("Gitlab", "gitlab", 80, strip_path=False)
    activate_kong_service_oidc_plugin(kong_url, "Gitlab", 'gitlab', secrets["value"])

    create_kong_service("Konga", "konga", 1337, strip_path=True)
    secrets = keycloak_create_client('konga')
    activate_kong_service_oidc_plugin(kong_url, 'Konga', 'konga', secrets["value"])

    secrets = keycloak_create_client('minio')
    create_kong_service("Minio", "minio", 9000, strip_path=False)
    activate_kong_service_oidc_plugin(kong_url, "Minio", secrets["value"])
