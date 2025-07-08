# db.mk is a sub makefile about database recipes
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

include $(CURDIR)/.env
DB_DUMP_FILE ?= $(CURDIR)/backup/sqldump/v2025/db_2025-07-08.sql

.PHONY: db/prepare
db/prepare:  ## Restore the database from a dump file
db/prepare: dev/up
	docker compose exec -T db \
		mysql -uroot -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < ${DB_DUMP_FILE}
	
DB_DUMP_BACKUP ?= $(CURDIR)/backup/sqldump/v2025/backup.sql
.PHONY: db/backup
db/backup:  ## Backup the database in a dumpfile
db/backup:
	docker compose exec -T db \
		mysqldump -uroot -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > ${DB_DUMP_BACKUP}

.PHONY: db/restore
db/restore:  ## Restore the database from a dump file
db/restore:
	docker compose exec -T db \
		mysql -uroot -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < ${DB_DUMP_BACKUP}

.PHONY: db/clean
db/clean:  ## Clean the database by dropping all tables
	docker compose exec -T db \
		mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "DROP DATABASE ${MYSQL_DATABASE};"

.PHONY: db/create
db/create:  ## Create the database
db/create: db/clean
	docker compose exec -T db \
		mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "CREATE DATABASE ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"