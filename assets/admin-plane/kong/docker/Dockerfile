FROM kong:2.3.2
LABEL description="Alpine + Kong + kong-oidc plugin"

USER root
RUN apk update && apk add git unzip luarocks
RUN luarocks install kong-oidc
RUN luarocks install lua-resty-openidc 1.7.4 --force

USER kong