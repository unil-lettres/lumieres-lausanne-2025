# Postmortem détaillé - Redémarrage production sur une ancienne image

Date de l’incident : 19 mars 2026
Environnement : production `lumieres.unil.ch`
Service concerné : stack Docker Compose Lumières, service `web`
Statut : corrigé, mesures préventives appliquées

## Résumé

Le 19 mars 2026, la production Lumières a été retrouvée avec le conteneur `web`
exécutant une ancienne image Docker : `unillett/lumieres:v2026.01.21`.

Cette image ne correspondait plus à l’état applicatif attendu. La production
avait dérivé vers une configuration ambiguë : `.env` pointait vers
`LUMIERES_IMAGE=unillett/lumieres:latest`, tandis que le fichier compose de base
contenait encore une référence historique à `v2026.01.21`.

Lors d’un reboot de l’hôte le 19 mars 2026 à 05:09 CET, deux entrées `@reboot`
dans la crontab utilisateur `lmradm` ont exécuté un `docker compose up -d`
simple dans `/u01/projects/dockerized/lumieres2-prod`. Cette commande ne
garantissait pas le chargement de `docker-compose.prod.yml`. Docker Compose a
donc résolu le service `web` vers l’image historique du fichier de base.

L’incident a été corrigé en déployant une release explicite `v2026.03.19`, en
repinnant `.env` sur cette image, puis en supprimant les entrées cron `@reboot`.

## Impact

- La production a redémarré sur une version applicative de janvier 2026.
- Les corrections déployées après `v2026.01.21` n’étaient plus garanties sur le
  service `web`.
- Le risque principal était la réapparition silencieuse de bugs déjà corrigés.
- L’incident a montré que `docker compose ps` seul ne suffisait pas à valider
  l’état applicatif réel.
- La validation doit aussi contrôler l’image effective du conteneur et ses
  labels applicatifs embarqués.

## Chronologie

### 2026-03-03

Une mise à jour production a modifié le pin d’image vers :

```env
LUMIERES_IMAGE=unillett/lumieres:latest
```

Le site répondait correctement après le déploiement, mais cette configuration a
réintroduit une ambiguïté : `latest` ne permettait plus de garantir quelle image
serait utilisée lors d’un redémarrage ou d’une recréation ultérieure.

### 2026-03-19 05:09 CET

L’hôte production a redémarré. La crontab utilisateur `lmradm` contenait deux
entrées :

```cron
@reboot sleep 30 && cd /u01/projects/dockerized/lumieres2-prod && docker compose up -d
@reboot sleep 300 && cd /u01/projects/dockerized/lumieres2-prod && docker compose up -d
```

Ces commandes ont relancé Docker Compose sans sélection explicite du fichier
`docker-compose.prod.yml`. À ce moment-là, le `docker compose up -d` simple a
résolu le service `web` vers l’image historique :

```text
unillett/lumieres:v2026.01.21
```

### 2026-03-19, investigation

L’état divergent a été confirmé :

```text
.env:        LUMIERES_IMAGE=unillett/lumieres:latest
web running: unillett/lumieres:v2026.01.21
```

La situation montrait deux problèmes distincts :

- la production n’était plus pinée sur une release explicite ;
- une automatisation de reboot relançait Compose avec un contexte incomplet.

### 2026-03-19, correction applicative

Une release explicite `v2026.03.19` a été créée depuis `master` commit
`aff6006`. La publication DockerHub de `unillett/lumieres:v2026.03.19` a été
vérifiée.

Des actifs de rollback ont été créés avant redéploiement :

```text
/u01/projects/dockerized/lumieres2-prod/backups/20260319_114450/
```

La base a été sauvegardée :

```text
backups/20260319_114450/lumieres-prod.sql
SHA256: e78ffe478b3058e5cbec04f131d85ed71ffb31a89f7ce20f297c4cc6055fcc00
```

`.env` a ensuite été repinné sur :

```env
LUMIERES_IMAGE=unillett/lumieres:v2026.03.19
```

Le service `web` a été redéployé, puis les tâches post-déploiement ont été
exécutées :

```bash
python manage.py collectstatic --noinput
python manage.py sync_status_roles --apply
python manage.py update_index
```

Les contrôles publics ont confirmé le retour à un état nominal :

```text
https://lumieres.unil.ch/         HTTP/2 200
https://lumieres.unil.ch/projets/ HTTP/2 200
```

### 2026-03-19, suppression de l’automatisation fautive

La crontab `lmradm` a été sauvegardée :

```text
/u01/projects/dockerized/lumieres2-prod/backups/20260319_130340/lmradm.crontab.before-remove-reboot
```

Les deux entrées `@reboot ... docker compose up -d` ont été supprimées. La
politique Docker `restart: unless-stopped` a été conservée comme mécanisme de
reprise après reboot.

### 2026-05-05, mitigation complémentaire

`.env` production a ensuite été complété avec les valeurs Compose attendues :

```env
COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
COMPOSE_PROJECT_NAME=lumieres-prod
LUMIERES_IMAGE=unillett/lumieres:v2026.05.05
```

Cette mesure rend les commandes `docker compose ...` simples moins dangereuses
depuis `/u01/projects/dockerized/lumieres2-prod`, à condition de vérifier la
résolution effective avec `docker compose config --images`.

## Cause racine

La cause racine est la combinaison de deux dérives opérationnelles :

1. La production n’était plus pinée sur une image de release explicite.
   L’utilisation de `latest` rendait la cible applicative ambiguë.
2. Une automatisation de reboot non nécessaire exécutait `docker compose up -d`
   sans garantir l’utilisation du fichier compose de production.

Ces deux dérives ont permis à Docker Compose de revenir silencieusement vers
l’image historique `v2026.01.21`.

## Facteurs contributifs

- Le fichier compose de base contenait encore une image historique.
- Le fichier compose de production n’était pas chargé par les commandes cron.
- Les deux entrées `@reboot` étaient redondantes avec la politique Docker
  `restart: unless-stopped`.
- Les validations précédentes ne rendaient pas obligatoire la comparaison entre
  `.env`, `docker compose config --images`, l’image effective du conteneur et
  les labels OCI.

## Détection

L’incident a été détecté lors d’une investigation de drift en production. La
vérification décisive a consisté à comparer :

- la valeur attendue dans `.env` ;
- l’image résolue par Docker Compose ;
- l’image effectivement exécutée par le conteneur `web` ;
- les labels applicatifs embarqués dans l’image.

Commande de vérification documentée :

```bash
docker inspect lumieres-prod-web-1 --format '{{.Config.Image}}|{{index .Config.Labels "org.opencontainers.image.revision"}}|{{index .Config.Labels "org.opencontainers.image.version"}}'
```

## Ce qui a bien fonctionné

- Les notes de déploiement ont permis de reconstruire la séquence de l’incident.
- Une release taguée `v2026.03.19` a pu être créée et publiée rapidement.
- Les actifs de rollback ont été préparés avant le redéploiement.
- Les validations publiques ont confirmé le retour au service.
- La suppression des cron `@reboot` a éliminé le déclencheur direct.

## Ce qui a moins bien fonctionné

- `latest` a été utilisé en production, ce qui a cassé la reproductibilité.
- Une automatisation ancienne est restée active alors qu’elle n’était plus
  nécessaire.
- Le comportement de `docker compose up -d` dépendait implicitement des fichiers
  compose chargés.
- Les contrôles opérationnels ne vérifiaient pas encore systématiquement
  l’image effective et les labels du conteneur après redémarrage.

## Mesures correctives appliquées

- Production repinnée sur une release explicite :

  ```env
  LUMIERES_IMAGE=unillett/lumieres:v2026.03.19
  ```

- Service `web` redéployé sur l’image correcte.
- `collectstatic`, `sync_status_roles --apply` et `update_index` exécutés.
- Deux entrées cron `@reboot` supprimées.
- `restart: unless-stopped` retenu comme mécanisme standard de redémarrage.
- `COMPOSE_FILE` et `COMPOSE_PROJECT_NAME` ajoutés ensuite dans `.env`
  production.
- Runbooks mis à jour pour rappeler que la production ne doit jamais rester sur
  `latest`.

## Règles opérationnelles retenues

1. Ne jamais utiliser `latest` comme pin de production.
2. Toujours déployer une image taguée `vYYYY.MM.DD`.
3. Avant tout redéploiement ou investigation de redémarrage, vérifier :

   ```bash
   docker compose config --images
   docker compose ps
   docker inspect lumieres-prod-web-1 --format '{{.Config.Image}}|{{index .Config.Labels "org.opencontainers.image.revision"}}|{{index .Config.Labels "org.opencontainers.image.version"}}'
   ```

4. Ne pas ajouter de cron `@reboot` pour relancer une stack Docker déjà couverte
   par `restart: unless-stopped`.
5. Si une commande Compose doit être automatisée, elle doit fixer explicitement
   le contexte attendu : répertoire, fichiers compose, projet, image taguée et
   validations.
6. Les runbooks doivent rester alignés avec les fichiers compose effectivement
   présents sur la VM.

## Points à discuter en technical meeting

1. Faut-il interdire explicitement `latest` dans tous les environnements de
   production SIER ?
2. Faut-il ajouter un contrôle CI ou un script de preflight qui échoue si une
   configuration prod pointe vers `latest` ?
3. Faut-il standardiser une commande de vérification post-déploiement pour
   toutes les stacks Docker Compose ?
4. Faut-il auditer les crontabs utilisateur/root sur les autres VMs pour trouver
   des `@reboot docker compose up -d` similaires ?
5. Faut-il documenter une règle commune : Docker restart policies plutôt que
   cron pour la reprise après reboot ?
6. Faut-il imposer que `.env` prod contienne toujours `COMPOSE_FILE` et
   `COMPOSE_PROJECT_NAME` ?

## Références

- `descr/prod-deploy-runbook.md`, section `Deployment Record (2026-03-19)`.
- `descr/deployment.md`, sections `Execution Record (2026-03-19, prod)`,
  `Reboot Automation Fix (2026-03-19, prod)` et
  `Compose Default Simplification (2026-05-05, prod)`.
