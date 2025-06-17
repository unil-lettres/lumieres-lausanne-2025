# v2024.mk is a sub makefile helps to compare with original version
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>


V2024_PATH ?= $(CURDIR)/backup/v2024
V2024_DOCKER_COMPOSE_FILE ?= $(CURDIR)/docker/docker-compose.v2024.yml

V2024_DOCKER ?= docker compose \
					-f ${V2024_DOCKER_COMPOSE_FILE} \
					--project-directory ${V2024_PATH}


$(V2024_PATH):
	git clone https://github.com/XavierBeheydt/lumieres-lausanne-2024 ${V2024_PATH}
	rm -rf ${V2024_PATH}/.git
	rm -rf ${V2024_PATH}/.devcontainer
	rm -rf ${V2024_PATH}/.vscode
	cp -r  $(CURDIR)/app/media ${V2024_PATH}/app/backend/media
v2024/download: $(V2024_PATH)
v2024/download:  ## Download the original version

v2024/rm:  ## Remove the original version
v2024/rm: v2024/down
	rm -rf $(V2024_PATH)

V2024_DB_DUMP_FILE 	?= $(CURDIR)/backup/sqldump/v2024/2024-08-23_LL_django-v1.sql
V2024_DB_NAME 		?= lumie_django_v3
V2024_DB_USER 		?= root
V2024_DB_PASSWORD	?= password
v2024/db/prepare:  ## Prepare the database for the original version
	$(V2024_DOCKER) up -d db && sleep 10 &&\
		$(V2024_DOCKER) exec -T db \
		mysql -uroot -p${V2024_DB_PASSWORD} ${V2024_DB_NAME} < ${V2024_DB_DUMP_FILE}


v2024/up:  ## Up the original version
	$(V2024_DOCKER) up -d

v2024/cp:  ## Copy the media folder in v2024 app
v2024/cp: v2024/up
	$(V2024_DOCKER) cp $(CURDIR)/app/media app:/usr/src/lumieres

v2024/down:  ## Down the original version
	$(V2024_DOCKER) down

v2024/createsuperuser:  ## Create a superuser for the original version
	$(V2024_DOCKER) exec -it app python manage.py createsuperuser