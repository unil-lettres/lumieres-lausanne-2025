# Playwright Tests - Facsimile Viewer

Tests automatisés pour valider le fonctionnement des 3 phases du refactorisation de la visionneuse de facsimilés sur Chrome, Firefox et Safari.

## 📋 Vue d'ensemble

Cette suite de tests valide :

- **Phase 2** : Refactorisation de la barre de navigation
  - Boutons en une seule ligne
  - Menu déroulant des options
  - Suppression du bouton sync
  
- **Phase 3** : Logique conditionnelle par mode
  - Attributs data pour disponibilité du contenu
  - Activation/désactivation des boutons
  - Menu options contextuel
  
- **Phase 4** : Persistance des options
  - Stockage sessionStorage des préférences
  - Restauration après rechargement
  - État persistant des cases à cocher

- **Accessibilité** : Vérifications WCAG
  - Attributs title sur les boutons
  - Navigation au clavier
  - Étiquetage des cases à cocher

- **Responsive** : Tests multi-résolutions
  - Mobile (320px)
  - Tablette (768px)
  - Desktop (1920px)

## 🔧 Installation

### 1. Installer les dépendances Playwright

```bash
pip install -r requirements-playwright.txt
```

### 2. Installer les navigateurs

```bash
playwright install
```

ou pour des navigateurs spécifiques :

```bash
playwright install chromium firefox webkit
```

## 🚀 Exécution des tests

### Tous les navigateurs

```bash
# Avec le script helper (recommandé)
./run-tests.sh --all

# Ou directement avec pytest
pytest tests/playwright/test_facsimile_viewer.py -v
```

### Navigateur spécifique

```bash
# Chrome uniquement
./run-tests.sh --chrome

# Firefox uniquement
./run-tests.sh --firefox

# Safari (WebKit) uniquement
./run-tests.sh --webkit
```

### Modes spéciaux

```bash
# Mode headless (par défaut)
./run-tests.sh --all

# Mode headed (affiche les navigateurs)
./run-tests.sh --all --headed

# Mode debug (pause interactive)
./run-tests.sh --all --debug

# Mode UI (interface interactive Playwright)
./run-tests.sh --all --ui

# Tests responsifs
./run-tests.sh --mobile
```

### Options pytest directes

```bash
# Tests spécifiques à une phase
pytest tests/playwright/test_facsimile_viewer.py::TestPhase2NavigationBar -v

# Tests avec marqueurs
pytest tests/playwright/test_facsimile_viewer.py -m "phase2" -v
pytest tests/playwright/test_facsimile_viewer.py -m "accessibility" -v

# Tests d'un navigateur spécifique
pytest tests/playwright/test_facsimile_viewer.py -k "chromium" -v
pytest tests/playwright/test_facsimile_viewer.py -k "firefox" -v
pytest tests/playwright/test_facsimile_viewer.py -k "webkit" -v

# Afficher les impressions (print statements)
pytest tests/playwright/test_facsimile_viewer.py -v -s

# Arrêter au premier échec
pytest tests/playwright/test_facsimile_viewer.py -x

# Afficher les tests sans les exécuter
pytest tests/playwright/test_facsimile_viewer.py --collect-only
```

## 📊 Structure des tests

```
tests/playwright/
├── test_facsimile_viewer.py     # Suite principale
│   ├── TestPhase2NavigationBar      (8 tests)
│   ├── TestPhase3ModeConditionalLogic (4 tests)
│   ├── TestPhase4OptionsPersistence (3 tests)
│   ├── TestAccessibility            (2 tests)
│   └── TestResponsive               (3 tests)
└── __init__.py
```

### Couverture des tests

- **Phase 2** (8 tests × 3 navigateurs = 24 tests)
  - ✅ Affichage des boutons en une ligne
  - ✅ Mode split-view actif par défaut
  - ✅ Changement de mode au clic
  - ✅ Accessibilité du menu options
  - ✅ Toggle du menu options
  - ✅ Fermeture du menu au clic externe
  - ✅ Rotation de la flèche du menu
  - ✅ Absence du bouton sync

- **Phase 3** (4 tests × 3 navigateurs = 12 tests)
  - ✅ Présence des attributs data
  - ✅ Activation des boutons si contenu disponible
  - ✅ Mise à jour du menu options par mode
  - ✅ Désactivation des boutons si contenu manquant

- **Phase 4** (3 tests × 3 navigateurs = 9 tests)
  - ✅ Persistance de l'état des cases à cocher
  - ✅ Restauration après rechargement
  - ✅ Toggle multiple des cases à cocher

- **Accessibilité** (2 tests × 3 navigateurs = 6 tests)
  - ✅ Attributs title sur les boutons
  - ✅ Étiquetage des cases à cocher

- **Responsive** (3 tests × 3 navigateurs = 9 tests)
  - ✅ Mobile (320px)
  - ✅ Tablette (768px)
  - ✅ Desktop (1920px)

**Total : 60+ tests sur 3 navigateurs**

## 🌍 Variables d'environnement

```bash
# URL de base pour les tests (défaut: http://localhost:8000)
export PLAYWRIGHT_TEST_BASE_URL="http://localhost:8000"

# Chemin racine du projet Django (défaut: ./app)
export APP_ROOT="./app"

# ID de transcription à tester (défaut: 1080)
# Modifiable dans le fichier test_facsimile_viewer.py
```

## 🔍 Débogage

### Mode headed (affiche le navigateur)

```bash
./run-tests.sh --all --headed
```

### Mode debug (pause interactive)

```bash
./run-tests.sh --all --debug
```

### Mode UI (interface Playwright)

```bash
./run-tests.sh --all --ui
```

### Obtenir les traces d'exécution

```bash
pytest tests/playwright/test_facsimile_viewer.py --trace on
```

### Afficher les vidéos de test

Les vidéos sont sauvegardées en cas d'échec :
```
test-results/
├── test_*_videos/
│   └── *.webm
└── ...
```

## 📝 Rapport des résultats

Les résultats sont générés dans `test-results/` :

```
test-results/
├── junit.xml              # Format JUnit (CI/CD compatible)
├── results.json           # Format JSON (parsing)
├── index.html             # Rapport HTML (navigateur)
└── test_*/
    ├── *.png              # Screenshots en cas d'erreur
    └── videos/            # Vidéos en cas d'erreur
```

### Voir le rapport HTML

```bash
# Sur macOS
open test-results/index.html

# Sur Linux
xdg-open test-results/index.html

# Ou via le script
./run-tests.sh --all --report
```

## ✅ Critères de succès

Les tests passent quand :

### Phase 2 ✅
- [ ] 4 boutons visibles en une ligne (text, split, viewer, options)
- [ ] Mode split-view actif par défaut
- [ ] Clic sur bouton change le mode activement
- [ ] Menu options s'ouvre/ferme au clic
- [ ] Clic externe ferme le menu
- [ ] Flèche tourne à l'ouverture
- [ ] Pas de bouton sync visible

### Phase 3 ✅
- [ ] Attributs `data-has-facsimile` et `data-has-transcription` présents
- [ ] Tous les boutons activés si contenu complet disponible
- [ ] Menu options mis à jour selon le mode
- [ ] Boutons désactivés si contenu manquant

### Phase 4 ✅
- [ ] État des cases à cocher persisté dans sessionStorage
- [ ] Restauration après rechargement page
- [ ] Plusieurs cases à cocher gérables

### Accessibilité ✅
- [ ] Tous les boutons ont des attributs title
- [ ] Cases à cocher correctement étiquetées

### Responsive ✅
- [ ] Layout fonctionnel à 320px
- [ ] Layout fonctionnel à 768px
- [ ] Layout fonctionnel à 1920px

## 🐛 Troubleshooting

### Les tests ne trouvent pas localhost:8000

```bash
# Démarrer le serveur Django dans un terminal
cd app
python manage.py runserver 0.0.0.0:8000

# Dans un autre terminal
./run-tests.sh --all
```

### Playwright n'est pas installé

```bash
pip install -r requirements-playwright.txt
playwright install
```

### Certains navigateurs ne sont pas installés

```bash
# Installer tous les navigateurs
playwright install

# Ou spécifiquement
playwright install chromium
playwright install firefox
playwright install webkit
```

### Tests échouent sur Safari (WebKit)

Safari nécessite parfois des délais supplémentaires :
- Les tests incluent `wait_for_load_state("networkidle")`
- Vérifier que la machine a assez de mémoire RAM

## 📚 Documentation

- [Playwright Python API](https://playwright.dev/python/)
- [pytest documentation](https://docs.pytest.org/)
- [Test fixtures et parameterization](https://docs.pytest.org/en/stable/fixture.html)

## 👥 Contributeurs

- Xavier Beheydt <xavier.beheydt@unil.ch>

## 📄 Licence

GPL-3.0-or-later

Voir [LICENSE](../../LICENSE) pour plus d'informations.
