# migration.mk is a sub makefile about migration recipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>


include $(CURDIR)/.env
DB_DUMP_FILE ?= $(CURDIR)/backup/sqldump/v2025/2025_LL_django-v5.2.sql

.PHONY: migration/db/restore
migration/db/restore:  ## Restore the database from a dump file
migration/db/restore: dev/up
	docker compose exec -T db \
		mysql -uroot -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < ${DB_DUMP_FILE}