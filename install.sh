sudo apt update -y
sudo apt upgrade -y
sudo apt install -y build-essential apt-transport-https ca-certificates \
    lsb-release gnupg make wget curl unzip vim git python3 python3-pip docker-compose

# Install  docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
 sudo apt-get update
 sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install docker-compose
pip install docker-compose --user

# Configure user environment
source metis.env

# Install and configure minikube
## minikube
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin
## kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/v${KUBE_VERSION}/bin/linux/amd64/kubectl
chmod +x kubectl
sudo mv kubectl /usr/local/bin
## helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
chmod +x get_helm.sh
sudo ./get_helm.sh
rm -f get_helm.sh

# add helm repositories
helm add_repo bitnami https://charts.bitnami.com/bitnami
helm update repo

# start minikube with Project Calico CNI
minikube start --network-plugin=cni --cni=calico --kubernetes-version v1.18.16 --driver=none

# Run minikube tunnel to enable Kubernetes LoadBalancer
nohup minikube tunnel > /dev/null&

cd cli
python install_admin_plane.py
python install_data_plane.py
cd -

