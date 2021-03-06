FROM ubuntu:20.04

# Upgrade and install curl, sudo, essential development tools nginx, and xubuntu-desktop
RUN apt update -y && apt upgrade -y

ENV DEBIAN_FRONTEND=noninteractive 
RUN  apt update -y && apt install -y --no-install-recommends curl wget git sudo build-essential unzip \
  lldb python gnupg libnss3 locales fuse libfuse2 s3fs default-jdk maven iputils-ping vim libxml2-utils tree dnsutils \
  apt-transport-https ca-certificates software-properties-common \
  && apt clean -y

# Free a bit of space
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN sh -c "echo 'deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_20.04/ /' > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list"
RUN wget -nv https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_20.04/Release.key -O Release.key
RUN apt-key add - < Release.key
RUN apt update -y && apt install -y buildah skopeo && apt clean -y

# Adjust storage.conf to use vfs
# RUN sed -i 's/driver = "overlay"/driver = "vfs"/g' /etc/containers/storage.conf
COPY storage.conf /etc/containers/storage.conf
COPY registries.conf /etc/containers/registries.conf

# Add a user `dev` so that you're not developing as the `root` user
# The user needs to sudoer be able to install code-server
RUN adduser --gecos '/usr/bin/bash' --disabled-password eopfdev && \
  echo "eopfdev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/nopasswd

ENV SHELL bash

RUN mkdir -p /usr/local/devtools/bin

## install kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.18.4/bin/linux/amd64/kubectl
RUN chmod +x kubectl
RUN sudo mv kubectl /usr/local/devtools/bin

# Install miniconda
RUN curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o Miniconda3-latest-Linux-x86_64.sh
RUN chmod u+x ./Miniconda3-latest-Linux-x86_64.sh
RUN sudo ./Miniconda3-latest-Linux-x86_64.sh -bfp /usr/local/devtools
RUN rm -f Miniconda3-latest-Linux-x86_64.sh
# Install code-server 
RUN curl -fsSL https://code-server.dev/install.sh > install.sh
RUN sh install.sh --method=standalone --prefix=/usr/local/devtools --version=3.10.2
RUN rm -f install.sh

# Install scdf shell
COPY scdf-shell /usr/local/devtools/bin/scdf-shell
RUN chmod a+x /usr/local/devtools/bin/scdf-shell

# Install spring boot cli
RUN wget https://repo.spring.io/release/org/springframework/boot/spring-boot-cli/2.5.2/spring-boot-cli-2.5.2-bin.tar.gz
RUN tar -zxvf spring-boot-cli-2.5.2-bin.tar.gz -C /usr/local/devtools/
RUN rm -f spring-boot-cli-2.5.2-bin.tar.gz



RUN chown -R eopfdev:eopfdev /usr/local/devtools


USER eopfdev
WORKDIR /home/eopfdev
# Create USER environment variable to prevent "could not determine the current user, please set $USER" error when running "cargo new ..."
ENV USER eopfdev
ENV SHELL bash
ENV PATH /usr/local/devtools/bin:${PATH}
SHELL ["conda", "run", "-n", "base", "/bin/bash", "-c"]
RUN conda init bash
RUN echo 'conda activate base' >> ~/.bashrc

ENV PATH /usr/local/devtools/bin:${PATH}

RUN curl -fsSL  https://github.com/GoogleContainerTools/jib/releases/download/v0.6.0-cli/jib-jre-0.6.0.zip -o jib-jre-0.6.0.zip
RUN unzip jib-jre-0.6.0.zip
RUN cp -r jib-0.6.0/lib /usr/local/devtools/
RUN cp -r jib-0.6.0/bin/* /usr/local/devtools/bin/
RUN rm -rf jib-jre-0.6.0.zip jib-0.6.0

RUN curl -L https://repo.spring.io/snapshot/org/springframework/cloud/spring-cloud-dataflow-shell/2.8.0-SNAPSHOT/spring-cloud-dataflow-shell-2.8.0-20210612.072342-389.jar -o /usr/local/devtools/lib/spring-cloud-dataflow-shell-2.8.0.jar

# RUN conda install pip -y
# # Install JupyterLab
RUN conda install -c conda-forge -y jupyterlab numpy pandas geopy nodejs yarn nbdime nbresuse jupyterlab-git jupyter-resource-usage ipykernel ipyvuetify voila pylint flake8 mypy rope black

# RUN git clone https://github.com/cytoscape/ipycytoscape.git
# RUN pip install ./ipycytoscape
RUN pip install ipycytoscape
# RUN git clone https://github.com/jupyter-widgets/ipyleaflet.git
# RUN pip install ./ipyleaflet
RUN pip install ipyleaflet

RUN git clone https://github.com/CS-METIS/metis-voila.git
RUN pip install ./metis-voila
RUN rm -R ./metis-voila
ADD jupyter_notebook_config.py /usr/local/devtools/etc/jupyter/jupyter_notebook_config.py

RUN jupyter lab build

# Install code-server extensions
# Python
RUN code-server --install-extension  ms-python.python
# git graph
RUN code-server --install-extension  mhutchie.git-graph
# ## Markdown
RUN code-server --install-extension yzhang.markdown-all-in-one
## JSon
RUN code-server --install-extension nickdemayo.vscode-json-editor
## Toml
RUN code-server --install-extension bungcip.better-toml
## yaml
RUN code-server --install-extension redhat.vscode-yaml
## xml
RUN code-server --install-extension redhat.vscode-xml
## Java
RUN code-server --install-extension vscjava.vscode-java-pack
RUN code-server --install-extension redhat.java
RUN code-server --install-extension Pivotal.vscode-boot-dev-pack

ADD settings.json /home/eopfdev/.local/share/code-server/User

RUN npm install -g ungit

USER root
WORKDIR /
# install file browser
RUN curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash
RUN chmod a+x /usr/local/bin/filebrowser
USER eopfdev
WORKDIR /home/eopfdev/.local
RUN /usr/local/bin/filebrowser config init --baseurl /browser --auth.method=noauth --port=8888
RUN /usr/local/bin/filebrowser users add "default-user" "default-password"
USER root
WORKDIR /
RUN rm -rf /etc/systemd/system/*
RUN rm -rf /usr/lib/systemd/system/*
RUN rm -rf /var/lib/systemd/deb-systemd-helper-enabled/multi-user.target.wants/*

ADD bootstrap.service /etc/systemd/system/bootstrap.service
ADD jupyterlab.service /etc/systemd/system/jupyterlab.service
ADD codeserver.service /etc/systemd/system/codeserver.service
ADD filebrowser.service /etc/systemd/system/filebrowser.service
ADD gitwebui.service /etc/systemd/system/gitwebui.service

RUN curl -L https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/systemctl3.py --output /usr/local/bin/systemctl
RUN curl -L https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/journalctl3.py --output /usr/local/bin/journalctl
RUN chmod a+x /usr/local/bin/systemctl
RUN chmod a+x /usr/local/bin/systemctl

RUN systemctl enable bootstrap.service
RUN systemctl disable binfmt-support.service

STOPSIGNAL SIGRTMIN+3

ADD start.sh /sbin
RUN chmod u+x /sbin/start.sh
VOLUME /home
CMD ["/bin/bash", "-c", "exec /usr/local/bin/systemctl"]