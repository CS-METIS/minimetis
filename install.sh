sudo apt update -y
sudo apt upgrade -y
sudo apt install -y build-essential apt-transport-https ca-certificates \
    lsb-release gnupg make wget curl unzip vim git python3 python3-pip docker-compose conntrack

# Install  docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install docker-compose
pip install docker-compose sarge python-keycloak requests --user

Configure user environment
source metis.env

cd assets/admin-plane
docker-compose up -d registry
cd -
# Install and configure minikube
## minikube
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin
## kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/v${KUBE_VERSION}/bin/linux/amd64/kubectl
chmod +x kubectl
sudo mv kubectl /usr/local/bin

## crictl
VERSION="v1.21.0"
wget https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz
sudo tar zxvf crictl-$VERSION-linux-amd64.tar.gz -C /usr/local/bin
rm -f crictl-$VERSION-linux-amd64.tar.gz

## helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
chmod +x get_helm.sh
sudo ./get_helm.sh
rm -f get_helm.sh

# add helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# start minikube with Project Calico CNI
minikube start --network-plugin=cni --cni=calico --kubernetes-version=v${KUBE_VERSION} --driver=none --insecure-registry=${PRIVATE_IP}:5000

# Run minikube tunnel to enable Kubernetes LoadBalancer
nohup minikube tunnel > /dev/null&

cd cli
python3 install_admin_plane.py
cd -

