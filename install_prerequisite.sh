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
sudo systemctl restart docker
# Install docker-compose
pip install docker-compose sarge python-keycloak requests certauth --user
