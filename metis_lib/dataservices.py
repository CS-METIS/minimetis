import os

from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

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
    helm.install(release="fluid", chart=f"{asset_path}/fluid-0.5.0.tgz", version="0.5.0")


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
        release="orientdb",
        chart=f"{asset_path}/orientdb-helm",
        version="0.1.0",
        namespace=namespace,
        values=f"{asset_path}/values.yml",
        set_options={"namespace": namespace},
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
    # asset_path = utils.asset_path("data_plane", "shared_volume")

    # shared_storage_size = int(os.getenv("SHARED_STORAGE_SIZE"))
    # # shared_storage_class = os.getenv("SHARED_STORAGE_CLASS")
    # if shared_storage_size > 0:
    #     templates.substitute_and_save(
    #         template_url=f"{asset_path}/pv.tpl.yml",
    #         destination_file=f"{asset_path}/pv.yml",
    #         size=shared_storage_size,
    #         # storage_class=shared_storage_class,
    #     )
    #     kubernetes.apply(f"{asset_path}/pv.yml")
