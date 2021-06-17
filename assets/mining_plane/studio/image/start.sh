#!/bin/bash
function start_services {
    systemctl enable codeserver.service
    systemctl enable jupyterlab.service
    systemctl enable filebrowser.service
    systemctl enable gitwebui.service

    systemctl start codeserver.service
    systemctl start jupyterlab.service
    systemctl start filebrowser.service
    systemctl start gitwebui.service
}


function rename_user {
    id eopfdev
    usermod -l ${USERNAME} eopfdev
    groupmod -n ${USERNAME} eopfdev
    usermod -d /home/${USERNAME} -m ${USERNAME}
    usermod -c "${USERFULLNAME}" ${USERNAME}
    id $1

    # echo "${USERNAME}:100000:65536" > /etc/subgid
    # echo "${USERNAME}:100000:65536" > /etc/subuid

    sed -i "s/USER/${USERNAME}/g" /etc/systemd/system/jupyterlab.service
    sed -i "s/USER/${USERNAME}/g" /etc/systemd/system/codeserver.service
    sed -i "s/USER/${USERNAME}/g" /etc/systemd/system/filebrowser.service
    sed -i "s/USER/${USERNAME}/g" /etc/systemd/system/gitwebui.service

    echo "export USER=${USERNAME}" > /home/${USERNAME}/.local/user_env.sh
    echo "export USERFULLNAME=${USERFULLNAME}" >> /home/${USERNAME}/.local/user_env.sh
    echo "export GIT_AUTHOR_NAME=${USERFULLNAME}" >> /home/${USERNAME}/.local/user_env.sh
    echo "export GIT_AUTHOR_EMAIL=${USEREMAIL}" >> /home/${USERNAME}/.local/user_env.sh
    echo "export PATH=/home/${USERNAME}/bin:/home/${USERNAME}/.local/bin:/usr/local/devtools/bin:\${PATH}" >> /home/${USERNAME}/.local/user_env.sh
    echo "source /home/${USERNAME}/.local/user_env.sh" >> /home/${USERNAME}/.bashrc

    sudo -u ${USERNAME} bash -c "git config --global user.name \"${USERFULLNAME}\""
    sudo -u ${USERNAME} bash -c "git config --global user.email \"${USEREMAIL}\""
    chown -Rf ${USERNAME}:${USERNAME} /home/${USERNAME}
}

rename_user
start_services
