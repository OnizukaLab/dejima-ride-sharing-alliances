# git install
sudo yum install git

# docker install
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
docker --version

# ec2-userをdockerグループに入れることでdockerデーモンに接続する権限をあげる
sudo usermod -aG docker ec2-user
newgrp docker
docker ps

# docker-compose install
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# docker-test clone
# git clone https://github.com/u109755b/docker-test.git