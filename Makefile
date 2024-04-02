NSPACE="wallen"
APP="pssp-app"
VER="0.3.4"
RPORT="6379"
FPORT="5000"
UID="1000"
GID="1000"

list-targets:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


build-db:
	docker pull redis:6.2.3

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
                   -p ${RPORT}:6379 \
                   -d \
                   -u ${UID}:${GID} \
                   -v ${PWD}/data/:/data \
                   redis:6.2.3

test-api: build-api
	docker run --name ${NSPACE}-api \
                   --network ${NSPACE}-network-test \
                   --env REDIS_IP=${NSPACE}-db \
                   -p ${FPORT}:5000 \
                   -d \
                   ${NSPACE}/${APP}-api:${VER} 

test-wrk: build-wrk
	docker run --name ${NSPACE}-wrk \
                   --network ${NSPACE}-network-test \
                   --env REDIS_IP=${NSPACE}-db \
                   -d \
                   ${NSPACE}/${APP}-wrk:${VER} 


clean-db:
	docker stop ${NSPACE}-db && docker rm -f ${NSPACE}-db

clean-api:
	docker stop ${NSPACE}-api && docker rm -f ${NSPACE}-api

clean-wrk:
	docker stop ${NSPACE}-wrk && docker rm -f ${NSPACE}-wrk



build-all: build-db build-api build-wrk

test-all: test-db test-api test-wrk

clean-all: clean-db clean-api clean-wrk



compose-up:
	VER=${VER} docker-compose -f docker/docker-compose.yml -p ${NSPACE} up -d --build

compose-down:
	VER=${VER} docker-compose -f docker/docker-compose.yml -p ${NSPACE} down




k-test:
	kubectl apply -f kubernetes/test/pssp-test-db-service.yml
	DBIP=$$(kubectl describe service pssp-test-db-service | grep 'IP:' | awk '{print $$2}') && \
	cat kubernetes/test/* | TAG=${VER} envsubst '$${TAG}' | RIP=$${DBIP} envsubst '$${RIP}' | yq | kubectl apply -f -

k-test-del:
	cat kubernetes/test/*.yml | TAG=${VER} envsubst '$${TAG}' | yq | kubectl delete -f -



k-prod:
	kubectl apply -f kubernetes/prod/pssp-prod-db-service.yml
	DBIP=$$(kubectl describe service pssp-prod-db-service | grep 'IP:' | awk '{print $$2}') && \
	cat kubernetes/prod/* | TAG=${VER} envsubst '$${TAG}' | RIP=$${DBIP} envsubst '$${RIP}' | yq | kubectl apply -f -

k-prod-del:
	cat kubernetes/prod/*.yml | TAG=${VER} envsubst '$${TAG}' | yq | kubectl delete -f -




