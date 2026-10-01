# Intégrer la refonte dans l'application ISTS Campus V8

Ce guide décrit l'intégration de l'écran **Vue d'ensemble** refondu
(`design/index.html`) dans l'application existante
`ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html`.

**Périmètre retenu : un seul écran. Le JavaScript n'est pas touché.**

---

## 1. Garanties apportées

L'intégration est conçue pour être réversible et sans effet de bord :

| Garantie | Comment elle est assurée |
| --- | --- |
| Rien n'est modifié par accident | La commande par défaut est une **simulation** ; l'écriture exige `--appliquer`. |
| Aucun retour en arrière impossible | Un fichier `.bak` est créé avant toute écriture. |
| Aucun conflit de style | Le design system est **porté** : chaque sélecteur est préfixé par `.ists-v9`, chaque jeton devient `--ists-…`. Hors de ce conteneur, la feuille n'a aucun effet. |
| Aucun conflit de noms | Icônes et variables préfixées `ists-`. |
| Aucun doublon | L'injection est **idempotente** : un second passage n'ajoute rien. |
| Votre logique est préservée | Aucun `id`, `class`, `onclick` ni bloc `<script>` n'est modifié. |
| Vérifiable | `bash tests/verifier-outils.sh` exécute 21 contrôles automatiques. |

---

## 2. Mode opératoire

### Étape 1 — État des lieux

```bash
node tools/audit-ui.mjs "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
```

L'audit liste, ligne par ligne, les défauts de finition : emojis-icônes,
libellés tronqués, largeurs fixes, focus clavier supprimé, `viewport` ou `lang`
manquants. Code de sortie `1` si des erreurs subsistent.

### Étape 2 — Simulation

```bash
python3 tools/integrer-refonte.py "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
```

Affiche ce qui **serait** fait : emojis remplacés, blocs injectés, emojis non
reconnus à traiter à la main. Aucun fichier n'est écrit.

### Étape 3 — Application

```bash
python3 tools/integrer-refonte.py "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html" --appliquer
```

Trois transformations mécaniques :

1. chaque emoji-icône devient une icône SVG (`<svg class="ists-icon">`) ;
2. la bibliothèque de 20 icônes est injectée avant `</body>` ;
3. le design system porté est injecté avant `</head>`.

Une sauvegarde `…html.bak` est créée.

### Étape 4 — Activer la refonte sur l'écran

Ajoutez la classe `ists-v9` sur le conteneur de l'écran Vue d'ensemble :

```html
<section class="ists-v9">   <!-- était : <div id="vue-ensemble"> -->
  …
</section>
```

Tant que cette classe est absente, **rien ne change** visuellement : le CSS
injecté reste inactif. C'est le point de bascule, et il est réversible.

### Étape 5 — Remplacer le contenu de la section

Reprenez la structure de `design/index.html` (bandeau d'intégrité, indicateurs
clés, actions rapides, tableau des champs à compléter) en rebranchant vos
fonctions existantes sur les nouveaux boutons :

| Action dans la maquette | À relier à votre fonction |
| --- | --- |
| Récupérer maintenant | appel existant « récupérer les champs manquants » |
| Tout récupérer | recherche complète dans l'historique |
| Voir le détail | liste détaillée des champs |
| Télécharger une sauvegarde | export de la base |
| Importer une sauvegarde | import d'une archive |
| Auditer les dossiers | contrôle d'intégrité |
| Vérifier les demandes | nouvelles demandes |

Libellés professionnalisés au passage : `Récupérer TOUT (recherche complète)`
devient **« Tout récupérer »**, et les majuscules criardes disparaissent.

> Le bandeau `<div class="band" id="demo-band">` en tête de la maquette est un
> repère de maquette : **supprimez-le** lors de l'intégration.

### Étape 6 — Vérification

```bash
node tools/audit-ui.mjs "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
bash tests/verifier-outils.sh
```

Objectif : plus aucune erreur d'audit, et 21/21 contrôles réussis.

### Retour arrière

```bash
mv "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html.bak" \
   "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
```

---

## 3. Ce qui reste à faire à la main

L'intégration automatique traite les icônes et la couche visuelle. Trois
défauts structurels doivent être corrigés dans votre fichier d'origine :

| Défaut | Correction |
| --- | --- |
| `<meta name="viewport">` absent | L'ajouter dans `<head>` : sans lui, l'affichage mobile est celui d'un site des années 2000, zoomé et débordant. |
| `<html>` sans attribut `lang` | Ajouter `lang="fr"` (lecteurs d'écran, correcteur orthographique). |
| `button:focus{outline:none}` | Remplacer par un anneau visible via `:focus-visible` — condition d'accessibilité clavier. |
| Largeurs en dur (`width:320px`) et libellés `nowrap` tronqués | Remplacer par `minmax(0, 1fr)` et laisser les libellés revenir à la ligne. |

Ces quatre points sont exactement ceux que l'audit signale encore après
l'intégration.

---

## 4. Correspondance des icônes

| Ancien emoji | Icône | Usage |
| --- | --- | --- |
| 🔍 🔎 | `ists-i-search` | recherche, vérification |
| 📥 ⬇️ | `ists-i-download` | télécharger une sauvegarde |
| 📤 ⬆️ | `ists-i-upload` | importer une sauvegarde |
| 🩺 | `ists-i-filecheck` | audit des dossiers |
| 🔔 | `ists-i-bell` | demandes en attente |
| 🏛️ | `ists-i-info` | rectorat, information |
| 💾 | `ists-i-database` | base de données |
| 🗂️ | `ists-i-folder` | dossiers |
| 👥 | `ists-i-users` | étudiants |
| 🎓 | `ists-i-cap` | accès cours |
| ✅ ⚠️ 🔄 🛡️ ❌ ➡️ | `ists-i-check`, `ists-i-alert`, `ists-i-refresh`, `ists-i-shield`, `ists-i-x`, `ists-i-arrow` | états et actions |

Toute icône absente de cette table est signalée par le script dans la rubrique
« emojis non reconnus », afin qu'aucune ne passe inaperçue.
