kubectl create namespace mining-plane

helm repo add gethue https://helm.gethue.com
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install scdf \
    -n mining-plane \
    -f scdf/values.yaml bitnami/spring-cloud-dataflow

kubectl wait --namespace mining-plane \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=server \
  --timeout=3600s

scdf_server_ip=$(kubectl get svc -n mining-plane scdf-spring-cloud-dataflow-server --output jsonpath='{.status.loadBalancer.ingress[0].ip}')
scdf_server_port=$(kubectl get svc -n mining-plane scdf-spring-cloud-dataflow-server --output jsonpath='{.spec.ports[0].port}')

java -jar scdf/spring-cloud-dataflow-shell-2.7.1.jar --dataflow.uri=http://${scdf_server_ip}:${scdf_server_port} --spring.shell.commandFile=scdf/import.txt

helm install hue \
    -n mining-plane \
    -f hue/values.yaml gethue/hue

kubectl expose rc hue \
    --name=hue-service --port=8888 --target-port=8888 --type=LoadBalancer -n mining-plane

kubectl wait --namespace mining-plane \
  --for=condition=ready pod \
  --selector=app=hue \
  --timeout=3600s

  