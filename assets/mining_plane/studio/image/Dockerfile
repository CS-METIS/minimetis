FROM ubuntu:20.04

# Upgrade and install curl, sudo, essential development tools nginx, and xubuntu-desktop
RUN apt update -y && apt upgrade -y

ENV DEBIAN_FRONTEND=noninteractive 
RUN  apt update -y && apt install -y --no-install-recommends curl git sudo build-essential \
  lldb python gnupg libnss3 locales fuse libfuse2 s3fs \
  apt-transport-https ca-certificates software-properties-common \
  && apt clean -y

# Free a bit of space
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# Add a user `dev` so that you're not developing as the `root` user
# The user needs to sudoer be able to install code-server
RUN adduser --gecos '/usr/bin/bash' --disabled-password eopfdev && \
  echo "eopfdev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/nopasswd

ENV SHELL bash

# Install miniconda
RUN curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o Miniconda3-latest-Linux-x86_64.sh
RUN chmod u+x ./Miniconda3-latest-Linux-x86_64.sh
RUN sudo ./Miniconda3-latest-Linux-x86_64.sh -bfp /usr/local/devtools
RUN rm -f Miniconda3-latest-Linux-x86_64.sh
# Install code-server 
RUN curl -fsSL https://code-server.dev/install.sh > install.sh
RUN sh install.sh --method=standalone --prefix=/usr/local/devtools --version=3.10.0
RUN rm -f install.sh

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

# RUN conda install pip -y
# # Install JupyterLab
RUN conda install -c conda-forge -y jupyterlab numpy pandas geopy nodejs yarn nbdime nbresuse jupyterlab-git jupyter-resource-usage ipykernel ipyvuetify voila

RUN git clone https://github.com/cytoscape/ipycytoscape.git
RUN pip install ./ipycytoscape

RUN git clone https://github.com/jupyter-widgets/ipyleaflet.git
RUN pip install ./ipyleaflet

ADD jupyter_notebook_config.py /usr/local/devtools/etc/jupyter/jupyter_notebook_config.py

RUN jupyter lab build

# Install code-server extensions
RUN code-server --install-extension  ms-python.python
# ## Markdown
RUN code-server --install-extension yzhang.markdown-all-in-one
## JSon
RUN code-server --install-extension nickdemayo.vscode-json-editor
## Toml
RUN code-server --install-extension bungcip.better-toml
## yaml
RUN code-server --install-extension redhat.vscode-yaml

# ADD settings.json /home/eopfdev/.local/share/code-server/User

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
ADD credentials /home/eopfdev/.config/credentials
ADD rclone.conf /home/eopfdev/.config/rclone/rclone.conf
RUN conda install pylint -y
RUN conda install -c conda-forge rclone
RUN conda install -c conda-forge vim
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