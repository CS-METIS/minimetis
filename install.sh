# # start minikube with Project Calico CNI
minikube start --network-plugin=cni --cni=calico --kubernetes-version=v${KUBE_VERSION} --driver=none --insecure-registry=registry.${DOMAIN}:4443


# configure calico to bind only an internal interface
kubectl set env daemonset/calico-node -n kube-system IP_AUTODETECTION_METHOD=interface=${PRIVATE_IF}

# Run minikube tunnel to enable Kubernetes LoadBalancer
nohup minikube tunnel > /dev/null&

# configure DNS

if ! grep -Fxq '# MINIMETIS HOSTS CONFIGURATION' /etc/hosts;
then
    sudo sh -c 'echo "# MINIMETIS HOSTS CONFIGURATION" >> /etc/hosts'
    sudo PRIVATE_IP=${PRIVATE_IP} DOMAIN=${DOMAIN} sh -c 'echo "${PRIVATE_IP} ${DOMAIN}" >> /etc/hosts'
    sudo PRIVATE_IP=${PRIVATE_IP} DOMAIN=${DOMAIN} sh -c 'echo "${PRIVATE_IP} portainer.${DOMAIN}" >> /etc/hosts'
    sudo PRIVATE_IP=${PRIVATE_IP} DOMAIN=${DOMAIN} sh -c 'echo "${PRIVATE_IP} registry" >> /etc/hosts'
    sudo PRIVATE_IP=${PRIVATE_IP} DOMAIN=${DOMAIN} sh -c 'echo "${PRIVATE_IP} registry.${DOMAIN}" >> /etc/hosts'
else
    echo "minimetis hosts already configured"
fi

python cli/install_admin_plane.py
mkdir -p ~/.minikube/files/etc/ssl/certs
cp "pki/CA Root Minimetis.pem" ~/.minikube/files/etc/ssl/certs/root.crt
python cli/install_data_plane.py
