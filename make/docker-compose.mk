# docker-compose.mk is sub makefile about docker compose commands.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: up docker/compose/up
up: docker/compose/up
docker/compose/up:  ## bring up the docker compose services
	docker-compose up -d ${SERVICES}

.PHONY: down docker/compose/down
down: docker/compose/down
docker/compose/down:  ## bring down the docker compose services
	docker-compose down ${SERVICES}

.PHONY: start docker/compose/start
start: docker/compose/start
docker/compose/start:  ## start the docker compose services
	docker-compose start ${SERVICES}

.PHONY: stop docker/compose/stop
stop: docker/compose/stop
docker/compose/stop:  ## stop the docker compose services
	docker-compose stop ${SERVICES}
	
.PHONY: restart docker/compose/restart
restart: docker/compose/restart
docker/compose/restart:  ## restart the docker compose services
	docker-compose restart ${SERVICES}

.PHONY: logs docker/compose/logs
logs: docker/compose/logs
docker/compose/logs:  ## show the logs of the docker compose services
	docker-compose logs -f ${SERVICES}