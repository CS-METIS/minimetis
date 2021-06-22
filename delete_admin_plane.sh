#! /bin/bash
docker-compose -f assets/admin-plane/docker-compose.yml stop
docker-compose -f assets/admin-plane/docker-compose.yml rm -fv
docker volume prune -f
