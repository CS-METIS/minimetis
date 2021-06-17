# Start minikube with Projetc Calico CNI
minikube start --network-plugin=cni --cni=calico --kubernetes-version v1.18.16 --driver=none

# Run minkube tunnel to enable Kubernetes LoadBalancer
nohup minikube tunnel > /dev/null&

# add DNS entry to join admin services from K8S
kubectl apply -n kube-system -f core-dns.yaml
kubectl delete pod -n kube-system -l k8s-app=kube-dns
