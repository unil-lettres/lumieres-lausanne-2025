# solr.mk is sub makefile about solr service receipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

.PHONY: solr/app/build-index
solr/app/build-index:
	docker compose exec -T bash -lc '\
		python manage.py rebuild_index --noinput --verbosity 2 && \
		python manage.py shell -c "from haystack.query import SearchQuerySet as S; print(\"Indexed docs:\", S().all().count())"\
		'

.PHONY: solr/dev/build-index
solr/dev/build-index:
	python ${APP_PATH}/manage.py rebuild_index --noinput --verbosity 2
	python ${APP_PATH}/manage.py shell -c "from haystack.query import SearchQuerySet as S; print(\"Indexed docs:\", S().all().count())"