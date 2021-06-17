FROM gethue/hue:20210308-135001

USER root
RUN apt update -y && apt install iputils-ping -y
ADD mozilla-django-oidc mozilla-django-oidc
RUN ./build/env/bin/pip install ./mozilla-django-oidc
USER hue
