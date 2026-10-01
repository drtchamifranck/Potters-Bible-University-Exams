#!/usr/bin/env python3
"""Contrôle le bloc prêt à coller (`docs/bloc-vue-ensemble.html`).

Vérifie que le bloc est réellement autonome et sans conflit :

  1. il contient sa feuille de style, sa bibliothèque d'icônes et sa section ;
  2. aucune classe du balisage n'est dépourvue de règle de style (une faute de
     frappe dans un nom de classe passerait sinon inaperçue) ;
  3. aucune classe n'est laissée sans le préfixe `ists-` ;
  4. aucun emoji ne subsiste ;
  5. une fois collé dans un document complet, l'audit ne relève plus aucune erreur.

Sortie : 0 si tout est conforme, 1 sinon.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BLOC = RACINE / "docs" / "bloc-vue-ensemble.html"
APERCU = RACINE / "docs" / "apercu-bloc.html"
PREFIXE = "ists-"

# Classes volontairement sans règle CSS (portées par un parent, ou utilitaires).
CLASSES_SANS_RÈGLE = {f"{PREFIXE}v9", f"{PREFIXE}sprite"}

echecs: list[str] = []
controles = 0


def controler(condition: bool, description: str, detail: str = "") -> None:
    global controles
    controles += 1
    if condition:
        print(f"  OK     {description}")
    else:
        echecs.append(description)
        print(f"  ÉCHEC  {description}" + (f"\n         {detail}" if detail else ""))


def main() -> int:
    print("\n─── Bloc prêt à coller ───\n")

    if not BLOC.exists():
        print("  ÉCHEC  bloc introuvable — lancez : python3 tools/generer-bloc.py")
        return 1
    source = BLOC.read_text(encoding="utf-8")

    # 1. Autonomie ---------------------------------------------------------
    for marqueur, description in [
        ('<style id="ists-icons"', "feuille d'icônes présente"),
        ('<style id="ists-design-system"', "design system présent"),
        ('id="ists-icon-sprite"', "bibliothèque d'icônes présente"),
        ('<section class="ists-v9"', "section portée par .ists-v9"),
        ('data-action="TODO"', "contrôles à relier annotés"),
    ]:
        controler(marqueur in source, description, f"marqueur absent : {marqueur}")

    # 2/3. Classes du balisage ---------------------------------------------
    balisage = source[source.index('<section class="ists-v9"'):]   # balisage seul, sans l'en-tête
    classes = set()
    for attribut in re.findall(r'class="([^"]+)"', balisage):
        classes.update(attribut.split())

    sans_prefixe = sorted(c for c in classes if not c.startswith(PREFIXE))
    controler(not sans_prefixe, "toutes les classes sont préfixées « ists- »",
              f"non préfixées : {', '.join(sans_prefixe)}")

    feuille = source[source.index('<style id="ists-design-system"'):source.index('id="ists-icon-sprite"')]
    selecteurs = " ".join(re.findall(r"([^{}]+)\{", feuille))
    orphelines = sorted(
        c for c in classes
        if c not in CLASSES_SANS_RÈGLE and f".{c}" not in selecteurs
    )
    controler(not orphelines, "chaque classe du balisage a une règle de style",
              f"sans règle : {', '.join(orphelines)}")

    # 4. Aucun emoji -------------------------------------------------------
    emojis = re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", source)
    controler(not emojis, "aucun emoji dans le bloc", f"trouvés : {''.join(sorted(set(emojis)))}")

    # 5. Collage dans un document complet ----------------------------------
    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Essai du bloc collé</title>
<style>
  /* Feuille de l'application hôte, volontairement générique et conflictuelle. */
  body{{margin:0;background:#fbf7ee;font-family:system-ui,sans-serif}}
  .btn{{background:#e2bd63;border-radius:0;padding:20px}}
  .card{{box-shadow:none;border:3px solid red}}
  .stat__value{{font-size:60px}}
  table{{border-collapse:separate}}
</style>
</head>
<body>
{source}
</body>
</html>
"""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "colle.html"
        chemin.write_text(page, encoding="utf-8")
        resultat = subprocess.run(
            ["node", str(RACINE / "tools" / "audit-ui.mjs"), "--json", str(chemin)],
            capture_output=True, text=True, cwd=RACINE,
        )
        import json

        rapport = json.loads(resultat.stdout)[0]
        erreurs = [r for r in rapport["resultats"] if r["gravite"] == "erreur"]
        controler(not erreurs, "aucune erreur une fois le bloc collé dans une page",
                  "\n         ".join(f"{r['titre']} (ligne {r['ligne']})" for r in erreurs[:5]))

        restants = [r for r in rapport["resultats"] if r["regle"] == "todo-restant"]
        attendus = balisage.count('data-action="TODO"')
        controler(len(restants) == attendus,
                  f"les {attendus} contrôles à relier sont signalés",
                  f"signalés : {len(restants)}")

        demo = [r for r in rapport["resultats"] if r["regle"] == "donnee-exemple"]
        controler(len(demo) == 5,
                  "les 5 zones de démonstration sont signalées à l'intégrateur",
                  f"signalées : {len(demo)}")

    # 6. Structure : le balisage doit être équilibré ------------------------
    from html.parser import HTMLParser

    vides = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr", "path", "circle", "rect",
             "ellipse", "use", "line", "polyline", "polygon", "stop", "symbol"}

    class Analyseur(HTMLParser):
        def __init__(self):
            super().__init__()
            self.pile: list[str] = []
            self.erreurs: list[str] = []

        def handle_starttag(self, t, a):
            if t not in vides:
                self.pile.append(t)

        def handle_endtag(self, t):
            if t in vides:
                return
            if not self.pile or self.pile[-1] != t:
                self.erreurs.append(f"</{t}> inattendu")
            else:
                self.pile.pop()

    analyseur = Analyseur()
    analyseur.feed(source)
    controler(not analyseur.erreurs and not analyseur.pile,
              "balisage équilibré (aucune balise orpheline)",
              "; ".join(analyseur.erreurs[:5]) or f"non fermées : {analyseur.pile[:5]}")

    # 6 bis. Données de démonstration ---------------------------------------
    zones = re.findall(r'data-donnee-exemple="([^"]*)"', source)
    controler(len(zones) == 5, "les 5 zones de données de démonstration sont balisées",
              f"balisées : {len(zones)} — {zones}")
    controler(all(z.strip() for z in zones),
              "chaque zone de démonstration décrit son contenu",
              "description vide dans : " + str([z for z in zones if not z.strip()]))

    # 7. Aperçu : le bloc doit être visualisable tel quel --------------------
    controler(APERCU.exists(), "page d'aperçu générée")
    if APERCU.exists():
        apercu = APERCU.read_text(encoding="utf-8")
        controler(
            all(m in apercu for m in ('ists-design-system', 'ists-icon-sprite', 'class="ists-v9"')),
            "l'aperçu embarque la feuille, les icônes et la section",
        )
        # L'aperçu simule une feuille hôte conflictuelle : le rendu doit y résister
        resultat = subprocess.run(
            ["node", str(RACINE / "tools" / "audit-ui.mjs"), "--json", str(APERCU)],
            capture_output=True, text=True, cwd=RACINE,
        )
        import json

        rapport = json.loads(resultat.stdout)[0]
        erreurs = [r for r in rapport["resultats"] if r["gravite"] == "erreur"]
        controler(not erreurs, "aucune erreur dans l'aperçu",
                  "\n         ".join(f"{r['titre']} (ligne {r['ligne']})" for r in erreurs[:5]))

    print(f"\n  Total : {controles - len(echecs)}/{controles} contrôles réussis\n")
    return 1 if echecs else 0


if __name__ == "__main__":
    raise SystemExit(main())
