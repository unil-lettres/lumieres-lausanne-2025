# Informations techniques - lumieres.unil.ch

## Informations générales

Cette page documente la VM de production qui héberge l'application web
**Lumières Lausanne**.

- Application : `https://lumieres.unil.ch/`
- VM / SSH : `lumieres-srv2.unil.ch`
- Hostname observé : `lumieres-srv2`
- FQDN observé : `lumieres-srv2.unil.ch`
- IP observée : `130.223.28.250`
- Hébergement : CI
- Environnement : production

Les informations fonctionnelles de l'application sont documentées dans la page
**Lumières Lausanne** du même livre.

Dernière vérification read-only : **2026-07-09** pour l'image applicative
active ; vérification système complète : **2026-06-12**.

## État opérationnel actuel

- OS : Red Hat Enterprise Linux 8.10
- Runtime : Docker Compose
- Répertoire stack : `/u01/projects/dockerized/lumieres2-prod`
- Image web : `unillett/lumieres:v2026.07.03`
- Base de données : MySQL 9.3
- Recherche : Solr 8
- Frontend/static/media : nginx
- Reverse proxy public : Traefik v1.7

Validation read-only du 2026-06-12 :

- `systemctl --failed` : 0 failed units
- `docker.service` : actif
- `firewalld.service` : actif
- `sshd.service` : actif
- `nessusagent.service` : actif
- `vmtoolsd.service` : actif
- `httpd.service` : inactif/désactivé, attendu avec le routage Docker actuel
- containers Lumières : up
- DB et Solr : healthy
- public `https://lumieres.unil.ch/` : `200`
- public `https://www.lumieres.unil.ch/` : `200`
- direct VM `https://lumieres-srv2.unil.ch/` : `404`, attendu
- dernier backup DB : `gzip -t` OK
- `needs-restarting -r` : reboot non nécessaire
- `dnf check-update --cacheonly --quiet` : aucune mise à jour listée pendant le
  check `sudo`

## Urgence / survie mainteneur

Cette section est volontairement redondante avec les sections détaillées plus
bas. Elle sert de point d'entrée rapide en cas d'incident ou de reprise par une
personne qui ne connaît pas encore l'application.

### Vérifier ou redémarrer la stack de production

```bash
ssh lmradm@lumieres-srv2.unil.ch
cd /u01/projects/dockerized/lumieres2-prod
docker compose config --images
docker compose ps
docker compose logs --tail=200 web
curl -I https://lumieres.unil.ch/
```

Si un redémarrage/recreate est explicitement nécessaire :

```bash
cd /u01/projects/dockerized/lumieres2-prod
docker compose config --images
docker compose up -d
docker compose ps
curl -I https://lumieres.unil.ch/
```

Point critique : `docker compose config --images` doit montrer une image
applicative pinnée sur un tag de release explicite, par exemple
`unillett/lumieres:v2026.07.03`, jamais `latest`.

### Importer un dump SQL

Un import de dump écrase l'état de la base ciblée. En production, ne le faire
qu'après autorisation explicite, snapshot/backup récent et plan de rollback.

Exemple de restauration sur la stack courante depuis un dump SQL gzip :

```bash
cd /u01/projects/dockerized/lumieres2-prod
zcat /path/to/dump.sql.gz | docker compose exec -T db \
  bash -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
docker compose exec -T web python manage.py sync_status_roles --apply
docker compose exec -T web python manage.py update_index
```

Si le dump est un ancien dump legacy, ne pas l'importer directement : suivre les
notes de normalisation de schema dans la documentation projet
`descr/deployment.md`.

### Créer un superuser Django

Créer un superuser en production doit rester exceptionnel et autorisé. Commande
technique :

```bash
cd /u01/projects/dockerized/lumieres2-prod
docker compose exec -T web python manage.py createsuperuser
docker compose exec -T web python manage.py sync_status_roles --apply
```

### Rafraîchir les fichiers statiques et l'index

Après un déploiement d'image ou si les CSS/images ne correspondent pas :

```bash
cd /u01/projects/dockerized/lumieres2-prod
docker compose exec -T web python manage.py collectstatic --noinput
```

Si la recherche est vide ou incohérente :

```bash
cd /u01/projects/dockerized/lumieres2-prod
docker compose exec -T web python manage.py update_index
```

Utiliser `rebuild_index --noinput` uniquement quand une reconstruction complète
est réellement voulue.

## Hardware

Informations observées le 2026-06-12 :

- vCPU : 2, selon la documentation VM existante
- mémoire : 7.5 GiB
- swap : 4 GiB
- disques : 160 GB au total

Organisation des disques :

| Device / LV | Taille | Point de montage | FS |
| --- | ---: | --- | --- |
| `/dev/mapper/rhel-root` | 35 GB | `/` | xfs |
| `/dev/mapper/rhel-var` | 19.8 GB | `/var` | xfs |
| `/dev/mapper/vg_data-u01` | 100 GB | `/u01` | xfs |
| `/boot` | 1 GB | `/boot` | xfs |
| `/boot/efi` | 200 MB | `/boot/efi` | vfat |

Utilisation disque observée le 2026-06-12 :

- `/` : 17 GB / 35 GB, 48 %
- `/var` : 3.5 GB / 20 GB, 18 %
- `/u01` : 66 GB / 100 GB, 66 %
- `/boot` : 348 MB / 994 MB, 35 %
- `/boot/efi` : 6.2 MB / 200 MB, 4 %

## Système

- OS : Red Hat Enterprise Linux 8.10
- Kernel actif le 2026-06-12 : `4.18.0-553.132.1.el8_10.x86_64`
- Hostname : `lumieres-srv2.unil.ch`
- DNS public : `lumieres.unil.ch`
- SELinux : `Enforcing`
- Cloud-init : non installé, selon la documentation existante
- Docker Engine : `29.0.0`
- Docker Compose : `v2.40.3`
- Git : `2.43.7`

## Réseau

- IPv4 : `130.223.28.250/22`
- Interface : `ens192`
- Gateway : `130.223.28.1`
- DNS : `130.223.8.20`, `130.223.4.5`
- Domaine de recherche : `unil.ch`

Interfaces Docker observées :

- `docker0` : `172.17.0.1/16`
- `br-8d5621466b9e` : `172.18.0.1/16`
- `br-d0e912102a66` : `172.25.0.1/16`

HTTPS public :

- `https://lumieres.unil.ch/`
- `https://www.lumieres.unil.ch/`

HTTPS direct sur la VM :

- `https://lumieres-srv2.unil.ch/` retourne `404`, ce qui correspond au routage
  actuel.

## Accès SSH

Accès serveur :

```bash
ssh lmradm@lumieres-srv2.unil.ch
```

Répertoire home :

```text
/home/lmradm
```

Credentials :

- voir `vlett` Vault ;
- ne pas copier de secrets dans le wiki.

Pour créer ou accorder un accès serveur, contacter Niels Alkema
(`niels.alkema@unil.ch`).

Utilisateurs locaux / applicatifs documentés :

- `lmradm`
- `jganivet`
- `nalkema`
- `vroubaty`

Accès sudo documenté :

- `lmradm`, `jganivet` : entrée sudoers locale avec `NOPASSWD`
- `nalkema`, `vroubaty` : entrée sudoers administrateurs

État sudo observé le 2026-06-12 :

- `lmradm` peut exécuter `sudo -n true`.

## Stack Docker Compose

Répertoire de la stack de production :

```text
/u01/projects/dockerized/lumieres2-prod
```

Fichiers Compose / déploiement présents en production :

```text
/u01/projects/dockerized/lumieres2-prod/docker-compose.yml
/u01/projects/dockerized/lumieres2-prod/docker-compose.prod.yml
/u01/projects/dockerized/lumieres2-prod/.env
```

`docker-compose.prod.yml` surcharge l'image web via :

```text
LUMIERES_IMAGE
```

Valeur observée le 2026-07-09 :

```text
LUMIERES_IMAGE=unillett/lumieres:v2026.07.03
```

Containers observés le 2026-07-09 :

| Container | Image | Rôle | État |
| --- | --- | --- | --- |
| `lumieres-prod-web-1` | `unillett/lumieres:v2026.07.03` | application Django | up |
| `lumieres-prod-db-1` | `mysql:9.3` | base MySQL | up, healthy |
| `lumieres-prod-front-1` | `nginx:alpine` | frontend/static/media | up |
| `lumieres-prod-solr-1` | `solr:8` | recherche Solr | up, healthy |
| `django-lumiereslausanne_proxy_1` | `traefik:v1.7-alpine` | proxy HTTP/HTTPS public | up |

Ports publics :

- Traefik : `0.0.0.0:80->80`, `0.0.0.0:443->443`
- Front nginx : `0.0.0.0:8000->80`

`httpd.service` est installé mais désactivé/inactif ; c'est attendu avec le
routage de production actuel.

Commandes de vérification :

```bash
cd /u01/projects/dockerized/lumieres2-prod
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --images
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

## Image de production

Image observée le 2026-07-09 :

```text
unillett/lumieres:v2026.07.03
```

Digest observé :

```text
unillett/lumieres@sha256:82ca96ac53e23ee607589261b46a250705152599f9b03a1fe99900069ea1e8a7
```

Labels observés :

```text
org.opencontainers.image.version=v2026.07.03
org.opencontainers.image.revision=c06c2c2a9d7a8a5e567a9900c931787e2626fe90
org.opencontainers.image.created=2026-07-03T17:27:44.598Z
org.opencontainers.image.source=https://github.com/unil-lettres/lumieres-lausanne-2025
```

Note importante :

- la production doit utiliser la surcharge `.env` avec un tag explicite ;
- ne pas se baser sur `latest` ;
- l'ancienne page wiki mentionnait `unillett/lumieres:prod-latest` puis
  `unillett/lumieres:v2026.03.19`; l'état observé le 2026-07-09 est
  `unillett/lumieres:v2026.07.03`.

## Données persistantes

Media :

```text
/u01/projects/dockerized/media
```

Stack/config/static/Solr bind data :

```text
/u01/projects/dockerized/lumieres2-prod
```

Logs applicatifs :

```text
/u01/projects/dockerized/lumieres2-prod/logging
```

Volume Docker DB :

```text
/u01/var-lib-docker/volumes/lumieres-prod_db_data/_data
```

Principaux volumes / bind mounts de production :

| Usage | Chemin |
| --- | --- |
| Static files | `/u01/projects/dockerized/lumieres2-prod/static` |
| Media | `/u01/projects/dockerized/media` |
| Logs | `/u01/projects/dockerized/lumieres2-prod/logging` |
| Logs nginx persistés | `/u01/projects/dockerized/lumieres2-prod/logging/nginx` |
| Configuration/données Solr | `/u01/projects/dockerized/lumieres2-prod/solr/...` |

## Logs trafic web

Une persistance des logs webserver a été ajoutée le 2026-06-09 sans redéployer
l'application Django.

Fichier actif :

```text
/u01/projects/dockerized/lumieres2-prod/logging/nginx/lumieres-access.log
```

État observé le 2026-06-12 :

- fichier présent ;
- taille : environ 11 MB ;
- propriétaire/groupe : `root:lmradm` ;
- mode : `0640`.

Le log nginx contient l'IP d'origine dans le champ `X-Forwarded-For`, utile pour
distinguer trafic UNIL / non-UNIL.

Rétention :

- logrotate : `/etc/logrotate.d/lumieres-nginx-access`
- rotation quotidienne ;
- 180 rotations ;
- compression ;
- `copytruncate`.

Documentation locale :

- `docs/traffic/lumieres-webserver-logging-setup.md`
- `docs/traffic/lumieres-anonymous-traffic-setup.md`

## Backups

Script de backup DB quotidien :

```text
/etc/cron.daily/lumieres-db-backup
```

Sortie des backups :

```text
/home/lmradm/LL_backup_YYYY-MM-DD_HH-MM.sql.gz
```

Rétention sur la VM : 14 jours.

Mécanisme :

```bash
docker compose exec -T db mysqldump --single-transaction --quick --routines --triggers ... | gzip
```

Dernier backup DB vérifié le 2026-06-12 :

```text
/home/lmradm/LL_backup_2026-06-12_03-43.sql.gz
```

Contrôle d'intégrité :

```text
gzip -t OK
```

Backup local de restauration sur le Mac de Julien :

```text
/Users/jganivet/Développement/Backups/lumieres.unil.ch
```

Contenu documenté :

- miroir media ;
- dumps DB ;
- fichiers de récupération du stack ;
- archive du conflit de noms ne différant que par la casse, pour restauration
  exacte des media.

## Timers et cron

Timers systemd observés le 2026-06-12 :

- `dnf-makecache.timer`
- `insights-client.timer`
- `mlocate-updatedb.timer`
- `sysstat-collect.timer`
- `sysstat-summary.timer`
- `systemd-tmpfiles-clean.timer`
- `unbound-anchor.timer`

Cron système :

```text
/etc/cron.d/0hourly
/etc/cron.d/raid-check
/etc/cron.daily/logrotate
/etc/cron.daily/lumieres-db-backup
/etc/cron.hourly/0anacron
```

Crontab root :

- aucune crontab root trouvée.

## Agents

Agents / VM tools documentés :

- `NessusAgent-11.0.3-el8.x86_64`
- `open-vm-tools-12.3.5-2.el8_10.2.x86_64`
- `pcp-export-zabbix-agent`
- `pcp-export-pcp2zabbix`

Services observés actifs le 2026-06-12 :

- `nessusagent.service`
- `vmtoolsd.service`

## Certificat SSL

Type : Let's Encrypt.

Gestion : Traefik ACME.

Noms du certificat observés le 2026-06-12 :

- `lumieres.unil.ch`
- `www.lumieres.unil.ch`

Validité observée le 2026-06-12 :

- Issuer : Let's Encrypt `YR2`
- Valide depuis : `2026-06-12 02:08:24 UTC`
- Valide jusqu'au : `2026-09-10 02:08:23 UTC`

Configuration ACME Traefik :

```text
/u01/projects/dockerized/proxy/acme.json
/u01/projects/dockerized/proxy_v1file/traefik.toml
```

Email ACME documenté :

```text
julien.ganivet@unil.ch
```

## Maintenance

Fenêtre de maintenance : mensuelle.

Dernière maintenance OS observée :

- `2026-06-11`

État live observé le 2026-06-12 :

- uptime : environ 1 jour et 11 heures ;
- kernel actif : `4.18.0-553.132.1.el8_10.x86_64` ;
- aucun reboot requis selon `needs-restarting -r` ;
- aucune mise à jour listée par `sudo dnf check-update --cacheonly --quiet`.

Maintenance observée du 2026-06-11 :

- transaction DNF `177` ;
- utilisateur DNF : `Niels Alkema <nalkema>` ;
- début : `2026-06-11 05:01:38` ;
- fin : `2026-06-11 05:05:52` ;
- return code : `Success` ;
- installation du kernel `4.18.0-553.132.1.el8_10` ;
- upgrade de paquets système, dont `docker-ce-rootless-extras`, `glibc`,
  `gnutls`, `firewalld`, `linux-firmware`, `cockpit`, `samba-*`, `expat`,
  `grub2-*`, `bind-*`, `httpd-*`, `mod_ssl`, `mod_http2`, `vim-*`, `poppler`,
  `unbound-libs`, `sos` et outils kernel ;
- suppression de l'ancien kernel `4.18.0-553.123.1.el8_10` ;
- reboot observé à `2026-06-11 05:06` ;
- kernel actif après reboot : `4.18.0-553.132.1.el8_10.x86_64`.

Maintenance documentée du 2026-04-23 :

- snapshot vSphere créé avant maintenance ;
- `sudo dnf -y update` ;
- 56 paquets mis à jour, notamment `systemd`, `bind`, `nss`, `grafana`,
  `linux-firmware`, `microcode_ctl`, `docker-ce-rootless-extras` et les outils
  kernel ;
- installation du kernel `4.18.0-553.120.1.el8_10` ;
- redémarrage effectué avec succès.

Validation post-maintenance 2026-04-23 :

- 0 failed units ;
- SELinux enforcing ;
- Docker actif ;
- conteneurs Lumières démarrés ;
- conteneurs DB et Solr healthy ;
- `https://lumieres.unil.ch/` : `200` ;
- direct `https://lumieres-srv2.unil.ch/` : `404`, attendu ;
- dernier backup DB : intégrité OK ;
- aucune mise à jour restante à ce moment.

## Validation

Commandes HTTP :

```bash
curl -k -sS -o /dev/null -w 'public %{http_code} %{time_total}\n' https://lumieres.unil.ch/
curl -k -sS -o /dev/null -w 'public_www %{http_code} %{time_total}\n' https://www.lumieres.unil.ch/
curl -k -sS -o /dev/null -w 'direct_vm %{http_code} %{time_total}\n' https://lumieres-srv2.unil.ch/
```

Résultat attendu :

- `public` : `200`
- `public_www` : `200`
- `direct_vm` : `404`

## Points d'attention

- La production doit rester pinnée sur un tag d'image explicite via `.env`.
- L'image active observée le 2026-07-09 est `unillett/lumieres:v2026.07.03`.
- Après mise à jour de l'image web, exécuter `collectstatic`.
- Le mode d'authentification opérationnel est `Connexion locale` uniquement.
- Surveiller régulièrement l'espace disque, en particulier `/u01`, media,
  backups et images Docker.
- Avant une maintenance OS ou une opération de déploiement risquée, confirmer
  un snapshot vSphere et vérifier les backups DB/media.
- Les logs webserver persistés depuis le 2026-06-09 servent à l'analyse de
  trafic, mais ne permettent pas à eux seuls de savoir si un visiteur était
  authentifié dans Django.

## Références

Documentation opérationnelle locale :

- `docs/wiki/lumieres-app.md`
- `docs/wiki/lumieres-lausanne-staging.md`
- `docs/runbooks/vms/lumieres.md`
- `docs/runbooks/vm-updates/rhel-8.md`
- `docs/inventory/vms.md`
- `docs/inventory/services.md`
- `docs/change-log/2026-06.md`
- `docs/traffic/lumieres-webserver-logging-setup.md`
- `docs/traffic/lumieres-anonymous-traffic-setup.md`
