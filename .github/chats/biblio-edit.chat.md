# Comparaison HTML `/fiches/biblio/edit/5948/`

## Conversation

**User:**  
Voici une comparaison détaillée entre les deux sources HTML pour `/fiches/biblio/edit/5948/` :

---

## 1. Différences numérotées et analyse

### 1.1. **Chemins des ressources statiques**
- **v2024** : `/site-media/` pour CSS, JS, images, favicon.
- **v2025** : `/static/` pour CSS, JS, images, favicon.
- **Analyse** : Migration vers la convention Django standard (`/static/`). Cela facilite la gestion des fichiers statiques et l’intégration avec les outils modernes.

---

### 1.2. **Structure du `<title>`**
- **v2024** : Titre sur une seule ligne, sans indentation.
- **v2025** : Titre multi-lignes, indentation, caractères spéciaux (`…` au lieu de `...`).
- **Analyse** : Amélioration de la lisibilité du code source, mais pas d’impact fonctionnel.

---

### 1.3. **Chargement de jQuery**
- **v2024** : jQuery chargé localement (`/site-media/js/lib/jquery/jquery.min.js`).
- **v2025** : jQuery chargé via CDN (`https://code.jquery.com/jquery-1.8.2.min.js`).
- **Analyse** : Utilisation d’un CDN peut améliorer la rapidité de chargement, mais dépend d’Internet.

---

### 1.4. **Scripts JavaScript**
- **v2024** : Beaucoup de scripts inline, certains dupliqués, code CSRF minifié.
- **v2025** : Scripts plus structurés, factorisés, code CSRF réécrit de façon plus lisible, suppression des doublons.
- **Analyse** : Refactoring pour clarté, maintenabilité et sécurité.

---

### 1.5. **Chemins et noms des fichiers CSS/JS**
- **v2024** : `/site-media/css/`, `/site-media/js/`
- **v2025** : `/static/css/`, `/static/js/`
- **Analyse** : Cohérence avec la migration des statiques.

---

### 1.6. **Ajout de `custom_overrides.css`**
- **v2025** uniquement.
- **Analyse** : Permet des surcharges CSS spécifiques sans toucher aux fichiers principaux.

---

### 1.7. **Formulaire de déconnexion**
- **v2024** : Lien `<a href="/accounts/logout/">Déconnexion</a>`
- **v2025** : Formulaire POST avec bouton, CSRF token inclus.
- **Analyse** : Amélioration de la sécurité (logout via POST recommandé).

---

### 1.8. **Champs du formulaire**
- **v2024** : Champs `input` et `textarea` classiques, certains champs dynamiques utilisent des noms différents (`lookup_contributiondoc_set-2-person`).
- **v2025** : Champs mieux typés (`type="number"` pour volume), noms de champs plus cohérents, certains champs dynamiques simplifiés.
- **Analyse** : Meilleure accessibilité, validation HTML5, simplification du markup.

---

### 1.9. **Gestion des mots-clés (keywords)**
- **v2024** : Les mots-clés secondaires affichent le label du mot-clé primaire.
- **v2025** : Pour certains mots-clés secondaires, le label du mot-clé primaire est vide (`<span class="pkw-label"></span>`).
- **Analyse** : Bug ou différence de gestion des mots-clés secondaires, à vérifier côté backend.

---

### 1.10. **Champs "Personne" (subj_person)**
- **v2024** : Plusieurs personnes déjà listées dans la fiche.
- **v2025** : Liste vide par défaut.
- **Analyse** : Différence de pré-remplissage, peut-être liée à la migration des données ou à un bug.

---

### 1.11. **Champs "Société/Académie"**
- **v2025** : Liste d’options plus longue, avec des doublons (ex : "Abbaye de l'Arc" apparaît deux fois).
- **Analyse** : Problème de duplication dans la génération des options, à corriger.

---

### 1.12. **Champs "Notes"**
- **v2024** : Champs `notebiblio_set-*`
- **v2025** : Champs `notes-*`
- **Analyse** : Renommage pour plus de clarté, mais nécessite adaptation du backend.

---

### 1.13. **Champs "Date"**
- **v2024** : Format `22-12-1706`, champ caché `date_f` avec `%d-%m-%Y`.
- **v2025** : Format `22.12.1706`, champ caché `date_f` avec `%d-%m-%y`.
- **Analyse** : Changement de séparateur et de format, peut impacter la validation ou l’affichage.

---

### 1.14. **Footer**
- **v2024** : Copyright 2013.
- **v2025** : Copyright 2013-2025, mention de la version Django.
- **Analyse** : Mise à jour pour refléter l’évolution du projet.

---

### 1.15. **Accessibilité et attributs HTML**
- **v2025** : Ajout d’attributs `required`, `maxlength`, `multiple`, etc.
- **Analyse** : Améliore la validation côté client et l’accessibilité.

---

### 1.16. **Suppression de certains scripts inline**
- **v2025** : Scripts de gestion de la toolbar, du menu, etc., sont factorisés et plus propres.
- **Analyse** : Meilleure maintenabilité.

---

### 1.17. **Champs cachés et gestion des formulaires**
- **v2024** : Champs cachés pour CSRF, gestion des formulaires Django classique.
- **v2025** : Champs cachés similaires, mais certains noms changent (`notes-*` vs `notebiblio_set-*`).
- **Analyse** : Cohérence à vérifier avec le backend.

---

## 2. Synthèse

La version 2025 apporte une modernisation technique et ergonomique :  
- **Migration des statiques** vers `/static/` (standard Django),  
- **Refactoring JS/CSS** pour plus de clarté et de sécurité,  
- **Amélioration de la sécurité** (logout via POST),  
- **Accessibilité accrue** (attributs HTML5),  
- **Quelques bugs/différences** à noter :  
  - Gestion des mots-clés secondaires (labels vides),  
  - Liste des personnes non pré-remplie,  
  - Doublons dans la liste des sociétés,  
  - Changement de format de date,  
  - Renommage de certains champs (`notes-*`).

**En résumé** :  
La v2025 va dans le sens des bonnes pratiques modernes (sécurité, accessibilité, maintenabilité), mais nécessite une vérification sur la gestion des données dynamiques (mots-clés, personnes, sociétés) et la compatibilité des formats de date et des noms de champs avec le backend. Quelques bugs d’affichage ou de duplication sont à corriger.

**Assistant:**  
*(No further response; the above is the exported conversation as