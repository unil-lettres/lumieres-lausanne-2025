# Validation des demandes de Béatrice — 31 juillet 2026

## Sources

- `LL Debbugage 07.2026.docx` daté du 15 juillet 2026.
- `LL détail des STATUTS revus 2026.07.xls` enregistré par Béatrice le
  15 juillet 2026.
- Branche de Xavier `feat/named_entities`, commit validé `5f28e22`.
- Branche combinée `staging/named_entities`.

Les deux fichiers bureautiques restent dans le dossier de travail isolé de
Xavier et ne sont pas copiés dans Git. Le mot de passe de test présent dans le
XLS n'est pas reproduit ici.

## Résultat d'acceptation

| Demande | Validation redondante | Résultat |
| --- | --- | --- |
| Auteur et dernière modification automatiques sur la fiche lieu | Tests de vue, POST réel Chrome, contrôle du rendu final | Conforme |
| Sauvegarde d'une fiche lieu par le Directeur sans « Accès non autorisé » | Permissions, GET, POST d'une fiche appartenant à un tiers, parcours Chrome | Conforme |
| Sites de référence l'un sous l'autre et identifiant modifiable | HTML du widget, nettoyage du champ, POST/DB, mise à jour du lien en direct et persistance Chrome | Conforme |
| Catégorie affichée avec le titre et les lieux associés | Tests de rendu et fiche Chrome | Conforme |
| Note « Utilisateurs » visible en consultation après connexion | Tests anonyme/connecté/public et fiche Chrome | Conforme |
| Droits des fiches lieu par statut | Matrice comportementale Utilisateur, Étudiant, Chercheur, Doctorant et Directeur | Conforme pour le périmètre fiche lieu |
| Références d'une fiche lieu : seul le titre est lié; manuscrits puis littérature primaire puis secondaire | Requêtes, ordre, sous-sections et HTML final | Conforme |
| Bouton de tagging lieu plus visible avec un globe | Chargement CKEditor réel; bouton « Lier un lieu » et icône 16×16 contrôlés dans Chrome | Conforme |
| Personne taguée dans une transcription visible sur sa fiche | Cas publié/non publié, autre personne, dédoublonnage et rendu Chrome dans « Littérature primaire > Manuscrit » | Conforme |
| Création de personnes/lieux depuis le tagging réservée au Directeur | Permissions fonctionnelles dédiées, commande de rôles, interface et endpoints refusé/autorisé | Conforme — « admin » est interprété comme Directeur LL pour cette fonction, sans privilèges d'administration technique |
| Littérature secondaire non indexable par les champs de lieu | Formulaire, conservation du texte sans tag, destination conservée, passage primaire→secondaire et disparition de la fiche lieu | Conforme |
| Index A–Z de la liste des lieux ne reste plus bloqué | Marquage HTML, filtre serveur, clic Chrome avec navigation `?q=B`, aucun XHR/fetch parasite | Conforme |

## Exécutions

- Branche Xavier isolée : `746 passed`.
- Première branche combinée : `754 passed`.
- Tests d'acceptation ciblés ajoutés : `47 passed`, plus `5 subtests`.
- Suite complète finale : `759 passed`, plus `5 subtests`.
- Après ajout du rôle `civilistes` et des garde-fous d'interface : `777` tests
  et `5` sous-tests exécutés avec succès; Ruff ciblé conforme.
- Contrôles Django : `manage.py check` sans erreur; aucune migration manquante.
- Chrome local : parcours A–Z, fiche lieu lecture/édition/sauvegarde,
  référentiel modifié, note connectée, métadonnées de fiche, fiche personne et
  barre CKEditor; aucune erreur console sur les parcours finaux.
- Parcours MCP final avec un Civiliste non-staff : tagging réel d'une personne
  et d'un lieu existants avec persistance en base, upload/édition/suppression
  d'un PDF réel, masquage d'une note confidentielle, consultation d'une
  transcription publiée avec édition refusée, et absence des boutons d'édition
  ou suppression trompeurs. Toutes les fixtures et le média uploadé ont ensuite
  été supprimés du clone local.

## Limites et portes de validation

- La matrice XLS décrit aussi des droits généraux sur les projets,
  bibliographies, transcriptions et documents joints. Seules les lignes
  modifiées ou dépendantes des travaux de Xavier ont été revalidées ici; ce
  document ne prétend pas recertifier toute la politique d'autorisation du
  site.
- La validation fonctionnelle humaine de Béatrice reste requise sur staging,
  en particulier pour le jugement visuel et le contenu bibliographique réel.
- Aucun déploiement staging ou production n'a été effectué pendant cette
  validation.

## Checklist avant mise en staging de la branche Xavier

### Intégration et validation automatisée

- [x] Intégrer le dernier commit validé de Xavier dans
  `staging/named_entities`.
- [x] Intégrer les corrections incontestables de propriété et de confidentialité
  pour les bibliographies, transcriptions, pièces jointes, collections privées
  et notes.
- [x] Ajouter les permissions dédiées de création d'autorités depuis le tagging.
- [x] Faire passer la suite complète locale, les tests d'acceptation redondants,
  les contrôles de migration et la CI GitHub.
- [x] Vérifier puis rafraîchir additivement le backup local canonique de
  production, sans écriture en production et sans suppression locale.

### Nouveau rôle métier « civilistes » — porte bloquante

- [x] Créer un groupe Django `civilistes`, distinct de `directeurs` et de
  l'administration technique.
- [x] Lui permettre de consulter les contenus de travail, de modifier les
  bibliographies et transcriptions nécessaires, de taguer les autorités
  existantes, de renseigner pagination/IIIF et d'ajouter les pièces jointes
  nécessaires.
- [x] Ne pas lui accorder la suppression des objets d'autrui, le transfert de
  propriété, la publication/validation finale, la visibilité générale des notes
  confidentielles, la gestion des utilisateurs/groupes ni l'accès au Django
  admin.
- [x] Garder la création directe d'une nouvelle personne ou d'un nouveau lieu
  depuis le tagging sous validation du Directeur LL; le civiliste peut utiliser
  une autorité existante mais ne crée pas seul une nouvelle autorité.
- [x] Ajouter une matrice de tests positifs et négatifs pour `civilistes`, avec
  un compte dédié et sans héritage accidentel de `directeurs`.
- [x] Faire signaler par le préflight tout compte cumulant `civilistes` avec
  `directeurs`, `is_staff` ou `is_superuser`, sans modifier automatiquement ses
  appartenances.
- [ ] Faire valider par Béatrice sur staging les parcours « tagging existant »,
  « demande de nouvelle autorité », « pagination/IIIF », « pièce jointe » et
  « soumission au Directeur LL ».
- [ ] Après validation seulement, préparer comme opération de production
  séparée la réaffectation des civilistes actuellement placés dans des groupes
  trop larges; aucune modification de compte de production ne fait partie du
  déploiement staging.

### Déploiement et validation staging

- [ ] Rétablir et confirmer l'accès à `plt-tst-2.unil.ch` puis effectuer le
  préflight en lecture seule de `/var/www/lumieres2` et du projet Compose
  `lumieres-staging`.
- [ ] Créer le bundle de rollback staging avant tout changement.
- [ ] Déployer une image immuable construite depuis le commit final incluant le
  rôle `civilistes`.
- [ ] Appliquer les migrations, `collectstatic`, `sync_status_roles --apply` et
  reconstruire l'index Solr.
- [ ] Exiger qu'un dernier `sync_status_roles` ne signale aucun conflit de
  compte Civiliste avant d'ouvrir la validation fonctionnelle.
- [ ] Exécuter les tests fonctionnels avec des comptes isolés Directeur LL,
  Civiliste, Doctorant, Chercheur et utilisateur sans rôle.
- [ ] Obtenir la validation fonctionnelle finale de Béatrice avant toute
  préparation de mise en production.
