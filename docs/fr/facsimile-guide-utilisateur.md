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

# Guide d'utilisation du visualiseur de facsimilés

## Vue d'ensemble

Ce guide explique comment utiliser le visualiseur de facsimilés IIIF dans Lumières.Lausanne pour consulter les transcriptions avec leurs images originales.

## Table des matières

1. [Modes d'affichage](#modes-daffichage)
2. [Utilisation du visualiseur](#utilisation-du-visualiseur)
3. [Navigation dans les facsimilés](#navigation-dans-les-facsimilés)
4. [Dépannage](#dépannage)

---

## Modes d'affichage

En haut de chaque page de transcription, vous trouverez trois boutons permettant de changer le mode d'affichage :

- **📄 Texte seul** : Affiche uniquement la transcription
- **📄🖼️ Texte + Facsimilé** : Affiche la transcription et le facsimilé côte à côte
- **🖼️ Facsimilé seul** : Affiche uniquement le facsimilé en pleine largeur

### Mode Texte seul

![Affichage en mode texte seul](../img/transcription-display-text-only-marginal-note.png)

**Quand l'utiliser :**
- Pour lire confortablement la transcription
- Pour effectuer des recherches dans le texte
- Pour copier du contenu texte
- Sur des écrans de petite taille

**Caractéristiques :**
- Le texte occupe toute la largeur de la page
- Les notes marginales sont affichées en ligne
- Meilleure lisibilité pour la lecture continue

### Mode Texte + Facsimilé (vue partagée)

![Vue côte à côte texte et facsimilé](../img/transcription-display-text+facsimile.png)

**Quand l'utiliser :**
- Pour comparer la transcription avec l'original
- Pour vérifier des passages difficiles à déchiffrer
- Pour étudier la mise en page originale

**Caractéristiques :**
- La transcription apparaît à gauche (60% de la largeur)
- Le visualiseur de facsimilé apparaît à droite (40% de la largeur)
- Le visualiseur reste visible pendant le défilement du texte
- Navigation indépendante dans le facsimilé (zoom, déplacement)

### Mode Facsimilé seul

![Affichage en mode facsimilé seul](../img/transcription-display-facsimile-only.png)

**Quand l'utiliser :**
- Pour examiner le document source en détail
- Pour étudier des éléments visuels (illustrations, ornements)
- Pour agrandir fortement l'image et voir les détails fins

**Caractéristiques :**
- Le visualiseur occupe toute la largeur de la page
- Possibilité de zoom maximal pour voir tous les détails
- Idéal pour l'examen paléographique ou codicologique

---

## Utilisation du visualiseur

### Contrôles disponibles

Le visualiseur OpenSeadragon offre plusieurs moyens de navigation :

#### Zoom

- **Molette de la souris** : Faire défiler pour zoomer/dézoomer
- **Boutons + et -** : Cliquer pour zoomer/dézoomer progressivement
- **Double-clic** : Zoomer sur un point précis

#### Déplacement

- **Clic et glisser** : Maintenir le bouton de la souris et déplacer pour parcourir l'image

#### Autres contrôles

- **🏠 Bouton Home** : Réinitialiser le zoom et la position par défaut
- **Miniature de navigation** : En haut à droite, montre la zone actuellement visible

### Fonctionnalités avancées

#### Zoom progressif (Deep Zoom)

Le visualiseur charge progressivement des images de plus haute résolution au fur et à mesure que vous zoomez. Vous pouvez :
- Zoomer jusqu'à voir les détails les plus fins du document
- Observer les filigranes du papier
- Examiner les détails de l'encre et de l'écriture

---

## Navigation dans les facsimilés

### Documents multi-pages

Lorsque le document comporte plusieurs pages :

1. Les numéros de page dans la transcription sont cliquables
2. Cliquer sur un numéro de page charge automatiquement l'image correspondante
3. Le visualiseur se synchronise avec votre position dans le texte

### Miniature de navigation

La petite miniature en haut à droite du visualiseur :
- Montre l'ensemble de la page
- Indique la zone actuellement visible (rectangle rouge)
- Permet de se déplacer rapidement en cliquant sur une zone

---

## Dépannage

### Le facsimilé ne s'affiche pas

**Causes possibles :**
- Aucune image n'est associée à cette transcription
- Problème de connexion réseau
- Le serveur d'images est temporairement indisponible

**Solutions :**
1. Vérifiez votre connexion Internet
2. Rafraîchissez la page (F5)
3. Essayez de basculer vers le mode texte seul puis de revenir au mode avec facsimilé

### L'image est floue

**Cause :** Les images haute résolution sont en cours de chargement

**Solutions :**
- Attendez quelques secondes que le chargement se termine
- Sur une connexion lente, le chargement peut prendre plus de temps
- Les tuiles haute résolution se chargent progressivement

### Les contrôles ne fonctionnent pas

**Solutions :**
1. Rafraîchissez la page
2. Vérifiez que JavaScript est activé dans votre navigateur
3. Essayez un autre navigateur (Chrome, Firefox, Safari, Edge)

---

## Conseils d'utilisation

### Pour la lecture

- Utilisez le **mode texte seul** pour une lecture fluide
- Basculez vers le **mode partagé** pour vérifier des passages difficiles
- Ajustez la taille du texte du navigateur si nécessaire (Ctrl/Cmd + ou -)

### Pour la recherche

- Le **mode texte seul** permet d'utiliser la recherche du navigateur (Ctrl/Cmd + F)
- Utilisez le **mode partagé** pour localiser les passages dans l'original
- Les numéros de page facilitent les citations et références

### Pour l'étude approfondie

- Le **mode facsimilé seul** offre la meilleure vue pour l'analyse visuelle
- Zoomez au maximum pour examiner les détails paléographiques

---

## Compatibilité navigateurs

Le visualiseur fonctionne sur :

- ✅ **Chrome/Chromium** (version récente)
- ✅ **Firefox** (version récente)
- ✅ **Safari** (version récente)
- ✅ **Edge** (version récente)

Les anciens navigateurs (Internet Explorer 11 et antérieurs) ne sont pas supportés.

---

## Accessibilité

- Tous les contrôles sont accessibles au clavier
- Les images peuvent être agrandies pour les personnes malvoyantes
- Le mode texte seul permet l'utilisation de lecteurs d'écran
- Les contrastes sont optimisés pour la lisibilité

---

**Dernière mise à jour** : 13 novembre 2025
