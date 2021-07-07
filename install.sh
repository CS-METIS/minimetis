# start minikube with Project Calico CNI
cat <<EOF >> tmp.json
{ 
    "insecure-registries": [
        "${PRIVATE_IP}:4443"
        ] 
}
EOF
sudo mv tmp.json /etc/docker/daemon.json
rm -f tmp.json
sudo systemctl restart docker
cat /etc/docker/daemon.json
minikube start --network-plugin=cni --cni=calico --kubernetes-version=v${KUBE_VERSION} --driver=none --insecure-registry=${PRIVATE_IP}:4443


# minikube start --network-plugin=cni --cni=calico --kubernetes-version=v${KUBE_VERSION} --driver=none 
kubectl set env daemonset/calico-node -n kube-system IP_AUTODETECTION_METHOD=interface=${PRIVATE_IF}

# Run minikube tunnel to enable Kubernetes LoadBalancer
nohup minikube tunnel > /dev/null&

# configure DNS
sudo PRIVATE_IP=${PRIVATE_IP} DOMAIN=${DOMAIN} sh -c 'echo "${PRIVATE_IP} ${DOMAIN}" >> /etc/hosts'
sudo PRIVATE_IP=${PRIVATE_IP} DOMAIN=${DOMAIN} sh -c 'echo "${PRIVATE_IP} portainer.${DOMAIN}" >> /etc/hosts'

python cli/install_admin_plane.py
python cli/install_data_plane.py

