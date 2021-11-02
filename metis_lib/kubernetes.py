import string
import json
from typing import List, Optional
from metis_lib.sh import run, call
from metis_lib import templates
import logging


def apply(template_url: str, namespace: Optional[str] = None, **kwargs):
    if not namespace:
        namespace_opt = ""
    else:
        namespace_opt = f" -n {namespace}"
    if template_url.startswith("http://") or template_url.startswith("https://"):
        return run(f"curl -L {template_url} | kubectl {namespace_opt} apply -f -")

    with open(template_url) as tpl:
        obj = tpl.read()
        if kwargs:
            obj = string.Template(obj).substitute(kwargs)
        import tempfile

        tmp = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
        print(f"Tmp {template_url} {tmp.name}")
        tmp.write(str.encode(obj))
        tmp.close()
        run(f"kubectl apply{namespace_opt} -f {tmp.name}")


def wait_pod_ready(label: str, namespace: str = "default", timeout: int = -1) -> bool:
    if not namespace:
        namespace_opt = ""
    else:
        namespace_opt = f"-n {namespace}"
    try:
        run(f"kubectl wait {namespace_opt} --for=condition=ready pod --selector={label} --timeout={timeout}s")
        return True
    except RuntimeError:
        return False


def get_service_external_address(name: str, namespace: str = "default") -> str:
    content = call(f"kubectl get svc -n {namespace} {name} --output json")
    obj = json.loads(content)
    ip = obj["status"]["loadBalancer"]["ingress"][0]["ip"]
    port = obj["spec"]["ports"][0]["port"]
    return f"{ip}:{port}"


def get_service_external_ip(name: str, namespace: str = "default") -> str:
    content = call(f"kubectl get svc -n {namespace} {name} --output json")
    obj = json.loads(content)
    return obj["status"]["loadBalancer"]["ingress"][0]["ip"]


def get_service_external_port(name: str, namespace: str = "default") -> int:
    content = call(f"kubectl get svc -n {namespace} {name} --output json")
    obj = json.loads(content)
    return int(obj["spec"]["ports"][0]["port"])


def create_namespace(namespace: str):
    tpl = templates.get("namespace")
    apply(tpl, namespace=None, name=namespace)


def get_pod_spec(namespace: str, selector: str) -> str:
    return call(f"kubectl get pods -n {namespace} --selector={selector} -o json")


def get_pod_name(namespace: str, selector: str) -> str:
    spec = json.loads(get_pod_spec(namespace, selector))
    return spec["items"][0]["metadata"]["name"]


def delete_pod(namespace: str, selector: str):
    pod_name = get_pod_name(namespace, selector)
    run(f"kubectl delete pod {pod_name} -n {namespace}")


def exec(namespace: str, selector: str, command: str, container_name: str = None):
    pod_name = get_pod_name(namespace, selector)
    container_opts = ""
    if container_name is not None:
        container_opts = f" -c {container_name}"
    return call(f"kubectl exec -n {namespace} {pod_name}{container_opts} -- {command}")


def add_host_aliases(
    namespace: str,
    resource_name: str,
    host_ip: str,
    hostnames: List[str],
    resource_type="deployment",
):
    resource_spec_str = call(f"kubectl get {resource_type} {resource_name} -n {namespace} -o json")
    resource_spec_obj = json.loads(resource_spec_str)
    containers_spec = resource_spec_obj["spec"]["template"]["spec"]
    aliases = []
    if "hostAliases" in containers_spec:
        aliases = containers_spec["hostAliases"]
    aliases.append({"ip": host_ip, "hostnames": hostnames})
    containers_spec["hostAliases"] = aliases
    file_name = f"{namespace}-{resource_name}.json"
    with open(file_name, "w+") as f:
        f.write(json.dumps(resource_spec_obj, indent=2))
    run(f"kubectl apply -n {namespace} -f {file_name}")


def create_config_map(
    name: str,
    from_file: str,
    key_name: Optional[str] = None,
    namespace: Optional[str] = None,
):
    namespace_opt = ""
    if namespace:
        namespace_opt = f"-n {namespace} "
    key_name_opt = ""
    if key_name:
        key_name_opt = f"{key_name}="
    run(f"kubectl {namespace_opt}create configmap {name} --from-file={key_name_opt}{from_file}")


def create_secret(
    name: str,
    from_file: str,
    key_name: Optional[str] = None,
    namespace: Optional[str] = None,
):
    key_name_opt = ""
    if key_name:
        key_name_opt = f"{key_name}="
    if namespace:
        namespace_opt = f"-n {namespace} "
    run(f"kubectl create {namespace_opt}secret generic {name} --from-file={key_name_opt}{from_file}")


def delete_namespace(namespace: str):
    try:
        run(f"kubectl delete ns {namespace}")
    except RuntimeError:
        logging.info(f"The namespace {namespace} is already delete or does not exist")


def delete_pv(namespace: str):
    try:
        run(f"kubectl delete pv shared-volume-{namespace}")
    except RuntimeError:
        logging.info(f"The pv {namespace} is already delete or does not exist")
