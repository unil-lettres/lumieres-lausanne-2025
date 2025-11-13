<!--
Copyright (C) 2010-2025 Université de Lausanne, RISET
<https://www.unil.ch/riset/>

This file is part of Lumières.Lausanne.
Lumières.Lausanne is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Lumières.Lausanne is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This copyright notice MUST APPEAR in all copies of the file.
-->

# Guide administrateur : Gestion des facsimilés IIIF

## Vue d'ensemble

Ce guide est destiné aux administrateurs et éditeurs qui gèrent les transcriptions et leurs facsimilés associés dans l'interface d'administration de Lumières.Lausanne.

## Table des matières

1. [Interface d'édition](#interface-dédition)
2. [Ajout d'une URL de manifeste IIIF](#ajout-dune-url-de-manifeste-iiif)
3. [Validation et prévisualisation](#validation-et-prévisualisation)
4. [Messages d'erreur et débogage](#messages-derreur-et-débogage)
5. [Gestion des facsimilés](#gestion-des-facsimilés)
6. [Bonnes pratiques](#bonnes-pratiques)

---

## Interface d'édition

L'interface d'édition des transcriptions comprend un champ dédié pour l'URL du manifeste IIIF, situé dans la section des métadonnées du document.

### Champ "Facsimile IIIF URL"

- **Libellé** : Facsimile IIIF URL
- **Type** : Champ URL
- **Requis** : Non (optionnel)
- **Aide** : URL du manifeste IIIF (doit pointer vers un fichier manifest.json ou info.json)

---

## Ajout d'une URL de manifeste IIIF

### Procédure standard

1. **Accédez à la page d'édition** de la transcription
2. **Localisez le champ** "Facsimile IIIF URL"
3. **Entrez l'URL complète** du manifeste IIIF
4. **Cliquez sur "Charger"** pour valider et prévisualiser

### Formats d'URL acceptés

L'URL doit pointer vers un manifeste IIIF valide :

**Exemples d'URLs valides :**
```
https://iiif.dcsr.unil.ch/iiif/2/patrinum-IG-9-81-2-007-050-recto.jp2/info.json
https://example.org/iiif/manuscript/manifest.json
https://gallica.bnf.fr/iiif/ark:/12148/btv1b8449691v/manifest.json
```

**Standards supportés :**
- IIIF Presentation API v2.0
- IIIF Presentation API v3.0
- IIIF Image API v2.0
- IIIF Image API v3.0

---

## Validation et prévisualisation

### État initial : Sans manifeste

![Champ vide, aucun manifeste](../img/transcription-edition-facsimile-no-manifest.png)

**État** : Champ vide, aucun visualiseur affiché

**Comportement** :
- Le bouton "Charger" est disponible
- Aucune prévisualisation n'est affichée
- La transcription s'affichera en mode texte seul côté public

### Chargement réussi

![Manifeste chargé avec succès](../img/transcription-edition-facsimile-loaded.png)

**État** : URL validée, visualiseur actif

**Comportement** :
- Le visualiseur OpenSeadragon s'affiche dans le panneau de droite
- Les contrôles de zoom et navigation sont fonctionnels
- Le champ URL est désactivé (grisé) pour éviter les modifications accidentelles
- Un champ caché conserve l'URL pour la soumission du formulaire
- Le bouton "Charger" se transforme en "Supprimer"

**Contrôles disponibles dans la prévisualisation :**
- **Zoom +/-** : Agrandir/réduire l'image
- **Home** : Réinitialiser la vue
- **Plein écran** : Agrandir le visualiseur
- **Navigateur miniature** : En haut à droite, aperçu de la page complète

### Validation échouée : Erreur 404

![Erreur 404 lors du chargement](../img/transcription-edition-facsimile-erreur-url-404.png)

**État** : URL invalide ou ressource non trouvée

**Message d'erreur affiché** :
```
Erreur lors du chargement du manifeste IIIF.
Vérifiez que l'URL est correcte et accessible.
```

**Causes possibles :**
1. **URL incorrecte** : Faute de frappe dans l'URL
2. **Ressource inexistante** : Le document n'existe pas sur le serveur IIIF
3. **Problème de chemin** : Le chemin vers le manifeste est incorrect
4. **Serveur inaccessible** : Le serveur IIIF est hors ligne ou inaccessible
5. **Problèmes de permissions** : Restrictions d'accès CORS

---

## Messages d'erreur et débogage

### Messages côté utilisateur

#### Erreur : "IIIF manifest URL is required"

**Contexte** : L'utilisateur clique sur "Charger" sans avoir saisi d'URL

**Solution** : Entrer une URL valide dans le champ avant de cliquer sur "Charger"

#### Erreur : "Failed to load manifest"

**Contexte** : La requête HTTP a échoué

**Causes possibles :**
- Problème réseau
- Serveur IIIF non disponible
- Timeout (délai dépassé)

**Solution** :
1. Vérifier la connexion Internet
2. Tester l'URL dans un navigateur séparé
3. Contacter l'administrateur du serveur IIIF

#### Erreur : "Invalid IIIF manifest format"

**Contexte** : Le fichier chargé n'est pas un manifeste IIIF valide

**Causes possibles :**
- L'URL pointe vers un fichier JSON non-IIIF
- Le manifeste est mal formé (JSON invalide)
- Version IIIF non supportée

**Solution** :
1. Vérifier que l'URL pointe vers un vrai manifeste IIIF
2. Tester le manifeste avec un validateur IIIF en ligne
3. Utiliser un manifeste conforme aux standards v2.0 ou v3.0

### Messages dans la console JavaScript

Pour accéder aux logs de débogage, ouvrir la **Console JavaScript** du navigateur :
- **Chrome/Edge** : F12 > onglet "Console"
- **Firefox** : F12 > onglet "Console"
- **Safari** : Cmd+Option+C

#### Logs de succès

```javascript
[Facsimile Viewer] Fetching IIIF manifest from: https://example.org/manifest.json
[Facsimile Viewer] Manifest loaded successfully
[Facsimile Viewer] IIIF version: 2.0
[Facsimile Viewer] Sequences found: 1
[Facsimile Viewer] Total canvases: 42
[Facsimile Viewer] OpenSeadragon viewer initialized
```

**Interprétation :**
- Le manifeste a été chargé avec succès
- Version IIIF détectée (2.0 ou 3.0)
- Nombre de séquences et de pages (canvases) trouvées
- Le visualiseur OpenSeadragon est initialisé

#### Logs d'erreur réseau

```javascript
[Facsimile Viewer] ERROR: Failed to fetch manifest
[Facsimile Viewer] HTTP Error: 404 Not Found
[Facsimile Viewer] URL: https://example.org/nonexistent.json
```

**Interprétation :**
- Erreur HTTP 404 : La ressource n'existe pas
- Vérifier l'URL et le chemin d'accès

```javascript
[Facsimile Viewer] ERROR: Network error
[Facsimile Viewer] CORS policy blocked the request
```

**Interprétation :**
- Problème CORS : le serveur IIIF ne permet pas les requêtes cross-origin
- **Solution** : Configurer les en-têtes CORS sur le serveur IIIF

#### Logs d'erreur de parsing

```javascript
[Facsimile Viewer] ERROR: Invalid JSON in manifest
[Facsimile Viewer] SyntaxError: Unexpected token < in JSON at position 0
```

**Interprétation :**
- Le fichier renvoyé n'est pas du JSON valide
- Peut arriver si l'URL pointe vers une page HTML d'erreur

```javascript
[Facsimile Viewer] ERROR: Missing required IIIF properties
[Facsimile Viewer] Expected 'sequences' or 'items' not found
```

**Interprétation :**
- Le JSON est valide mais ne contient pas les propriétés IIIF requises
- Le manifeste n'est pas conforme au standard IIIF

#### Logs d'erreur OpenSeadragon

```javascript
[OpenSeadragon] ERROR: Unable to load tile source
[OpenSeadragon] Invalid tile source format
```

**Interprétation :**
- Le visualiseur ne peut pas charger les tuiles d'image
- Problème avec le service d'images IIIF ou les URLs des tuiles

```javascript
[OpenSeadragon] WARN: Viewer container not found
[OpenSeadragon] Element ID: facsimile-viewer
```

**Interprétation :**
- Problème d'initialisation : le conteneur HTML n'existe pas
- Vérifier que l'élément `<div id="facsimile-viewer">` est présent dans la page

### Logs Django (côté serveur)

Les validations côté serveur génèrent des logs dans les fichiers Django.

**Emplacement des logs** : Selon la configuration `settings.py`

#### Validation réussie

```
[INFO] Validating IIIF manifest: https://example.org/manifest.json
[INFO] Manifest validation successful
[INFO] IIIF version: 2.1.1
```

#### Erreurs de validation

```
[ERROR] Failed to fetch IIIF manifest
[ERROR] URL: https://example.org/manifest.json
[ERROR] HTTPError: 404 Client Error: Not Found
```

```
[ERROR] Invalid IIIF manifest format
[ERROR] Missing required field: sequences
[ERROR] URL: https://example.org/manifest.json
```

```
[ERROR] Timeout while fetching manifest
[ERROR] URL: https://example.org/slow-server.com/manifest.json
[ERROR] Timeout: 10 seconds exceeded
```

**Configuration du timeout** :
Par défaut, le timeout est de 10 secondes (configurable dans `forms.py`)

---

## Gestion des facsimilés

### Modification d'une URL existante

Pour modifier une URL de facsimilé déjà enregistrée :

1. **Cliquez sur "Supprimer"** pour désactiver le visualiseur
2. Le champ URL redevient éditable
3. **Modifiez l'URL** ou supprimez-la complètement
4. **Cliquez sur "Charger"** pour valider la nouvelle URL
5. **Enregistrez** le formulaire

### Suppression d'un facsimilé

Pour retirer complètement le facsimilé d'une transcription :

1. **Cliquez sur "Supprimer"** si le visualiseur est chargé
2. **Videz le champ URL** complètement
3. **Enregistrez** le formulaire
4. La transcription s'affichera en mode texte seul côté public

### Sauvegarde du formulaire

**Important :** Même si le champ URL est désactivé (grisé) après le chargement, l'URL est bien préservée lors de la soumission grâce à un champ caché.

**Vérification** :
- Après sauvegarde, rechargez la page d'édition
- L'URL doit apparaître dans le champ et le visualiseur doit se charger automatiquement

---

## Bonnes pratiques

### Sources IIIF recommandées

**Serveurs IIIF de confiance :**
- Serveur IIIF de l'UNIL : `iiif.dcsr.unil.ch`
- Gallica (BnF) : `gallica.bnf.fr/iiif`
- Internet Archive : `iiif.archivelab.org`
- Bibliothèque numérique suisse : `iiif.e-codices.ch`

### Vérification avant ajout

Avant d'ajouter une URL de manifeste :

1. **Testez l'URL dans un navigateur** : Elle doit renvoyer du JSON valide
2. **Vérifiez avec un validateur IIIF** : [IIIF Validator](https://presentation-validator.iiif.io/)
3. **Testez dans Mirador ou Universal Viewer** : Visualiseurs IIIF en ligne pour tester

### Nommage et organisation

**Conventions suggérées :**
- Utiliser des URLs stables (permaliens)
- Préférer HTTPS à HTTP
- Documenter la source du manifeste dans les notes internes

### Performance et optimisation

**Recommandations :**
- Utiliser des serveurs IIIF performants (réponse < 2 secondes)
- Privilégier les manifestes bien structurés avec métadonnées complètes
- Éviter les manifestes avec trop de pages (> 500) si possible

### Accessibilité

**Points à vérifier :**
- Le manifeste contient-il des métadonnées descriptives ?
- Les images ont-elles une résolution suffisante (min. 300 DPI) ?
- Le serveur IIIF est-il fiable et disponible 24/7 ?

---

## Débogage avancé

### Test manuel d'un manifeste IIIF

**Étapes :**

1. **Copier l'URL du manifeste**
2. **Ouvrir un nouvel onglet** et coller l'URL
3. **Vérifier la réponse JSON** :
   - Doit être du JSON valide
   - Doit contenir `@context` avec une URL IIIF
   - Doit contenir `sequences` (v2.x) ou `items` (v3.x)

**Exemple de manifeste valide (v2.1) :**
```json
{
  "@context": "http://iiif.io/api/presentation/2/context.json",
  "@id": "https://example.org/iiif/book1/manifest",
  "@type": "sc:Manifest",
  "label": "Book 1",
  "sequences": [
    {
      "@type": "sc:Sequence",
      "canvases": [
        {
          "@id": "https://example.org/iiif/book1/canvas/p1",
          "@type": "sc:Canvas",
          "images": [...]
        }
      ]
    }
  ]
}
```

### Validation avec des outils externes

**IIIF Presentation Validator :**
- URL : https://presentation-validator.iiif.io/
- Copier/coller l'URL du manifeste
- Vérifier les erreurs et avertissements

**Mirador Viewer :**
- URL : https://projectmirador.org/
- Charger le manifeste pour tester l'affichage
- Vérifier que les images se chargent correctement

### Problèmes CORS

**Symptôme :** Message dans la console
```
Access to fetch at 'https://example.org/manifest.json' from origin 'https://lumieres-lausanne.ch' 
has been blocked by CORS policy
```

**Solution côté serveur IIIF :**
Le serveur doit renvoyer les en-têtes suivants :
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET
Access-Control-Allow-Headers: Content-Type
```

**Solution temporaire :**
- Contacter l'administrateur du serveur IIIF
- Utiliser un proxy CORS (pour tests uniquement)

### Inspection réseau

**Dans Chrome/Firefox DevTools :**

1. Ouvrir **F12 > Network** (Réseau)
2. Cliquer sur "Charger" pour déclencher la requête
3. Observer la requête vers le manifeste IIIF :
   - **Statut** : Doit être `200 OK`
   - **Type** : Doit être `application/json`
   - **Taille** : Vérifier que le fichier n'est pas vide
4. Cliquer sur la requête pour voir :
   - **Headers** : Vérifier les en-têtes CORS
   - **Preview** : Voir le JSON formaté
   - **Response** : Voir le JSON brut

---

## Dépannage spécifique

### Le visualiseur se charge en édition mais pas en affichage public

**Causes possibles :**
1. Le contexte de template n'inclut pas l'URL
2. Erreur JavaScript dans la page d'affichage
3. Fichiers statiques non chargés (OpenSeadragon manquant)

**Diagnostic :**
- Vérifier la console JavaScript sur la page publique
- Vérifier que `trans.facsimile_iiif_url` est bien passé au template
- Vérifier que `openseadragon.min.js` est chargé

### Le champ reste grisé après suppression

**Cause :** État JavaScript non réinitialisé

**Solution :**
1. Rafraîchir la page complète (F5)
2. Si le problème persiste, vider le cache du navigateur

### Les modifications ne sont pas sauvegardées

**Vérifications :**
1. Le formulaire a-t-il été soumis (bouton "Save" cliqué) ?
2. Y a-t-il des erreurs de validation sur d'autres champs ?
3. Vérifier les logs Django pour des erreurs de sauvegarde

---

## Référence technique

### Architecture du système

**Composants :**
- **Backend (Django)** : Validation serveur du manifeste IIIF
- **Frontend (JavaScript)** : Validation client et initialisation du visualiseur
- **OpenSeadragon** : Bibliothèque de visualisation Deep Zoom
- **Serveur IIIF** : Hébergement des images et manifestes

**Flux de données :**
1. Admin entre l'URL → Validation JavaScript (client)
2. Requête AJAX vers le manifeste IIIF → Parsing JSON
3. Si valide → Initialisation OpenSeadragon
4. Soumission du formulaire → Validation Django (serveur)
5. Sauvegarde en base de données
6. Affichage public → Chargement du manifeste → Affichage du visualiseur

### Fichiers concernés

**Backend :**
- `app/fiches/models/documents/document.py` : Modèle Transcription
- `app/fiches/forms.py` : TranscriptionForm avec validation
- `app/fiches/migrations/0009_add_facsimile_iiif_url.py` : Migration de la BDD

**Frontend :**
- `app/fiches/templates/fiches/edition/transcription.html` : Interface admin
- `app/fiches/templates/fiches/display/transcription.html` : Interface publique
- `app/fiches/static/fiches/js/transcription-sync.js` : Synchronisation des pages
- `app/static/js/lib/openseadragon/openseadragon.min.js` : Bibliothèque OpenSeadragon

**CSS :**
- `app/fiches/static/fiches/css/transcription.css` : Styles du visualiseur
- `app/fiches/static/fiches/css/display_base.css` : Styles généraux

---

## Ressources externes

### Documentation IIIF

- **IIIF Presentation API** : https://iiif.io/api/presentation/
- **IIIF Image API** : https://iiif.io/api/image/
- **Awesome IIIF** : https://github.com/IIIF/awesome-iiif

### Outils de validation

- **IIIF Validator** : https://presentation-validator.iiif.io/
- **JSON Validator** : https://jsonlint.com/

### Visualiseurs IIIF de référence

- **Mirador** : https://projectmirador.org/
- **Universal Viewer** : https://universalviewer.io/
- **OpenSeadragon** : https://openseadragon.github.io/

---

## Support et contact

En cas de problème persistant :

1. **Consulter les logs** (console JS + logs Django)
2. **Tester le manifeste** avec les outils de validation
3. **Vérifier la documentation** technique du projet
4. **Contacter l'équipe technique** RISET, UNIL

---

**Dernière mise à jour** : 13 novembre 2025  
**Branch** : `feat/facsimile-viewer`
