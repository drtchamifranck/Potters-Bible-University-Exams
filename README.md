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
├── design/            # Maquettes et design system (HTML/CSS autonome)
│   └── index.html     # Écran « Vue d'ensemble » — refonte professionnelle
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
