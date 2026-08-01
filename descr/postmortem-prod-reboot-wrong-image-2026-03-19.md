# Postmortem court - Prod redémarrée sur une ancienne image

Date de l’incident : 19 mars 2026
Environnement : production `lumieres.unil.ch`
Service concerné : stack Docker Compose Lumières, service `web`
Statut : corrigé

## Résumé

Le 19 mars 2026, la production Lumières a été retrouvée avec le conteneur `web`
démarré sur une ancienne image Docker : `unillett/lumieres:v2026.01.21`.

La production ne devait plus utiliser cette image. Deux dérives se sont
combinées :

- `.env` pointait vers `LUMIERES_IMAGE=unillett/lumieres:latest`, au lieu d’une
  release explicite ;
- deux entrées `@reboot` dans la crontab de `lmradm` relançaient
  `docker compose up -d` après redémarrage de l’hôte, sans garantir le chargement
  du fichier `docker-compose.prod.yml`.

Résultat : après le reboot de l’hôte à **05:09 CET**, Docker Compose a résolu le
service `web` vers l’image historique du fichier compose de base.

## Impact

- Retour silencieux à une version applicative de janvier 2026.
- Risque de réapparition de bugs corrigés entre janvier et mars 2026.
- Perte de confiance dans un simple `docker compose ps` comme validation
  suffisante de l’état applicatif.

## Détail des cron fautifs

La crontab utilisateur `lmradm` contenait :

```cron
@reboot sleep 30 && cd /u01/projects/dockerized/lumieres2-prod && docker compose up -d
@reboot sleep 300 && cd /u01/projects/dockerized/lumieres2-prod && docker compose up -d
```

Ces tâches étaient inutiles, car les conteneurs avaient déjà une politique Docker
`restart: unless-stopped`.

## Cause racine

La cause racine est la combinaison de :

1. un pin de production ambigu sur `latest` ;
2. une automatisation de reboot non nécessaire ;
3. une commande Compose implicite qui ne garantissait pas l’utilisation du
   fichier de production.

## Correction appliquée

- Création et déploiement de la release explicite `v2026.03.19`.
- Repin de `.env` :

  ```env
  LUMIERES_IMAGE=unillett/lumieres:v2026.03.19
  ```

- Sauvegarde de rollback avant redéploiement :
  `/u01/projects/dockerized/lumieres2-prod/backups/20260319_114450/`
- Sauvegarde de la crontab :
  `/u01/projects/dockerized/lumieres2-prod/backups/20260319_130340/lmradm.crontab.before-remove-reboot`
- Suppression des deux entrées `@reboot`.
- Conservation de `restart: unless-stopped` comme mécanisme de reprise après
  reboot.
- Ajout ultérieur dans `.env` production :

  ```env
  COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
  COMPOSE_PROJECT_NAME=lumieres-prod
  ```

## Règles retenues

1. Ne jamais utiliser `latest` en production.
2. Toujours déployer une image taguée `vYYYY.MM.DD`.
3. Avant tout redéploiement ou investigation de redémarrage, vérifier :

   ```bash
   docker compose config --images
   docker compose ps
   docker inspect lumieres-prod-web-1 --format '{{.Config.Image}}|{{index .Config.Labels "org.opencontainers.image.revision"}}|{{index .Config.Labels "org.opencontainers.image.version"}}'
   ```

4. Ne pas utiliser de cron `@reboot` pour relancer une stack déjà couverte par
   `restart: unless-stopped`.
5. Auditer les autres VMs pour détecter d’éventuels `@reboot docker compose up -d`
   similaires.

## Question pour le technical meeting

Faut-il formaliser une règle SIER commune : **production toujours pinée sur une
image de release explicite, vérification `docker compose config --images` après
déploiement, et pas de cron de redémarrage Docker Compose sans justification
documentée ?**

Références : `descr/prod-deploy-runbook.md` et `descr/deployment.md`.
