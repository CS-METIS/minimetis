import os
import shutil

from metis_lib import helm, kubernetes
from metis_lib.portainer import Portainer
from metis_lib.kong import Kong
from metis_lib.keycloak import Keycloak
from metis_lib.compose import Compose
from metis_lib.gitlab import Gitlab
from metis_lib.certificates import PKI, create_keystore
from metis_lib import docker
from metis_lib import utils


def kong_certificate(server_cert, server_key, domain, kong: Kong, private_ip: str):
    kong.wait_ready(timeout=5 * 60)
    kong.add_certificate(server_cert, server_key, [domain])
    kong.add_certificate(server_cert, server_key, [f"*.{domain}"])


def install_keycloak(metis_admin_password: str, keycloak: Keycloak, kong: Kong):
    kong.create_service("keycloak", "keycloak", 8443, protocol="https")
    keycloak.create_realm("metis")
    keycloak.create_realm_role("metis", "metis-admin")
    keycloak.create_user(
        realm_name="metis",
        email="admin@metis.eu",
        username="admin",
        password=metis_admin_password,
    )
    keycloak.assign_realm_role_to_user("metis", "admin", "metis-admin")


def install_gitlab(keycloak: Keycloak, kong: Kong):
    kong.create_service("gitlab", "gitlab", 443, protocol="https")
    keycloak.create_client("metis", "gitlab")
    keycloak.add_realm_role_to_client_scope("metis", "gitlab", "metis-admin")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="name", mapper_property="Username")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="email", mapper_property="Email")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="first_name", mapper_property="FirstName")
    keycloak.add_mapper_to_client("metis", "gitlab", mapper_name="last_name", mapper_property="LastName")


def install_konga(keycloak: Keycloak, kong: Kong):
    kong.create_service("konga", "konga", 1337, strip_path=True)
    keycloak.create_client("metis", "konga")
    keycloak.add_realm_role_to_client_scope("metis", "konga", "metis-admin")


def install_portainer(metis_admin_password: str, kong: Kong, private_ip: str):
    kong.create_service("portainer", private_ip, 9000, strip_path=True)

    portainer = Portainer(
        username="admin",
        password=metis_admin_password,
    )
    portainer_agent_address = kubernetes.get_service_external_address("portainer-agent", namespace="portainer")
    portainer.wait_ready(timeout=5 * 60)
    portainer.register_docker_endpoint("Metis control plane")
    portainer.register_kubernetes_endpoint(portainer_agent_address, "Metis cluster", timeout=10 * 60)


def create_gitlab_role_for_dataminer(
    keycloak: Keycloak,
    kong: Kong,
    compose: Compose,
    admin_assets,
    domain,
    keycloak_external_ssl_url: str,
):
    keycloak.create_client_role("metis", "gitlab", "dataminer")

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
        service_name="gitlab",
        headers_to_remove=["X-Frame-Options", "Content-Security-Policy"],
    )
    compose.up(["gitlab"])
    gitlab.wait_ready(timeout=10 * 60)
    compose.exec("gitlab", "update-ca-certificates")


def install_prometheus(monitoring_namespace: str):
    kubernetes.create_namespace(monitoring_namespace)
    helm.install(
        release="prometheus",
        chart="bitnami/kube-prometheus",
        version="6.0.1",
        namespace=monitoring_namespace,
    )


def deploy_image(private_ip: str, tag_name: str, client: str):
    tag = f"{private_ip}:4443/metis/{tag_name}:0.2"
    client_assets = utils.asset_path("mining_plane", client)
    docker.build_image(f"{client_assets}/image/Dockerfile", tag)
    docker.push(tag)


def patch_scdf_image(processor_name: str):
    scdf_assets = utils.asset_path("mining_plane", "scdf")
    tag = f"springcloudstream/{processor_name}-processor-kafka:patched"
    docker.build_image(f"{scdf_assets}/scdf_app_patched_images/{processor_name}/Dockerfile", tag)


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

    kong_certificate(
        server_cert=server_cert,
        server_key=server_key,
        domain=domain,
        kong=kong,
        private_ip=private_ip,
    )

    keycloak_ip = docker.get_container_ip("keycloak")
    keycloak_internal_url = f"http://{keycloak_ip}:8080/keycloak"
    keycloak = Keycloak(
        f"{keycloak_internal_url}/auth/admin",
        username="admin",
        password=metis_admin_password,
        timeout=5 * 60,
    )

    install_keycloak(metis_admin_password=metis_admin_password, keycloak=keycloak, kong=kong)

    install_gitlab(keycloak=keycloak, kong=kong)

    install_konga(keycloak=keycloak, kong=kong)

    install_portainer(metis_admin_password=metis_admin_password, kong=kong, private_ip=private_ip)

    create_gitlab_role_for_dataminer(
        keycloak=keycloak,
        kong=kong,
        compose=compose,
        admin_assets=admin_assets,
        domain=domain,
        keycloak_external_ssl_url=keycloak_external_ssl_url,
    )

    install_prometheus("admin-plane")

    deploy_image(private_ip=private_ip, tag_name="studio", client="studio")
    deploy_image(private_ip=private_ip, tag_name="miningui", client="ui")

    patch_scdf_image("image-recognition")
    patch_scdf_image("object-detection")
