#!/usr/bin/env python3
"""Intègre la refonte ISTS Campus dans une application existante, sans risque.

Le script applique trois transformations mécaniques et réversibles :

  1. remplacement des emojis-icônes par des icônes SVG préfixées `ists-` ;
  2. injection de la bibliothèque d'icônes avant `</body>` ;
  3. injection du design system (portée limitée à `.ists-v9`) avant `</head>`.

Rien d'autre n'est modifié : ni le JavaScript, ni les identifiants, ni la
structure de vos écrans. Par défaut le script ne fait qu'un rapport
(simulation) ; l'écriture réelle exige `--appliquer` et crée une sauvegarde
`.bak`.

Usage :
    python3 tools/integrer-refonte.py app.html              # simulation
    python3 tools/integrer-refonte.py app.html --appliquer  # écriture + .bak
    python3 tools/integrer-refonte.py app.html --sans-css   # icônes seulement
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
MAQUETTE = RACINE / "design" / "index.html"
CSS_SCOPE = RACINE / "design" / "ists-design-system.scope.css"

PREFIXE = "ists-"
MARQUEUR_DEBUT = "<!-- ISTS Campus : bloc généré par tools/integrer-refonte.py -->"
MARQUEUR_FIN = "<!-- /ISTS Campus -->"
ID_STYLE = "ists-design-system"
ID_SPRITE = "ists-icon-sprite"
ID_ICONES = "ists-icons"

# --------------------------------------------------------------- correspondances
# Emoji → identifiant d'icône (celui du sprite de la maquette).
CORRESPONDANCES: dict[str, str] = {
    "🔍": "i-search", "🔎": "i-search",
    "📥": "i-download", "⤵": "i-download", "⬇": "i-download",
    "📤": "i-upload", "⤴": "i-upload", "⬆": "i-upload",
    "🩺": "i-filecheck", "👨‍⚕": "i-filecheck", "👩‍⚕": "i-filecheck", "🧑‍⚕": "i-filecheck",
    "🔔": "i-bell", "🛎": "i-bell",
    "🏛": "i-info", "🏦": "i-info", "🏫": "i-info",
    "🎓": "i-cap",
    "✅": "i-check", "☑": "i-check", "✔": "i-check",
    "⚠": "i-alert", "❗": "i-alert",
    "💾": "i-database", "🗄": "i-database", "🗃": "i-database",
    "📊": "i-grid", "📈": "i-grid", "📉": "i-grid",
    "🗂": "i-folder", "📁": "i-folder", "📂": "i-folder",
    "👤": "i-users", "👥": "i-users", "🧑‍🎓": "i-users",
    "🕐": "i-clock", "⏰": "i-clock", "⌛": "i-clock", "⏳": "i-clock",
    "🔁": "i-refresh", "🔄": "i-refresh", "♻": "i-refresh",
    "🛡": "i-shield",
    "❌": "i-x", "✖": "i-x",
    "ℹ": "i-info",
    "➡": "i-arrow",
    "🔽": "i-chevron", "🔻": "i-chevron", "⬇️": "i-chevron",
}

# Séquences emoji (hors chiffres et lettres) recherchées dans le document.
RE_EMOJI = re.compile(
    "(?:[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF]|\uFE0F|\u200D)+"
)
RE_HEAD = re.compile(r"<head\b.*?</head>", re.S | re.I)
RE_BALISE_TITRE = re.compile(r"<title\b.*?</title>", re.S | re.I)


def normaliser(sequence: str) -> list[str]:
    """Propose les clés de correspondance d'une séquence emoji, de la plus précise à la plus simple."""
    variantes = [sequence, sequence.replace("\ufe0f", "").replace("\u200d", "")]
    # Découpe une éventuelle séquence ZWJ en ses composants (👨‍⚕️ → 👨, ⚕️)
    for base in re.split("[\u200d\ufe0f]", sequence):
        if base:
            variantes.append(base)
    vues, uniques = set(), []
    for v in variantes:
        if v and v not in vues:
            vues.add(v)
            uniques.append(v)
    return uniques


def icone_html(identifiant: str, variante: str = "") -> str:
    classes = f"{PREFIXE}icon" + (f" {PREFIXE}icon--{variante}" if variante else "")
    return (
        f'<svg class="{classes}" aria-hidden="true" focusable="false">'
        f'<use href="#{PREFIXE}{identifiant}"></use></svg>'
    )


def extraire_bloc(texte: str, motif: str) -> str:
    m = re.search(motif, texte, re.S | re.I)
    return m.group(0) if m else ""


# --------------------------------------------------------------------- étapes
def associer(sequence: str) -> str | None:
    """Renvoie l'identifiant d'icône correspondant à une séquence emoji, sinon None."""
    for variante in normaliser(sequence):
        if variante in CORRESPONDANCES:
            return CORRESPONDANCES[variante]
    return None


def remplacer_emojis(source: str) -> tuple[str, list[tuple[str, str]], list[str]]:
    """Remplace les emojis hors `<head>` et `<title>`.

    Renvoie (texte, [(séquence, icône)], restants).
    """
    remplaces: list[tuple[str, str]] = []
    restants: list[str] = []

    # On met de côté les zones où un remplacement serait nuisible.
    protegees: list[str] = []

    def mettre_de_cote(m: re.Match) -> str:
        protegees.append(m.group(0))
        return f"\x00ZONE{len(protegees) - 1}\x00"

    travail = RE_HEAD.sub(mettre_de_cote, source)
    travail = RE_BALISE_TITRE.sub(mettre_de_cote, travail)

    def remplacer(m: re.Match) -> str:
        sequence = m.group(0)
        icone = associer(sequence)
        if icone:
            remplaces.append((sequence, icone))
            return icone_html(icone)
        restants.append(sequence)
        return sequence

    travail = RE_EMOJI.sub(remplacer, travail)
    travail = re.sub(
        r"\x00ZONE(\d+)\x00", lambda m: protegees[int(m.group(1))], travail
    )
    return travail, remplaces, restants


def nombre_icones() -> int:
    """Nombre de symboles réellement disponibles dans la bibliothèque."""
    return len(re.findall(r'<symbol\b', construire_sprite()))


def construire_sprite() -> str:
    """Reprend le sprite de la maquette en préfixant les identifiants."""
    maquette = MAQUETTE.read_text(encoding="utf-8")
    sprite = extraire_bloc(maquette, r'<svg class="sprite".*?</svg>')
    if not sprite:
        raise SystemExit("Sprite introuvable dans la maquette (design/index.html).")
    sprite = re.sub(r'\bid="i-', f'id="{PREFIXE}i-', sprite)
    sprite = re.sub(r'href="#i-', f'href="#{PREFIXE}i-', sprite)
    sprite = sprite.replace('class="sprite"', f'class="{PREFIXE}sprite" id="{ID_SPRITE}"')
    return sprite


def construire_feuille_icones() -> str:
    """Rejoue les règles `.icon` de la maquette sous le préfixe `ists-icon`.

    Ces règles restent **globales** : une icône injectée doit être dimensionnée
    même lorsqu'elle se trouve en dehors de la portée `.ists-v9` (c'est le cas
    des emojis remplacés dans le reste de l'application).
    """
    maquette = MAQUETTE.read_text(encoding="utf-8")
    blocs = re.findall(r"<style[^>]*>(.*?)</style>", maquette, flags=re.S)
    css = "\n".join(blocs)
    regles = []
    for selecteur, corps in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sel = selecteur.strip().splitlines()[-1].strip() if selecteur.strip() else ""
        if re.fullmatch(r"\.icon(?:--sm|--lg)?|\.sprite", sel):
            regles.append(f".{PREFIXE}{sel[1:]} {{{corps.strip()}}}")
    if not any("sprite" in r for r in regles):
        regles.append(f".{PREFIXE}sprite {{ display: none; }}")
    return "\n".join(regles)


def injecter_style(source: str, css: str, identifiant: str) -> tuple[str, bool]:
    """Insère <style id="…"> avant </head>. Idempotent : ne réinjecte jamais."""
    if f'id="{identifiant}"' in source:
        return source, False
    index = source.lower().rfind("</head>")
    if index == -1:  # document sans <head> explicite
        index = source.lower().find("<body")
    if index == -1:
        return source, False
    bloc = (
        f"{MARQUEUR_DEBUT}\n"
        f'<style id="{identifiant}">\n{css.strip()}\n</style>\n'
        f"{MARQUEUR_FIN}\n"
    )
    return source[:index] + bloc + source[index:], True


def injecter_sprite(source: str) -> tuple[str, bool]:
    """Insère la bibliothèque d'icônes avant </body>. Idempotent."""
    if ID_SPRITE in source:
        return source, False
    index = source.lower().rfind("</body>")
    if index == -1:
        index = len(source)
    bloc = f"{MARQUEUR_DEBUT}\n{construire_sprite()}\n{MARQUEUR_FIN}\n"
    return source[:index] + bloc + source[index:], True


# ---------------------------------------------------------------------- rapport
def main() -> int:
    analyseur = argparse.ArgumentParser(description="Intègre la refonte ISTS Campus dans un fichier HTML.")
    analyseur.add_argument("fichier", type=Path, help="fichier HTML de l'application")
    analyseur.add_argument("--appliquer", action="store_true", help="écrire les modifications (sinon simulation)")
    analyseur.add_argument("--sans-css", action="store_true", help="ne pas injecter le design system")
    options = analyseur.parse_args()

    cible: Path = options.fichier
    if not cible.is_file():
        print(f"Fichier introuvable : {cible}", file=sys.stderr)
        return 2

    original = cible.read_text(encoding="utf-8")
    source, remplaces, restants = remplacer_emojis(original)

    # --- injection ---------------------------------------------------------
    modifie = source
    etapes: list[str] = []

    if not options.sans_css:
        if not CSS_SCOPE.exists():
            print(
                f"Design system porté introuvable ({CSS_SCOPE.name}) — "
                "lancez d'abord : python3 tools/extraire-design-system.py",
                file=sys.stderr,
            )
            return 2
        # Les icônes injectées doivent être dimensionnées même hors portée .ists-v9
        modifie, fait = injecter_style(modifie, construire_feuille_icones(), ID_ICONES)
        if fait:
            etapes.append(f'feuille d\'icônes (id="{ID_ICONES}")')
        modifie, fait = injecter_style(
            modifie, CSS_SCOPE.read_text(encoding="utf-8"), ID_STYLE
        )
        if fait:
            etapes.append(f'design system porté .{PREFIXE}v9 (id="{ID_STYLE}")')

    if ID_SPRITE not in modifie:
        modifie, fait = injecter_sprite(modifie)
        if fait:
            etapes.append(f'bibliothèque de {nombre_icones()} icônes SVG (id="{ID_SPRITE}")')

    # --- rapport -----------------------------------------------------------
    print(f"\n─── Intégration de la refonte : {cible.name} ───\n")
    print(f"  Emojis-icônes remplacés : {len(remplaces)}  ({len(set(e for e, _ in remplaces))} distincts)")
    if remplaces:
        from collections import Counter

        for (emoji, icone), nombre in Counter(remplaces).most_common():
            print(f"     · {emoji}  ×{nombre}  →  {PREFIXE}{icone}")
    if restants:
        print(f"\n  Emojis non reconnus ({len(restants)}, à traiter manuellement) :")
        for emoji in sorted(set(restants)):
            print(f"     · {emoji}  (U+{ord(emoji[0]):04X})")

    if etapes:
        print("\n  Injecté :")
        for etape in etapes:
            print(f"     · {etape}")

    print("\n  Prochaines étapes :")
    print("     1. ajouter la classe « ists-v9 » sur le conteneur de l'écran Vue d'ensemble ;")
    print("     2. remplacer le contenu de la section par design/index.html (mêmes id/onclick) ;")
    print("     3. vérifier : node tools/audit-ui.mjs " + cible.name)

    if modifie == original:
        print("\n  Aucune modification nécessaire.\n")
        return 0

    if not options.appliquer:
        print("\n  SIMULATION : aucun fichier écrit. Ajoutez --appliquer pour modifier.\n")
        return 0

    sauvegarde = cible.with_suffix(cible.suffix + ".bak")
    shutil.copy2(cible, sauvegarde)
    cible.write_text(modifie, encoding="utf-8")
    print(f"\n  écrit : {cible.name}  (sauvegarde : {sauvegarde.name})\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
