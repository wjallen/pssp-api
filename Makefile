NSPACE="wallen"
APP="pssp-app"
VER="0.1.2"

list-targets:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


build-db:
	docker build -t ${NSPACE}/${APP}-db:${VER} \
                     -f docker/Dockerfile.db \
                     ./

build-api:
	docker build -t ${NSPACE}/${APP}-api:${VER} \
                     -f docker/Dockerfile.api \
                     ./

build-wrk:
	docker build -t ${NSPACE}/${APP}-wrk:${VER} \
                     -f docker/Dockerfile.wrk \
                     ./


test-db: build-db
	docker run --name ${NSPACE}-db \
                   --network ${NSPACE}-network-test \
                   -p 6441:6379 \
                   -d \
                   -u 827385:815499 \
                   -v ${PWD}/data/:/data \
                   ${NSPACE}/${APP}-db:${VER}

test-api: build-api
	docker run --name ${NSPACE}-api \
                   --network ${NSPACE}-network-test \
                   -p 5041:5000 \
                   -d \
                   ${NSPACE}/${APP}-api:${VER} 

test-wrk: build-wrk
	docker run --name ${NSPACE}-wrk \
                   --network ${NSPACE}-network-test \
                   -d \
                   ${NSPACE}/${APP}-wrk:${VER} 


clean-db:
	docker ps -a | grep ${NSPACE}-db | awk '{print $$1}' | xargs docker rm -f

clean-api:
	docker ps -a | grep ${NSPACE}-api | awk '{print $$1}' | xargs docker rm -f

clean-wrk:
	docker ps -a | grep ${NSPACE}-wrk | awk '{print $$1}' | xargs docker rm -f



build-all: build-db build-api build-wrk

test-all: test-db test-api test-wrk

clean-all: clean-db clean-api clean-wrk




compose-up:
	docker-compose -f docker/docker-compose.yml pull
	docker-compose -f docker/docker-compose.yml -p ${NSPACE} up -d --build ${NSPACE}-db
	docker-compose -f docker/docker-compose.yml -p ${NSPACE} up -d --build ${NSPACE}-api
	sleep 5
	docker-compose -f docker/docker-compose.yml -p ${NSPACE} up -d --build ${NSPACE}-wrk

compose-down:
	docker-compose -f docker/docker-compose.yml -p ${NSPACE} down

