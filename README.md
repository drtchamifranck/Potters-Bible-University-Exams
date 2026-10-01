# Potter's Bible University — ISTS Campus

Système de gestion des dossiers étudiants et des examens du **Rectorat ISTS**
(Potter's Bible University). L'application permet de consulter, compléter et
auditer les dossiers étudiants, de gérer les sauvegardes et de suivre les
demandes du rectorat.

---

## Sommaire

- [Aperçu](#aperçu)
- [Structure du dépôt](#structure-du-dépôt)
- [Démarrage rapide](#démarrage-rapide)
- [Conventions de code](#conventions-de-code)
- [Accessibilité](#accessibilité)
- [Contribution](#contribution)
- [Licence](#licence)

## Aperçu

| Écran | Description |
| --- | --- |
| Vue d'ensemble | Indicateurs de la base, intégrité des dossiers, actions rapides |
| Étudiants | Fiches et inscriptions |
| Dossiers | Consultation, complétion et audit des dossiers |
| Sauvegardes | Export, import et vérification des archives |
| Journal | Historique des opérations |

## Structure du dépôt

```
.
├── design/
│   ├── index.html                       # Maquette de l'écran « Vue d'ensemble » (autonome)
│   ├── comparaison.html                 # Avant / après, côte à côte
│   ├── ists-design-system.css           # Design system extrait (généré)
│   └── ists-design-system.scope.css     # Version portée par .ists-v9 (généré)
├── docs/
│   └── integration-v8.md                # Procédure d'intégration à l'application V8
├── tools/
│   ├── audit-ui.mjs                     # Audit qualité d'interface (sans dépendance)
│   ├── extraire-design-system.py        # Génère les deux feuilles CSS
│   └── integrer-refonte.py              # Intègre la refonte dans un fichier existant
├── tests/
│   ├── fixtures/avant-v8.html           # Banc d'essai reproduisant l'écran avant refonte
│   └── verifier-outils.sh               # 21 contrôles automatiques
└── README.md
```

> `design/` contient des maquettes de référence : elles ne dépendent d'aucune
> bibliothèque externe et s'ouvrent directement dans un navigateur.

## Démarrage rapide

Ouvrir la maquette :

```bash
python3 -m http.server 8000 --directory design
# puis http://localhost:8000
```

## Outils

### Audit qualité d'interface

Contrôle automatique d'un écran avant intégration : emojis utilisés comme
icônes, libellés tronqués, largeurs fixes qui débordent, contour de focus
supprimé, bouton-icône sans nom accessible, image sans `alt`, `viewport` ou
`lang` manquants, hiérarchie de titres discontinue, et **action proposée deux
fois** — y compris lorsque les libellés diffèrent (« Récupérer TOUT » d'un
côté, « Récupération complète » de l'autre).

```bash
node tools/audit-ui.mjs design/index.html        # rapport lisible
node tools/audit-ui.mjs --json design/index.html # sortie JSON (CI)
```

Le code de sortie vaut `1` si au moins une **erreur** est détectée : le script
peut donc servir de garde-fou dans une chaîne d'intégration continue.

### Extraction du design system

```bash
python3 tools/extraire-design-system.py
```

Régénère les deux feuilles CSS à partir de la maquette, afin qu'il n'existe
qu'une seule source de vérité :

- `ists-design-system.css` — version brute, telle qu'utilisée par la maquette ;
- `ists-design-system.scope.css` — version **portée** : sélecteurs préfixés par
  `.ists-v9`, jetons renommés `--ists-…`. Elle est sans effet en dehors du
  conteneur `ists-v9`, donc inoffensive dans une application existante.

### Intégration dans une application existante

```bash
python3 tools/integrer-refonte.py app.html              # simulation (n'écrit rien)
python3 tools/integrer-refonte.py app.html --appliquer  # écriture + sauvegarde .bak
```

Remplace les emojis-icônes par des icônes SVG, injecte la bibliothèque
d'icônes et le design system porté. Ne touche ni au JavaScript, ni aux `id`,
ni aux `onclick`. Opération idempotente et réversible.

Procédure détaillée : **[docs/integration-v8.md](docs/integration-v8.md)**.

### Contrôles automatiques

```bash
bash tests/verifier-outils.sh
```

Vérifie la chaîne complète sur un banc d'essai (`tests/fixtures/avant-v8.html`)
qui reproduit l'écran avant refonte : détection des défauts, intégration,
préservation du code applicatif, idempotence, cloisonnement du CSS.

## Conventions de code

- **Aucun emoji dans l'interface.** Toutes les icônes sont des SVG *inline*
  (trait `currentColor`, grille 24 × 24), regroupées dans une `<defs>` unique.
- **Aucune largeur fixe.** Les mises en page utilisent `grid`, `minmax(0, 1fr)`
  et `flex-wrap` : jamais de barre horizontale, même sur écran étroit.
- **Aucun texte tronqué.** Les libellés se replient (`white-space: normal`)
  au lieu d'être coupés par `overflow: hidden`.
- **Design system par jetons.** Couleurs, rayons et espacements sont des
  variables CSS définies dans `:root`, avec variante sombre automatique.
- **Thème clair/sombre** piloté par `prefers-color-scheme`.

## Accessibilité

Objectif : conformité **WCAG 2.1 niveau AA**.

- Hiérarchie de titres continue (`h1` → `h2` → `h3`) ;
- navigation clavier complète, anneau de focus visible ;
- contrastes vérifiés en thème clair et sombre ;
- zones tactiles ≥ 40 px, libellés `aria-label` sur les boutons-icônes ;
- information jamais portée par la seule couleur (badges + libellés) ;
- respect de `prefers-reduced-motion`.

## Contribution

1. Créer une branche : `git checkout -b feat/nom-de-la-fonctionnalite`
2. Commiter avec un message clair (format [Conventional Commits](https://www.conventionalcommits.org/fr/)) :
   `feat(design): refonte de l'écran Vue d'ensemble`
3. Ouvrir une *pull request* en décrivant le besoin et en joignant une capture
   avant/après pour tout changement d'interface.

## Licence

© Potter's Bible University — Rectorat ISTS. Tous droits réservés.
