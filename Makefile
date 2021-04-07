NSPACE="wallen"
APP="pssp-app"
VER="1.0.1"

list-targets:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


build-db:
	docker build -t ${NSPACE}/${APP}-db:${VER} \
                     -f docker/Dockerfile.db \
                     ./

build-fe:
	docker build -t ${NSPACE}/${APP}-fe:${VER} \
                     -f docker/Dockerfile.fe \
                     ./

build-api:
	docker build -t ${NSPACE}/${APP}-api:${VER} \
                     -f docker/Dockerfile.api \
                     ./


test-db: build-db
	docker run --name ${NSPACE}-db \
                   --network ${NSPACE}-network-test \
                   -p 6441:6379 \
                   -d \
                   -u 827385:815499 \
                   -v ${PWD}/data/:/data \
                   ${NSPACE}/${APP}-db:${VER}

test-fe: build-fe
	docker run --name ${NSPACE}-fe \
                   --network ${NSPACE}-network-test \
                   -p 5041:5000 \
                   -d \
                   ${NSPACE}/${APP}-fe:${VER} 

test-api: build-api
	docker run --name ${NSPACE}-api \
                   --network ${NSPACE}-network-test \
                   -p 5141:5000 \
                   -d \
                   ${NSPACE}/${APP}-api:${VER} 


build-all: build-db build-fe build-api

test-all: test-db test-fe test-api



clean-all:
	docker ps -a | grep ${NSPACE} | awk '{print $$1}'  | xargs docker rm -f

clean-db:
	docker ps -a | grep ${NSPACE}-db | awk '{print $$1}' | xargs docker rm -f

clean-fe:
	docker ps -a | grep ${NSPACE}-fe | awk '{print $$1}' | xargs docker rm -f

clean-api:
	docker ps -a | grep ${NSPACE}-api | awk '{print $$1}' | xargs docker rm -f




compose-up:
	docker-compose -p ${NSPACE} up -d --build

compose-down:
	docker-compose -p ${NSPACE} down

