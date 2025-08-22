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
# Make migrations for all apps
django/makemigrations:  ## Make migrations for all Django apps
	python ${APP_PATH}/manage.py makemigrations --settings=lumieres_project.settings

.PHONY: django/makemigrations/fiches
# Make migrations for fiches app only
django/makemigrations/fiches:  ## Make migrations for fiches app only
	python ${APP_PATH}/manage.py makemigrations fiches --settings=lumieres_project.settings

.PHONY: django/migrate
# Apply migrations for all apps
django/migrate:  ## Apply migrations for all Django apps
	python ${APP_PATH}/manage.py migrate --settings=lumieres_project.settings

.PHONY: django/migrate/fiches
# Apply migrations for fiches app only
django/migrate/fiches:  ## Apply migrations for fiches app only
	python ${APP_PATH}/manage.py migrate fiches --settings=lumieres_project.settings

.PHONY: django/collectstatic
django/collectstatic:  ## Collect static files for Django
	python ${APP_PATH}/manage.py collectstatic --noinput --settings=lumieres_project.settings

.PHONY: django/test
django/test:  ## Run all Django unit tests
	DJANGO_DEVELOPMENT=1 python ${APP_PATH}/manage.py test --settings=lumieres_project.settings

ARGS ?=
.PHONY: django/import
django/import:  ## Import data into Django
	python ${APP_PATH}/manage.py import_database ${ARGS} --settings=lumieres_project.settings

.PHONY: django/cov
django/cov:  ## Run Django tests with coverage and show report
	DJANGO_DEVELOPMENT=1 PYTHONPATH=${APP_PATH} coverage run --source=${APP_PATH}/fiches -m django test fiches --settings=lumieres_project.settings
	coverage report -m

.PHONY: django/showmigrations
# Show migrations for all apps
django/showmigrations:  ## Show Django migrations
	python ${APP_PATH}/manage.py showmigrations --settings=lumieres_project.settings

.PHONY: django/showmigrations/fiches
# Show migrations for fiches app only
django/showmigrations/fiches:  ## Show Django migrations for fiches app only
	python ${APP_PATH}/manage.py showmigrations fiches --settings=lumieres_project.settings

# Thumbnail cache management
.PHONY: django/thumbnail/cleanup
django/thumbnail/cleanup:  ## Cleanup thumbnail cache (media cache)
	python ${APP_PATH}/manage.py thumbnail cleanup
