# django.mk is sub makefile about django commands.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>
#

.PHONY: django/runserver
django/runserver:  ## Run the django dev server
	python ${APP_PATH}/manage.py runserver

.PHONY: django/shell
django/shell:  ## Open a shell with Django
	python ${APP_PATH}/manage.py shell

.PHONY: django/createsuperuser
django/createsuperuser:  ## Create a superuser for Django
	python ${APP_PATH}/manage.py createsuperuser

.PHONY: django/makemigrations
django/makemigrations:  ## Make migrations for Django
	python ${APP_PATH}/manage.py makemigrations fiches --settings=lumieres_project.settings

.PHONY: django/migrate
django/migrate:  ## Apply migrations for Django
	python ${APP_PATH}/manage.py migrate fiches --settings=lumieres_project.settings

.PHONY: django/test
django/test:  ## Run all Django unit tests
	DJANGO_DEVELOPMENT=1 python ${APP_PATH}/manage.py test fiches --settings=lumieres_project.settings

ARGS ?=
.PHONY: django/import
django/import:  ## Import data into Django
	python ${APP_PATH}/manage.py import_database ${ARGS} --settings=lumieres_project.settings

.PHONY: django/cov
django/cov:  ## Run Django tests with coverage and show report
	DJANGO_DEVELOPMENT=1 PYTHONPATH=${APP_PATH} coverage run --source=${APP_PATH}/fiches -m django test fiches --settings=lumieres_project.settings
	coverage report -m