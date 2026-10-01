#!/usr/bin/env python3
"""Extrait le design system de la maquette vers des fichiers CSS réutilisables.

Produit deux fichiers à partir de `design/index.html` (source de vérité unique) :

  · design/ists-design-system.css        — version brute, telle qu'utilisée par la maquette ;
  · design/ists-design-system.scope.css  — version « portée », sûre à intégrer dans une
    application existante : chaque sélecteur est préfixé par `.ists-v9` et chaque jeton
    `--nom` devient `--ists-nom`. Aucune règle ne peut donc s'appliquer en dehors du
    conteneur `.ists-v9`, et aucun jeton ne peut entrer en collision avec les vôtres.

Usage :
    python3 tools/extraire-design-system.py
"""

from pathlib import Path
import re
import sys

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "design" / "index.html"
CIBLE_BRUTE = RACINE / "design" / "ists-design-system.css"
CIBLE_PORTEE = RACINE / "design" / "ists-design-system.scope.css"

PORTEE = ".ists-v9"          # conteneur de l'écran refondu
PREFIXE_JETON = "--ists-"    # préfixe des variables CSS


# --------------------------------------------------------------- analyse CSS
def decouper_blocs(css: str):
    """Découpe une feuille CSS en (selecteur, corps, est_at_regle_de_contenu)."""
    i, taille, tampon = 0, len(css), []
    while i < taille:
        caractere = css[i]
        if caractere == "{":
            fin = trouver_accolade(css, i)
            selecteur = "".join(tampon).strip()
            tampon = []
            corps = css[i + 1 : fin]
            if selecteur.startswith("@") and re.match(r"@(media|supports|layer)", selecteur):
                yield selecteur, corps, True          # bloc imbriqué à parcourir
            elif selecteur.startswith("@"):
                yield selecteur, corps, False         # @keyframes, @font-face : laissé tel quel
            else:
                yield selecteur, corps, False
            i = fin + 1
            continue
        tampon.append(caractere)
        i += 1


def trouver_accolade(css: str, debut: int) -> int:
    """Index de l'accolade fermante correspondant à celle en position `debut`."""
    profondeur = 0
    for i in range(debut, len(css)):
        if css[i] == "{":
            profondeur += 1
        elif css[i] == "}":
            profondeur -= 1
            if profondeur == 0:
                return i
    return len(css) - 1


def prefixer_jetons(css: str) -> str:
    """Renomme `--bg` en `--ists-bg`, déclarations comme utilisations."""
    noms = sorted(set(re.findall(r"(--[a-zA-Z0-9-]+)\s*:", css)), key=len, reverse=True)
    for nom in noms:
        if nom.startswith(PREFIXE_JETON):
            continue
        nouveau = PREFIXE_JETON + nom[2:]
        css = re.sub(rf"{re.escape(nom)}(\s*:)", rf"{nouveau}\1", css)
        css = re.sub(rf"var\(\s*{re.escape(nom)}(\s*[,)])", rf"var({nouveau}\1", css)
    return css


def decouper_selecteurs(selecteur: str) -> list[str]:
    """Sépare une liste de sélecteurs en respectant les parenthèses."""
    morceaux, profondeur, courant = [], 0, []
    for caractere in selecteur:
        if caractere == "(":
            profondeur += 1
        elif caractere == ")":
            profondeur -= 1
        if caractere == "," and profondeur == 0:
            morceaux.append("".join(courant).strip())
            courant = []
        else:
            courant.append(caractere)
    morceaux.append("".join(courant).strip())
    return [m for m in morceaux if m]


def porter_selecteur(selecteur: str) -> str | None:
    """Applique la portée à un sélecteur. Renvoie None si la règle doit être écartée."""
    selecteur = selecteur.strip()
    if selecteur in (":root", "body"):
        return PORTEE
    if selecteur == "html":
        return None                      # non portable : la règle vise la racine du document
    if selecteur.startswith("@"):
        return selecteur
    if re.fullmatch(r"\*,\s*\*::before,\s*\*::after", selecteur):
        return f"{PORTEE} *, {PORTEE} *::before, {PORTEE} *::after"
    if selecteur.startswith(PORTEE):
        return selecteur
    return f"{PORTEE} {selecteur}"


def portee(css: str) -> str:
    """Réécrit la feuille pour qu'elle ne s'applique que sous `.ists-v9`."""
    sortie: list[str] = []
    for selecteur, corps, imbrique in decouper_blocs(css):
        if imbrique:                     # @media / @supports : on descend d'un niveau
            sortie.append(f"{selecteur} {{\n{portee(corps).strip()}\n}}")
            continue
        if selecteur.startswith("@"):    # @keyframes, @font-face : conservé tel quel
            sortie.append(f"{selecteur} {{{corps.strip()}}}")
            continue
        selecteurs = [porter_selecteur(s) for s in decouper_selecteurs(selecteur)]
        selecteurs = [s for s in selecteurs if s]
        if not selecteurs:
            continue
        sortie.append(f"{', '.join(selecteurs)} {{{corps.strip()}}}")
    return "\n\n".join(sortie)


# ----------------------------------------------------------------------- main
def main() -> int:
    if not SOURCE.exists():
        print(f"Source introuvable : {SOURCE}", file=sys.stderr)
        return 1

    html = SOURCE.read_text(encoding="utf-8")
    blocs = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S)
    if not blocs:
        print("Aucun bloc <style> dans la maquette.", file=sys.stderr)
        return 1

    brut = "\n".join(b.strip("\n") for b in blocs)

    en_tete = lambda nom, description: (
        "/* ==========================================================================\n"
        f"   ISTS Campus — {nom} (Potter's Bible University)\n"
        f"   {description}\n"
        "   Fichier GÉNÉRÉ depuis design/index.html par tools/extraire-design-system.py\n"
        "   Ne pas modifier à la main : modifier la maquette puis relancer le script.\n"
        "   ========================================================================== */\n\n"
    )

    CIBLE_BRUTE.write_text(
        en_tete("design system", "Version brute, utilisée telle quelle par la maquette.")
        + brut + "\n",
        encoding="utf-8",
    )

    sans_commentaires = re.sub(r"/\*.*?\*/", "", brut, flags=re.S)
    porte = portee(prefixer_jetons(sans_commentaires))
    CIBLE_PORTEE.write_text(
        en_tete(
            "design system porté",
            f"Version sûre à intégrer dans l'application : tout est porté par `{PORTEE}`,\n"
            f"   jetons renommés `{PREFIXE_JETON}…`. Aucun effet hors du conteneur {PORTEE}.",
        )
        + porte + "\n",
        encoding="utf-8",
    )

    for cible in (CIBLE_BRUTE, CIBLE_PORTEE):
        print(f"Écrit : {cible.relative_to(RACINE)} ({cible.stat().st_size} octets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
