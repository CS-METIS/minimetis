from urllib.parse import urlparse
import os

from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerAlreadyExistsError
from metis_lib import kubernetes
from metis_lib import helm
from metis_lib import utils
from metis_lib import templates
from metis_lib import docker
from metis_lib.kong import Kong

# # from metis_lib.keycloak import Keycloak
# # from metis_lib.utils import admin_service_internal_url
# from metis_lib import kubernetes


def install_alluxio(namespace: str) -> str:
    asset_path = utils.asset_path("data_plane", "alluxio")
    storage_provider = utils.get_env(str, "STORAGE_PROVIDER")
    storage_key = utils.get_env(str, "STORAGE_ACCESS_KEY")
    storage_secret = utils.get_env(str, "STORAGE_SECRET_KEY")
    storage_endpoint = utils.get_env(str, "STORAGE_ENDPOINT")
    storage_region = utils.get_env(str, "STORAGE_REGION")
    storage_bucket = utils.get_env(str, "STORAGE_BUCKET")

    enpoint_url = urlparse(storage_endpoint)
    bucket_url = urlparse(storage_bucket)
    bucket_name = bucket_url.netloc

    StorageDriver = get_driver(storage_provider)

    storage = StorageDriver(
        key=storage_key, secret=storage_secret, host=enpoint_url.hostname, port=enpoint_url.port, region=storage_region
    )
    try:
        storage.create_container(container_name=bucket_name)
    except ContainerAlreadyExistsError:
        print(f"bucket {storage_bucket} already exists")
        # c = storage.get_container(container_name=bucket_name)
        # storage.delete_container(c)
        # storage.create_container(container_name=bucket_name)

    values_tpl = f"{asset_path}/values.tpl.yml"
    configured_values = templates.substitute(
        values_tpl,
        bucket=storage_bucket,
        endpoint=storage_endpoint,
        access_key=storage_key,
        secret_key=storage_secret,
        region=storage_region,
        disable_dns=utils.get_env(bool, "STORAGE_DISABLE_DNS", False),
        inherit_acl=utils.get_env(bool, "STORAGE_INHERIT_ACL", True),
    )

    with open(f"{asset_path}/values.yml", "w") as values:
        values.write(configured_values)

    helm.install(
        release="alluxio", chart="alluxio-charts/alluxio", namespace=namespace, values=f"{asset_path}/values.yml"
    )
    kubernetes.wait_pod_ready("app=alluxio", "data-plane", 5 * 60)
    opts = kubernetes.exec(
        "data-plane", "role=alluxio-master", "/bin/bash -c 'echo ${ALLUXIO_JAVA_OPTS}'", container_name="alluxio-master"
    )
    print(opts)


def install_hive_metastore(namespace: str, alluxio_java_options: str):
    asset_path = utils.asset_path("data_plane", "hive")
    docker.build_image(f"{asset_path}/image/Dockerfile", "metis/hive:latest")
    values = templates.substitute(
        f"{asset_path}/chart/hive-metastore/values.tpl.yaml", alluxio_java_options=alluxio_java_options
    )
    with open(f"{asset_path}/chart/hive-metastore/values.yaml") as f:
        f.write(values)
    helm.install(
        release="hive-metastore",
        chart=f"{asset_path}/chart/hive-metastore",
        namespace=namespace,
        values=f"{asset_path}/chart/hive-metastore/values.yaml",
    )


def install_trino(namespace: str):
    asset_path = utils.asset_path("data_plane", "trino")
    docker.build_image(f"{asset_path}/image/Dockerfile", "metis/trino:latest")
    helm.install(
        release="trino",
        chart=f"{asset_path}/chart/trino",
        namespace=namespace,
        values=f"{asset_path}/chart/trino/values.yaml",
    )


def install_orientdb(namespace: str, domain: str, kong: Kong):
    asset_path = utils.asset_path("data_plane", "orientdb")
    helm.install(
        release="orientdb", chart=f"{asset_path}/chart", namespace=namespace, values=f"{asset_path}/chart/values.yaml",
    )

    @retry(stop=stop_after_delay(3 * 60), wait=wait_fixed(2))
    def get_orient_external_ip() -> str:
        return kubernetes.get_service_external_ip("orientdb-service", namespace)

    orientdb_ip = get_orient_external_ip()
    kong.create_service_subdomain(
        name="orientdb",
        target_host=orientdb_ip,
        target_port=2480,
        target_protocol="http",
        match_host=f"orientdb.{domain}",
        match_path=None,
    )


def install(namespace: str):
    kubernetes.create_namespace(namespace)

    kong = Kong()

    domain = os.environ.get("DOMAIN")
    install_orientdb(namespace=namespace, domain=domain, kong=kong)
    # # metis_admin_password = os.environ.get("METIS_ADMIN_PASSWORD", "metis@admin01")
    # # keycloak = Keycloak(
    # #     url=f"{admin_service_internal_url('keycloak', 8080)}/auth/admin",
    # #     username="admin",
    # #     password=metis_admin_password,
    # #     timeout=30,
    # # )
    # # keycloak.create_user(
    # #     "metis", email=email, username=username, password=password, firstname=firstname, lastname=lastname,
    # # )

    # kubernetes.create_namespace(namespace)
    # install_alluxio(namespace)
    # install_hive_metastore(namespace)

    # # install_trino(namespace)

    # # kubernetes.wait_pod_ready("app=trino", namespace, timeout=10 * 60)

    # # @retry(stop=stop_after_delay(60), wait=wait_fixed(2))
    # # def get_external_ip() -> str:
    # #     return kubernetes.get_service_external_ip("trino", namespace)

    # # trino_host = get_external_ip()

    # # # kong.create_service("TrinoUI", host=trino_host, port=8080, path="trino", strip_path=True, protocol="http")
    # # kong.create_service_subdomain(
    # #     name="trino-ui",
    # #     target_host=trino_host,
    # #     target_port=8080,
    # #     target_protocol="http",
    # #     match_host=f"trinoui.{domain}",
    # #     match_path=None,
    # # )
