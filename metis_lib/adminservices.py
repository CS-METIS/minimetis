import os
import shutil

from metis_lib import kubernetes
from metis_lib.portainer import Portainer
from metis_lib.kong import Kong
from metis_lib.keycloak import Keycloak
from metis_lib.compose import Compose
from metis_lib.gitlab import Gitlab
from metis_lib.certificates import PKI, create_keystore
from metis_lib import docker
from metis_lib import utils


def deploy():
    metis_home = os.environ.get("METIS_HOME")
    private_ip = os.environ.get("PRIVATE_IP")
    admin_assets = f"{metis_home}/assets/admin-plane"
    domain = os.environ.get("DOMAIN", "minimetis.dev")

    keycloak_external_ssl_url = f"https://{domain}/keycloak"
    metis_admin_password = os.environ.get("METIS_ADMIN_PASSWORD", "metis@admin01")
    kubernetes.apply(
        namespace="portainer",
        template_url="https://downloads.portainer.io/portainer-agent-k8s-lb.yaml",
    )

    server_key = "pki/server.key"
    server_cert = "pki/server.pem"
    ca_cert = "pki/CA Root Minimetis.pem"
    if not os.path.exists("pki"):
        os.mkdir("pki")
        pki = PKI()
        ca_cert, ca_key = pki.create_ca_cert()
        server_cert, server_key = pki.create_server_cert(ca_cert_file=ca_cert, ca_key_file=ca_key)

    create_keystore(
        keypath=server_key,
        certpath=server_cert,
        password=metis_admin_password,
        output=f"{admin_assets}/keycloak/kc.pkcs12",
    )
    os.chmod(f"{admin_assets}/keycloak/kc.pkcs12", 0o0666)
    shutil.copy(ca_cert, f"{admin_assets}/gitlab/CA.crt")
    shutil.copy(server_cert, f"{admin_assets}/gitlab/ssl/{domain}.crt")
    shutil.copy(server_key, f"{admin_assets}/gitlab/ssl/{domain}.key")

    compose = Compose(f"{admin_assets}/docker-compose.yml")
    compose.up(["kong", "konga", "keycloak", "portainer", "registry"])
    kubernetes.wait_pod_ready(namespace="portainer", label="app=portainer-agent", timeout=10 * 60)

    kong = Kong()
    kong.wait_ready(timeout=5 * 60)
    kong.add_certificate(server_cert, server_key, [domain])
    kong.add_certificate(server_cert, server_key, [f"*.{domain}"])
    kong.create_service("keycloak", "keycloak", 8443, protocol="https")
    kong.create_service("gitlab", "gitlab", 443, protocol="https")
    kong.create_service("konga", "konga", 1337, strip_path=True)
    kong.create_service("portainer", private_ip, 9000, strip_path=True)
    # kong.create_service("minio", "minio", 9000)

    keycloak_ip = docker.get_container_ip("keycloak")
    keycloak_internal_url = f"http://{keycloak_ip}:8080/keycloak"
    keycloak = Keycloak(
        f"{keycloak_internal_url}/auth/admin",
        username="admin",
        password=metis_admin_password,
        timeout=5 * 60,
    )
    keycloak.create_realm("metis")
    keycloak.create_realm_role("metis", "metis-admin")
    keycloak.create_user(
        realm_name="metis",
        email="admin@metis.eu",
        username="admin",
        password=metis_admin_password,
    )
    keycloak.assign_realm_role_to_user("metis", "admin", "metis-admin")

    # Configure gitlab authentication
    keycloak.create_client("metis", "gitlab")
    keycloak.add_realm_role_to_client_scope("metis", "gitlab", "metis-admin")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="name", mapper_property="Username")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="email", mapper_property="Email")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="first_name", mapper_property="FirstName")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="last_name", mapper_property="LastName")

    # Configure konga authentication
    keycloak.create_client("metis", "konga")
    keycloak.add_realm_role_to_client_scope("metis", "konga", "metis-admin")
    kong.activate_oidc_plugin(
        service_name="konga",
        oidc_provider_url=keycloak_external_ssl_url,
        oidc_client_id="konga",
        oidc_client_secret=keycloak.get_client_secret("metis", "konga"),
    )

    # Create gitlab role for dataminer
    keycloak.create_client_role("metis", "gitlab", "dataminer")

    portainer = Portainer(
        username="admin",
        password=metis_admin_password,
    )
    portainer_agent_address = kubernetes.get_service_external_address("portainer-agent", namespace="portainer")
    portainer.wait_ready(timeout=5 * 60)
    portainer.register_docker_endpoint("Metis control plane")
    portainer.register_kubernetes_endpoint(portainer_agent_address, "Metis cluster", timeout=10 * 60)
    gitlab = Gitlab(
        gitlab_url=f"https://{domain}/gitlab/",
        gitlab_rb_path=f"{admin_assets}/gitlab/gitlab.rb",
    )

    gitlab.configure_omiauth(
        oidc_client_id="gitlab",  # keycloak.get_client_id("metis", "gitlab"),
        oidc_client_secret=keycloak.get_client_secret("metis", "gitlab"),
        issuer_url=f"{keycloak_external_ssl_url}/auth/realms/metis",
    )
    kong.activate_response_transformer_plugin(
        service_name="gitlab", headers_to_remove=["X-Frame-Options", "Content-Security-Policy"]
    )
    # compose.up(["gitlab", "minio"])
    compose.up(["gitlab"])
    gitlab.wait_ready(timeout=10 * 60)
    compose.exec("gitlab", "update-ca-certificates")

    tag = f"{private_ip}:4443/metis/studio:0.2"
    studio_assets = utils.asset_path("mining_plane", "studio")
    docker.build_image(f"{studio_assets}/image/Dockerfile", tag)
    docker.push(tag)

    tag = f"{private_ip}:4443/metis/miningui:0.2"
    ui_assets = utils.asset_path("mining_plane", "ui")
    docker.build_image(f"{ui_assets}/image/Dockerfile", tag)
    docker.push(tag)

    scdf_assets = utils.asset_path("mining_plane", "scdf")
    tag = "springcloudstream/image-recognition-processor-kafka:patched"
    docker.build_image(f"{scdf_assets}/scdf_app_patched_images/image-recognition/Dockerfile", tag)
    tag = "springcloudstream/object-detection-processor-kafka:patched"
    docker.build_image(f"{scdf_assets}/scdf_app_patched_images/object-detection/Dockerfile", tag)
