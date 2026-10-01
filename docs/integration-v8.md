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
| Vérifiable | `bash tests/verifier-outils.sh` exécute 24 contrôles automatiques. |

---

## 2. Deux voies possibles

| Voie | Pour qui | Effort |
| --- | --- | --- |
| **A. Copier-coller** (recommandée) | Vous, sans outil ni ligne de commande | Coller un bloc dans votre fichier |
| **B. Outil automatique** | Intégration scriptée, reproductible | Trois commandes |

Les deux produisent le même écran et utilisent les mêmes identifiants : elles
ne peuvent pas se dupliquer si vous passez de l'une à l'autre.

### Voie A — coller le bloc

Le fichier **[bloc-vue-ensemble.html](bloc-vue-ensemble.html)** contient la
section complète : programme de style, vingt et une icônes SVG et structure.

0. Regardez le résultat attendu dans `docs/apercu-bloc.html` — la section y
   apparaît telle qu'elle sera après collage, y compris dans une page dont la
   feuille de style définit des noms courants (`.btn`, `.card`) : l'isolation
   y est démontrée.
1. Ouvrez votre fichier `ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8…html`.
2. Repérez votre section « Vue d'ensemble » et remplacez-la par tout le contenu
   de `bloc-vue-ensemble.html`, du `<section>` initial jusqu'à `</section>`.
3. Sur chaque bouton annoté `data-action="TODO"`, branchez votre fonction :

   ```html
   <button class="ists-btn ists-btn--primary" type="button"
           onclick="recupererMaintenant()">
   ```

4. **Remplacez les données de démonstration.** Les chiffres et les noms du
   bloc sont fictifs. Les cinq zones concernées portent l'attribut
   `data-donnee-exemple`, dont la valeur décrit ce qu'elles contiennent :

   | Zone | Contenu à remplacer |
   | --- | --- |
   | `page-head__meta` | horodatage de la dernière vérification |
   | bandeau d'intégrité | nombre de champs détectés, horodatage, n° de rapport |
   | `.stats` | les quatre indicateurs clés |
   | tableau | lignes : étudiant, matricule, champ, date de sauvegarde |
   | `aside` | état de la base et activité récente |

   Une fois rempli, retirez l'attribut : l'audit cesse alors de le signaler.

5. Ajoutez dans votre `<head>` :

   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1">
   ```

   et `lang="fr"` sur votre balise `<html>`.

6. Vérifiez : `node tools/audit-ui.mjs votre-fichier.html`. Objectif : plus
   aucun avertissement `todo-restant` (15 contrôles) ni `donnee-exemple`
   (5 zones). Tant qu'il en reste, l'audit vous indique lesquels et où.

Le bloc est **isolé** : toutes ses classes portent le préfixe `ists-`, et son
style est porté par `.ists-v9`. Même si votre feuille de style définit déjà
`.btn`, `.card` ou `.stat__value`, aucun échange de styles n'est possible —
c'est vérifié automatiquement par `tests/verifier-bloc.py`.

Pour le régénérer après une modification de la maquette :

```bash
python3 tools/generer-bloc.py
```

### Voie B — outil automatique

#### Étape 1 — État des lieux

```bash
node tools/audit-ui.mjs "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
```

L'audit liste, ligne par ligne, les défauts de finition : emojis-icônes,
libellés tronqués, largeurs fixes, focus clavier supprimé, `viewport` ou `lang`
manquants. Code de sortie `1` si des erreurs subsistent.

#### Étape 2 — Simulation

```bash
python3 tools/integrer-refonte.py "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
```

Affiche ce qui **serait** fait : emojis remplacés, blocs injectés, emojis non
reconnus à traiter à la main. Aucun fichier n'est écrit.

#### Étape 3 — Application

```bash
python3 tools/integrer-refonte.py "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html" --appliquer
```

Trois transformations mécaniques :

1. chaque emoji-icône devient une icône SVG (`<svg class="ists-icon">`) ;
2. la bibliothèque de 20 icônes est injectée avant `</body>` ;
3. le design system porté est injecté avant `</head>`.

Une sauvegarde `…html.bak` est créée.

#### Étape 4 — Activer la refonte sur l'écran

Ajoutez la classe `ists-v9` sur le conteneur de l'écran Vue d'ensemble :

```html
<section class="ists-v9">   <!-- était : <div id="vue-ensemble"> -->
  …
</section>
```

Tant que cette classe est absente, **rien ne change** visuellement : le CSS
injecté reste inactif. C'est le point de bascule, et il est réversible.

#### Étape 5 — Remplacer le contenu de la section

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

#### Étape 6 — Vérification

```bash
node tools/audit-ui.mjs "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
bash tests/verifier-outils.sh
```

Objectif : plus aucune erreur d'audit, et 21/21 contrôles réussis.

#### Retour arrière

```bash
mv "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html.bak" \
   "ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8-corrige.html"
```

---

## 3. Ce qui reste à faire à la main

Deux catégories de travail, toutes deux signalées par l'audit :

| Règle | Nombre | Nature |
| --- | --- | --- |
| `todo-restant` | 15 | Boutons à relier à vos fonctions existantes |
| `donnee-exemple` | 5 | Zones contenant des données fictives à remplacer |


L'intégration automatique traite les icônes et la couche visuelle. Trois
défauts structurels doivent être corrigés dans votre fichier d'origine :

| Défaut | Correction |
| --- | --- |
| `<meta name="viewport">` absent | L'ajouter dans `<head>` : sans lui, l'affichage mobile est celui d'un site des années 2000, zoomé et débordant. |
| `<html>` sans attribut `lang` | Ajouter `lang="fr"` (lecteurs d'écran, correcteur orthographique). |
| `button:focus{outline:none}` | Remplacer par un anneau visible via `:focus-visible` — condition d'accessibilité clavier. |
| Largeurs en dur (`width:320px`) et libellés `nowrap` tronqués | Remplacer par `minmax(0, 1fr)` et laisser les libellés revenir à la ligne. |
| « Récupérer TOUT » proposé deux fois : dans le panneau de vérification (tout l'historique) et dans la liste des outils (recherche complète) | Ne garder qu'**un seul point d'entrée** par action : l'opération lourde dans la liste des outils, l'action immédiate dans le panneau. Dans la refonte, le panneau ne propose plus que « Récupérer maintenant », « Voir le détail » et « Reporter ». |

### Actions en double

Deux boutons qui déclenchent la même opération aux deux endroits de l'écran
sèment le doute : l'utilisateur ne sait pas lequel choisir, ni s'ils font la
même chose. L'audit le signale sous la règle `action-dupliquee`, y compris
lorsque les libellés ne se ressemblent pas, grâce au dictionnaire de familles
d'actions (`FAMILLES_ACTIONS` dans `tools/audit-ui.mjs`). Pour ajouter une
équivalence propre à votre application, complétez ce dictionnaire.

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
