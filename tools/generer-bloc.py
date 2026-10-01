#!/usr/bin/env python3
"""Génère `docs/bloc-vue-ensemble.html` : la section « Vue d'ensemble » prête à coller.

Le bloc produit est **autonome** : il contient sa feuille de style, sa
bibliothèque d'icônes et sa structure. L'utilisateur le colle à la place de sa
propre section, sans rien installer ni lancer de commande.

Deux protections évitent tout conflit avec l'application hôte :

  · toutes les classes sont préfixées `ists-` (aucune collision avec les
    classes existantes de l'application) ;
  · toutes les règles sont portées par `.ists-v9`, donc sans effet ailleurs.

Le fichier généré porte les mêmes identifiants que ceux injectés par
`tools/integrer-refonte.py` (`ists-design-system`, `ists-icons`,
`ists-icon-sprite`) : les deux procédés ne peuvent donc pas se dupliquer.

Usage :
    python3 tools/generer-bloc.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

RACINE = Path(__file__).resolve().parent.parent
MAQUETTE = RACINE / "design" / "index.html"
CSS_PORTE = RACINE / "design" / "ists-design-system.scope.css"
CIBLE = RACINE / "docs" / "bloc-vue-ensemble.html"
APERCU = RACINE / "docs" / "apercu-bloc.html"

PREFIXE = "ists-"
PORTEE = f".{PREFIXE}v9"

# Classes de la maquette à ne pas renommer (portées par le conteneur lui-même).
CLASSES_RESERVEES = {f"{PREFIXE}v9"}


def charger_outils():
    """Charge tools/integrer-refonte.py (nom de fichier non importable tel quel)."""
    chemin = RACINE / "tools" / "integrer-refonte.py"
    spec = importlib.util.spec_from_file_location("integrer_refonte", chemin)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ extraction
def extraire_section(maquette: str) -> str:
    """Récupère le contenu de <main> en retirant le bandeau de maquette."""
    contenu = re.search(r"<main class=\"page\" id=\"main\">(.*?)</main>", maquette, re.S)
    if not contenu:
        raise SystemExit("Section <main> introuvable dans la maquette.")
    texte = contenu.group(1)
    # Bandeau « maquette de refonte » : n'a pas sa place dans l'application
    texte = re.sub(r'\s*<div class="band" id="demo-band">.*?</div>', "\n", texte, flags=re.S)
    return texte.strip()


def classes_utilisees(html: str) -> set[str]:
    """Liste les classes présentes dans le balisage."""
    noms: set[str] = set()
    for attribut in re.findall(r'class="([^"]+)"', html):
        noms.update(attribut.split())
    return {n for n in noms if not n.startswith(PREFIXE)} - CLASSES_RESERVEES


def prefixer_markup(html: str) -> str:
    """Préfixe toutes les classes et tous les renvois d'icônes."""
    def remplacer_classe(m: re.Match) -> str:
        noms = " ".join(
            f"{PREFIXE}{n}" if not n.startswith(PREFIXE) else n
            for n in m.group(1).split()
        )
        return f'class="{noms}"'

    html = re.sub(r'class="([^"]+)"', remplacer_classe, html)
    html = re.sub(r'href="#i-', f'href="#{PREFIXE}i-', html)
    return html


def prefixer_css(css: str, classes: set[str]) -> str:
    """Préfixe dans la feuille les classes utilisées par le balisage."""
    # Le regard arrière est volontairement absent : un sélecteur composé
    # (« td.is-primary », « a.section__link ») doit lui aussi être préfixé.
    # Le regard avant, lui, évite que « card » ne ronge « card__head ».
    for nom in sorted(classes, key=len, reverse=True):
        css = re.sub(rf"\.{re.escape(nom)}(?![\w-])", f".{PREFIXE}{nom}", css)
    return css


# ------------------------------------------------------------------ assemblage
ENTETE = """<!-- ==========================================================================
     ISTS Campus — section « Vue d'ensemble » prête à coller
     Générée par tools/generer-bloc.py — ne pas modifier à la main.

     MODE D'EMPLOI
       1. Ouvrez votre fichier ISTS-CAMPUS-ACCES-COURS-RAPIDE-V8…html.
       2. Repérez votre section « Vue d'ensemble » et REMPLACEZ-LA par tout ce
          qui suit, du <section> initial jusqu'à </section> final inclus.
       3. Enregistrez, rechargez la page : le nouveau rendu s'applique.

     CE QUI EST INCLUS
       · le programme de style (porté par .ists-v9, donc sans effet sur le
         reste de votre application) ;
       · les vingt icônes SVG (plus aucun emoji) ;
       · la structure de l'écran : bandeau d'intégrité, indicateurs, actions,
         tableau des champs à compléter.

     À SAVOIR
       · L'identifiant id="vue-ensemble" est celui de la section. Si votre
         JavaScript s'appuie sur un identifiant différent, remplacez-le ici.
       · Toutes les classes sont préfixées « ists- » et le style est porté par
         .ists-v9 : aucun risque de conflit avec votre propre feuille.

     À FAIRE APRÈS LE COLLAGE

       1) RELIER LES BOUTONS
          Sur chacun des 15 contrôles annotés data-action="TODO", mettez votre
          fonction existante. Exemple :
              <button class="ists-btn ists-btn--primary" type="button"
                      onclick="recupererMaintenant()">
          Vos fonctions ne sont pas modifiées : seul le bouton qui les appelle change.

       2) REMPLACER LES DONNÉES DE DÉMONSTRATION
          Les chiffres et les noms présents ici sont FICTIFS. Les cinq zones
          concernées portent l'attribut data-donnee-exemple, qui décrit ce
          qu'elles contiennent :
              · l'horodatage de la dernière vérification   (page-head__meta)
              · le bandeau : nombre de champs, horodatage, n° de rapport
              · les quatre indicateurs clés
              · les lignes du tableau (étudiants, matricules, champs, dates)
              · l'état de la base et l'activité récente
          Remplissez-les depuis vos données réelles, puis retirez l'attribut.

          L'audit les signale tant qu'ils sont présents :
              · 15 avertissements « Annotation TODO »     (contrôles à relier)
              ·  5 avertissements « Donnée de démonstration » (à remplacer)
       · Ajoutez <meta name="viewport" content="width=device-width, initial-scale=1">
         dans votre <head> : sans elle, l'écran reste tronqué sur téléphone.
       · Ajoutez lang="fr" sur votre balise <html>.

     VÉRIFIER
       node tools/audit-ui.mjs votre-fichier.html
     ========================================================================== -->

"""


APERCU_GABARIT = """<!DOCTYPE html>
<!-- Aperçu du bloc collé — généré par tools/generer-bloc.py.
     Montre le rendu exact de la section telle qu'elle apparaîtra une fois
     collée dans l'application. La feuille ci-dessous joue le rôle de la
     feuille de style de l'application hôte : elle définit volontairement des
     noms courants (.btn, .card, .stat__value) pour démontrer l'isolation. -->
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Aperçu du bloc collé · ISTS Campus</title>
<style>
  /* Feuille de style « hôte », conflictuelle à dessein. */
  body {{ margin: 0; background: #fbf7ee; font-family: Georgia, serif; }}
  .btn {{ background: #e2bd63; border-radius: 0; padding: 20px; border: 0; }}
  .card {{ box-shadow: none; border: 3px solid red; }}
  .stat__value {{ font-size: 72px; color: magenta; }}
  table {{ border-collapse: separate; border-spacing: 8px; }}
  .bandeau {{ padding: 10px 16px; background: #17202e; color: #fff; font-family: system-ui, sans-serif; font-size: 13px; }}
  .bandeau strong {{ color: #e2bd63; }}
</style>
</head>
<body>
<p class="bandeau">
  <strong>Aperçu du bloc collé.</strong>
  La feuille ci-dessus redéfinit volontairement <code>.btn</code>, <code>.card</code>
  et <code>.stat__value</code> : le rendu ci-dessous n'en subit aucun effet.
</p>

{bloc}
</body>
</html>
"""


def main() -> int:
    if not MAQUETTE.exists():
        print(f"Maquette introuvable : {MAQUETTE}", file=sys.stderr)
        return 1
    outils = charger_outils()

    maquette = MAQUETTE.read_text(encoding="utf-8")
    contenu = extraire_section(maquette)
    classes = classes_utilisees(contenu)
    contenu = prefixer_markup(contenu)

    # Feuille portée, classes préfixées une seconde fois
    css = CSS_PORTE.read_text(encoding="utf-8")
    css = prefixer_css(css, classes)

    # Icônes : règles globales + bibliothèque
    regles_icones = outils.construire_feuille_icones()
    sprite = outils.construire_sprite()

    # Chaque contrôle interactif est annoté : l'appelant sait exactement où
    # brancher sa fonction existante, et l'audit signale ce qui reste à faire.
    contenu = re.sub(
        r'(<(?:button|a) class="ists-(?:btn|action|rowaction|section__link)\b[^"]*"[^>]*?)(\s*/?>)',
        r'\1 data-action="TODO"\2',
        contenu,
    )

    bloc = (
        f'{ENTETE}'
        f'<style id="{outils.ID_ICONES}">\n{regles_icones}\n</style>\n'
        f'<style id="{outils.ID_STYLE}">\n{css.strip()}\n</style>\n'
        f'{sprite}\n\n'
        f'<section class="{PREFIXE}v9" id="vue-ensemble">\n'
        f'{contenu}\n'
        f"</section>\n"
    )

    CIBLE.write_text(bloc, encoding="utf-8")
    APERCU.write_text(APERCU_GABARIT.format(bloc=bloc), encoding="utf-8")

    # --- rapport -----------------------------------------------------------
    print(f"\nGénéré : {CIBLE.relative_to(RACINE)} ({CIBLE.stat().st_size} octets)")
    print(f"  · classes préfixées  : {len(classes)}")
    print(f"  · icônes SVG         : {len(re.findall(r'<symbol', sprite))}")
    print(f"  · boutons à relier   : {len(re.findall(r'data-action=', bloc))}")
    print(f"  · marge de style     : {len(css)} octets, toutes règles sous {PORTEE}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
