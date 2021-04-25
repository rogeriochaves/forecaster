eval $(docker-machine env rchaves-platform)
docker-compose -f docker-compose.prod.yml up -d --build