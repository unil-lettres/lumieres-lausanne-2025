# TODO

## Staging stack

- [ ] Create staging.mk file with staging recipes
  - [ ] staging/up, staging/down, staging/start, staging/stop
  - [ ] staging/compose/up, staging/compose/down, staging/compose/start, etc.
  - [ ] staging/compose/logs, staging/compose/build
- [ ] Create docker/compose.staging.yml
- [ ] Update COMPOSE_STAGING variable in staging.mk
- [ ] Add staging.mk to main Makefile

## Prod stack

- [ ] Create prod.mk file with prod recipes
  - [ ] prod/up, prod/down, prod/start, prod/stop
  - [ ] prod/compose/up, prod/compose/down, prod/compose/start, etc.
  - [ ] prod/compose/logs, prod/compose/build
- [ ] Create docker/compose.prod.yml
- [ ] Update COMPOSE_PROD variable in prod.mk
- [ ] Add prod.mk to main Makefile

## Docker structure

- [ ] Move docker-compose override files into docker/ folder
  - [ ] Move docker/docker-compose.dev.yml to docker/compose.dev.yml
  - [ ] Update dev.mk COMPOSE variable path
  - [ ] Verify all references are updated

## Solr

- [ ] Move solr configuration to settings folder
  - [ ] Identify solr data/config location
  - [ ] Move to settings/solr
  - [ ] Update docker-compose references
  - [ ] Update Django settings if needed
