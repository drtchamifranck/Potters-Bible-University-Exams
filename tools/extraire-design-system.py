#!/usr/bin/env python3
"""Extrait le design system de la maquette vers un fichier CSS réutilisable.

`design/index.html` reste autonome (aucune dépendance, s'ouvre par double-clic).
Ce script en extrait le bloc <style> pour produire `design/ists-design-system.css`,
la couche à intégrer dans l'application ISTS Campus V8.

Usage :
    python3 tools/extraire-design-system.py
"""

from pathlib import Path
import re
import sys

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "design" / "index.html"
CIBLE = RACINE / "design" / "ists-design-system.css"

def main() -> int:
    if not SOURCE.exists():
        print(f"Source introuvable : {SOURCE}", file=sys.stderr)
        return 1

    html = SOURCE.read_text(encoding="utf-8")
    bloc = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S)
    if not bloc:
        print("Aucun bloc <style> dans la maquette.", file=sys.stderr)
        return 1

    entete = (
        "/* ==========================================================================\n"
        "   ISTS Campus — Design system (Potter's Bible University)\n"
        "   Fichier GÉNÉRÉ depuis design/index.html par tools/extraire-design-system.py\n"
        "   Ne pas modifier à la main : modifier la maquette puis relancer le script.\n"
        "   ========================================================================== */\n\n"
    )
    CIBLE.write_text(entete + "\n".join(b.strip("\n") for b in bloc) + "\n", encoding="utf-8")
    print(f"Écrit : {CIBLE.relative_to(RACINE)} ({CIBLE.stat().st_size} octets)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
