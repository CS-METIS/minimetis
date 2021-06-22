sudo apt update -y
sudo apt upgrade -y
sudo apt install -y build-essential apt-transport-https ca-certificates \
    lsb-release gnupg make wget curl unzip vim git python3 python3-pip docker-compose conntrack python-is-python3 default-jre

# Install  docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io 
sleep 30
sudo systemctl restart docker
docker run hello-world
# Install docker-compose
pip install docker-compose tenacity==6.3.1 sarge==0.1.6 python-keycloak==0.24.0 requests==2.24.0 certauth==1.3.0 urllib3==1.25.11 --user
