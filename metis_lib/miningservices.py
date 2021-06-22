import time
import os
from typing import Optional

from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from metis_lib import helm, kubernetes, sh, templates
from metis_lib.keycloak import Keycloak
from metis_lib.kong import Kong
from metis_lib.utils import (
    admin_service_external_url,
    admin_service_internal_url,
    asset_path,
)


def create_client(keycloak: Keycloak, username: str, domain: str, application: Optional[str] = None):
    client_name = f"{application}-{username}"
    app_domain = ""
    if application is not None:
        app_domain = f"{application}-"
    url = f"https://{app_domain}{username}.{domain}"
    keycloak.create_client(
        "metis", client_name, root_url=url, redirected_uri="/*", base_url="/*",
    )
    # client_id = keycloak.get_client_id("metis", client_name)client_secret = keycloak.get_client_secret("metis", client_name)
    keycloak.create_client_role("metis", client_name, "user")
    keycloak.assign_client_role_to_user("metis", client_name, username, "user")
    return client_name, keycloak.get_client_secret("metis", client_name)


def create_route(
    kong: Kong,
    service_name: str,
    target_host: str,
    target_port: int,
    match_host: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
):
    kong.create_service_subdomain(
        name=service_name,
        target_host=target_host,
        target_port=target_port,
        target_protocol="http",
        match_path=None,
        match_host=match_host,
    )
    if client_id is not None:
        kong.activate_oidc_plugin(
            service_name=service_name,
            oidc_provider_url=admin_service_external_url("keycloak"),
            oidc_client_id=client_id,
            oidc_client_secret=client_secret,
        )
    kong.activate_response_transformer_plugin(
        service_name=service_name, headers_to_remove=["X-Frame-Options", "Content-Security-Policy"]
    )


def create_namespace(username: str,):
    kubernetes.create_namespace(username)


def secure_namespace(
    username: str, cpu_limit: int = 16, memory_limit: str = "64Gi", gpu_limit: int = 0, storage_limit: str = "200Gi",
):
    kubernetes.apply(templates.get("network_policy"), username)
    kubernetes.apply(
        templates.get("quota"),
        namespace=username,
        cpu=cpu_limit,
        memory=memory_limit,
        gpu=gpu_limit,
        storage=storage_limit,
    )


def install_scdf(domain: str, namespace: str, kong: Kong, keycloak: Keycloak):
    client_name, client_secret = create_client(keycloak=keycloak, domain=domain, username=namespace, application="scdf")
    # deploy SCDF
    assets = asset_path("mining_plane", "scdf")
    helm.install(
        release="scdf", chart="bitnami/spring-cloud-dataflow", namespace=namespace, values=f"{assets}/values.yml",
    )
    kubernetes.wait_pod_ready("app.kubernetes.io/component=server", namespace, timeout=10 * 60)

    @retry(stop=stop_after_delay(60), wait=wait_fixed(2))
    def get_external_address() -> str:
        return kubernetes.get_service_external_address("scdf-spring-cloud-dataflow-server", namespace)

    # import scdf built-in applications
    scdf_address = get_external_address()
    scdf_cli_jar = f"{assets}/spring-cloud-dataflow-shell-2.7.1.jar"
    scdf_cmd_tpl_file = f"{assets}/import.tpl.txt"
    scdf_cmd_file = f"{assets}/import.txt"
    templates.substitute_and_save(scdf_cmd_tpl_file, scdf_cmd_file, metis_home=os.getenv("METIS_HOME"))
    sh.run(
        f"java -jar {scdf_cli_jar} \
            --dataflow.uri=http://{scdf_address} \
            --spring.shell.commandFile={scdf_cmd_file}"
    )

    @retry(stop=stop_after_delay(60), wait=wait_fixed(2))
    def get_external_ip() -> str:
        return kubernetes.get_service_external_ip("scdf-spring-cloud-dataflow-server", namespace)

    # configure SCDF access
    scdf_ip = get_external_ip()
    scdf_name = f"scdf-{namespace}"
    create_route(
        kong=kong,
        service_name=scdf_name,
        target_host=scdf_ip,
        target_port=8080,
        match_host=f"scdf-{namespace}.{domain}",
        client_id=client_name,
        client_secret=client_secret,
    )


def install_hue(domain: str, namespace: str, kong: Kong, keycloak: Keycloak):
    # create Keycloak Hue client and Kong route
    client_id, client_secret = create_client(keycloak, namespace, domain, "hue")
    hue_external_url = f"https://hue.{namespace}.{domain}"
    keycloak_external_url = f"https://{domain}/keycloak/auth"
    # deploy HUE
    assets = asset_path("mining_plane", "hue")
    values_tpl = f"{assets}/values.tpl.yml"
    configured_values = templates.substitute(
        values_tpl,
        domain=f"hue.{namespace}.{domain}",
        realm="metis",
        oidc_client_id=client_id,
        oidc_client_secret=client_secret,
        keycloak_external_url=keycloak_external_url,
        hue_external_url=hue_external_url,
    )
    with open(f"{assets}/values.yml", "w") as values:
        values.write(configured_values)

    helm.install(
        release="hue", chart="gethue/hue --version v1.0.0", namespace=namespace, values=f"{assets}/values.yml",
    )
    kubernetes.wait_pod_ready("app=hue-postgres", namespace, timeout=30 * 60)
    kubernetes.wait_pod_ready("app=hue", namespace, timeout=30 * 60)
    # https://github.com/cloudera/hue/issues/1242
    # https://programmersought.com/article/33542024487/
    time.sleep(60)
    kubernetes.exec(
        namespace=namespace, selector="app=hue", command="/usr/share/hue/build/env/bin/hue syncdb",
    )
    kubernetes.exec(
        namespace=namespace, selector="app=hue", command="/usr/share/hue/build/env/bin/hue migrate",
    )

    kubernetes.apply(
        templates.get("loadbalancer"),
        namespace=namespace,
        service_name="hue-server",
        app_name="hue",
        port=8888,
        target_port=8888,
    )

    @retry(stop=stop_after_delay(60), wait=wait_fixed(2))
    def get_hue_external_ip() -> str:
        return kubernetes.get_service_external_ip("hue-lb", namespace)

    hue_ip = get_hue_external_ip()

    # create route
    create_route(
        kong=kong,
        service_name=client_id,
        target_host=hue_ip,
        target_port=8888,
        match_host=f"hue-{namespace}.{domain}",
        # client_id=client_id,
        # client_secret=client_secret,
    )


def install_studio(
    domain: str, namespace: str, kong: Kong, keycloak: Keycloak, firstname: str, lastname: str, email: str,
):

    # deploy studio
    assets = asset_path("mining_plane", "studio")
    private_ip = os.environ.get("PRIVATE_IP")
    tag = f"{private_ip}:5000/studio:0.2"
    kubernetes.apply(
        f"{assets}/metis-studio.yml",
        namespace=namespace,
        image_tag=tag,
        username=namespace,
        firstname=firstname,
        lastname=lastname,
        email=email,
    )

    kubernetes.wait_pod_ready("app=metis-studio", namespace, timeout=10 * 60)

    @retry(stop=stop_after_delay(60), wait=wait_fixed(2))
    def get_external_ip() -> str:
        return kubernetes.get_service_external_ip("metis-studio-service", namespace)

    studio_ip = get_external_ip()

    # configure studio access
    studio_name = f"studio-{namespace}"

    # studio_client_id = keycloak.get_client_id("metis", studio_name)
    # studio_client_secret = keycloak.get_client_secret("metis", studio_name)

    studio_jupyterlab_name = f"{studio_name}-jupyterlab"
    client_id, client_secret = create_client(
        keycloak=keycloak, domain=domain, username=namespace, application="jupyterlab"
    )
    create_route(
        kong,
        service_name=studio_jupyterlab_name,
        target_host=studio_ip,
        target_port=8080,
        match_host=f"jupyterlab-{namespace}.{domain}",
        client_id=client_id,
        client_secret=client_secret,
    )
    client_id, client_secret = create_client(
        keycloak=keycloak, domain=domain, username=namespace, application="codeserver"
    )
    studio_codeserver_name = f"{studio_name}-codeserver"
    create_route(
        kong,
        service_name=studio_codeserver_name,
        target_host=studio_ip,
        target_port=8081,
        match_host=f"codeserver-{namespace}.{domain}",
        client_id=client_id,
        client_secret=client_secret,
    )
    client_id, client_secret = create_client(
        keycloak=keycloak, domain=domain, username=namespace, application="filebrowser"
    )
    studio_filebrower_name = f"{studio_name}-filebrowser"
    create_route(
        kong,
        service_name=studio_filebrower_name,
        target_host=studio_ip,
        target_port=8082,
        match_host=f"filebrowser-{namespace}.{domain}",
        client_id=client_id,
        client_secret=client_secret,
    )
    client_id, client_secret = create_client(keycloak=keycloak, domain=domain, username=namespace, application="ungit")
    ungit_name = f"{studio_name}-ungit"
    create_route(
        kong,
        service_name=ungit_name,
        target_host=studio_ip,
        target_port=8083,
        match_host=f"ungit-{namespace}.{domain}",
        client_id=client_id,
        client_secret=client_secret,
    )


def install_ui(
    domain: str, namespace: str, kong: Kong, keycloak: Keycloak,
):

    # deploy studio
    assets = asset_path("mining_plane", "ui")
    private_ip = os.environ.get("PRIVATE_IP")
    tag = f"{private_ip}:5000/studio:0.2"
    kubernetes.apply(
        f"{assets}/metis-mining-ui.yml",
        namespace=namespace,
        image_tag=tag,
        username=namespace,
        domain=domain,
    )

    kubernetes.wait_pod_ready("app=metis-mining-ui", namespace, timeout=10 * 60)

    @retry(stop=stop_after_delay(60), wait=wait_fixed(2))
    def get_external_ip() -> str:
        return kubernetes.get_service_external_ip("metis-mining-ui-service", namespace)

    ui_ip = get_external_ip()

    # configure studio access
    ui_name = f"ui-{namespace}"
    # studio_client_id = keycloak.get_client_id("metis", studio_name)
    # studio_client_secret = keycloak.get_client_secret("metis", studio_name)

    client_id, client_secret = create_client(keycloak=keycloak, domain=domain, username=namespace)
    create_route(
        kong,
        service_name=ui_name,
        target_host=ui_ip,
        target_port=80,
        match_host=f"{namespace}.{domain}",
        client_id=client_id,
        client_secret=client_secret,
    )


def deploy(
    email: str,
    username: str,
    password: str,
    firstname: str,
    lastname: str,
    cpu_limit: int = 16,
    memory_limit: str = "64Gi",
    gpu_limit: int = 0,
    storage_limit: str = "200Gi",
):
    domain = os.environ.get("DOMAIN")
    metis_admin_password = os.environ.get("METIS_ADMIN_PASSWORD", "metis@admin01")
    kong = Kong()
    keycloak = Keycloak(
        url=f"{admin_service_internal_url('keycloak', 8080)}/auth/admin",
        username="admin",
        password=metis_admin_password,
        timeout=30,
    )
    keycloak.create_user(
        "metis", email=email, username=username, password=password, firstname=firstname, lastname=lastname,
    )

    create_namespace(username)

    # deploy scdf services
    install_scdf(domain=domain, namespace=username, kong=kong, keycloak=keycloak)
    install_studio(
        domain=domain,
        namespace=username,
        kong=kong,
        keycloak=keycloak,
        firstname=firstname,
        lastname=lastname,
        email=email,
    )
    install_ui(domain=domain, namespace=username, kong=kong, keycloak=keycloak)
    # add user to gitlab/dataminer role
    keycloak.assign_client_role_to_user("metis", "gitlab", username, "dataminer")

    # secure_namespace(username, cpu_limit, memory_limit, gpu_limit, storage_limit)
