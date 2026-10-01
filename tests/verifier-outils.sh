#!/usr/bin/env bash
# Vérifie la chaîne d'outils ISTS Campus (audit + intégration) sur un banc d'essai.
# Chaque contrôle affiche OK ou ÉCHEC ; le script sort en erreur si un contrôle échoue.
#
# Usage :  bash tests/verifier-outils.sh
set -uo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

FIXTURE="tests/fixtures/avant-v8.html"
MAQUETTE="design/index.html"
TRAVAIL="$(mktemp -d)"
trap 'rm -rf "$TRAVAIL"' EXIT

if [ -t 1 ]; then ROUGE=$'\033[31m'; VERT=$'\033[32m'; RAZ=$'\033[0m'
else ROUGE=""; VERT=""; RAZ=""; fi

controles=0
echecs=0

ok()    { controles=$((controles + 1)); printf '  %s  %s\n' "${VERT}OK   ${RAZ}" "$1"; }
echec() { controles=$((controles + 1)); echecs=$((echecs + 1)); printf '  %s  %s\n' "${ROUGE}ÉCHEC${RAZ}" "$1"; }

verifier() {   # verifier "description" <valeur attendue> <valeur obtenue>
  if [ "$2" = "$3" ]; then ok "$1"; else echec "$1  (attendu : $2, obtenu : $3)"; fi
}

verifier_vrai() {  # verifier_vrai "description" <commande…>
  local description="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$description"; else echec "$description"; fi
}

empreinte() { sha256sum "$1" | cut -d' ' -f1; }
nombre_regle() {  # nombre_regle <rapport.json> <règle>
  node -e '
    const fs = require("node:fs");
    const [fichier, regle] = process.argv.slice(1);
    const rapport = JSON.parse(fs.readFileSync(fichier, "utf8"))[0].resultats;
    process.stdout.write(String(rapport.filter((r) => r.regle === regle).length));
  ' "$1" "$2"
}

echo
echo "═══ Vérification de la chaîne d'outils ISTS Campus ═══"

echo
echo "1. Maquette de référence"
node tools/audit-ui.mjs "$MAQUETTE" --json > "$TRAVAIL/maquette.json"
verifier "aucune erreur dans la maquette" "0" "$(nombre_regle "$TRAVAIL/maquette.json" emoji)"

verifier "aucune action en double dans la maquette refondue" "0" "$(nombre_regle "$TRAVAIL/maquette.json" action-dupliquee)"

echo
echo "2. Détection : écran V8 avant refonte (banc d'essai)"
node tools/audit-ui.mjs "$FIXTURE" --json > "$TRAVAIL/avant.json"
verifier "15 emojis-icônes détectés" "15" "$(nombre_regle "$TRAVAIL/avant.json" emoji)"
verifier_vrai "largeurs fixes détectées" test "$(nombre_regle "$TRAVAIL/avant.json" largeur-fixe)" -ge 1
verifier_vrai "contour de focus supprimé détecté" test "$(nombre_regle "$TRAVAIL/avant.json" outline-none)" -ge 1
verifier "action dupliquée détectée (« Récupérer TOUT » en double)" "1" "$(nombre_regle "$TRAVAIL/avant.json" action-dupliquee)"
if node tools/audit-ui.mjs "$FIXTURE" --json >/dev/null 2>&1; then
  echec "l'audit signale un écran non conforme (code de sortie 1)"
else
  ok "l'audit signale un écran non conforme (code de sortie 1)"
fi

echo
echo "3. Intégration sur une copie du banc d'essai"
cp "$FIXTURE" "$TRAVAIL/app.html"
AVANT="$(empreinte "$TRAVAIL/app.html")"

python3 tools/integrer-refonte.py "$TRAVAIL/app.html" >/dev/null
verifier "la simulation n'écrit rien dans le fichier" "$AVANT" "$(empreinte "$TRAVAIL/app.html")"

python3 tools/integrer-refonte.py "$TRAVAIL/app.html" --appliquer >/dev/null
verifier_vrai "une sauvegarde .bak est créée" test -f "$TRAVAIL/app.html.bak"
verifier "la sauvegarde contient bien le fichier d'origine" "$AVANT" "$(empreinte "$TRAVAIL/app.html.bak")"

node tools/audit-ui.mjs "$TRAVAIL/app.html" --json > "$TRAVAIL/apres.json"
verifier "plus aucun emoji après intégration" "0" "$(nombre_regle "$TRAVAIL/apres.json" emoji)"
verifier_vrai "design system injecté" grep -q 'ists-design-system' "$TRAVAIL/app.html"
verifier_vrai "bibliothèque d'icônes injectée" grep -q 'ists-icon-sprite' "$TRAVAIL/app.html"

echo
echo "4. Non-régression : le code applicatif reste intact"
verifier_vrai "fonctions JavaScript préservées" grep -q 'function recupererTout' "$TRAVAIL/app.html"
verifier_vrai "seconde fonction préservée" grep -q 'function telechargerSauvegarde' "$TRAVAIL/app.html"
verifier_vrai "attributs onclick préservés" grep -q 'onclick="recupererMaintenant()"' "$TRAVAIL/app.html"
verifier_vrai "identifiants des boutons préservés" grep -q 'id="btn-tout"' "$TRAVAIL/app.html"
verifier "nombre de balises <script> inchangé" \
         "$(grep -c '<script' "$FIXTURE")" "$(grep -c '<script' "$TRAVAIL/app.html")"

echo
echo "5. Robustesse"
APRES_INTEGRATION="$(empreinte "$TRAVAIL/app.html")"
python3 tools/integrer-refonte.py "$TRAVAIL/app.html" --appliquer >/dev/null
verifier "un second passage ne modifie rien (idempotence)" \
         "$APRES_INTEGRATION" "$(empreinte "$TRAVAIL/app.html")"

verifier_vrai "le fichier modifié reste un HTML valide" python3 - "$TRAVAIL/app.html" <<'PY'
import sys
from html.parser import HTMLParser

VIDE = {"area","base","br","col","embed","hr","img","input","link","meta","param",
        "source","track","wbr","path","circle","rect","ellipse","use","line",
        "polyline","polygon","stop","symbol"}

class Analyseur(HTMLParser):
    def __init__(self):
        super().__init__(); self.pile = []; self.erreurs = 0
    def handle_starttag(self, t, a):
        if t not in VIDE: self.pile.append(t)
    def handle_endtag(self, t):
        if t in VIDE: return
        if not self.pile or self.pile[-1] != t: self.erreurs += 1
        else: self.pile.pop()

a = Analyseur(); a.feed(open(sys.argv[1], encoding="utf-8").read())
sys.exit(0 if not a.erreurs and not a.pile else 1)
PY

echo
echo "6. Design system porté : cloisonnement"
verifier_vrai "aucune règle ne vise :root, body ou html" \
              bash -c "! grep -qE '^(:root|body|html)[ ,{]' design/ists-design-system.scope.css"
verifier_vrai "tous les jetons sont préfixés --ists-" \
              bash -c "! grep -o 'var(--[a-z0-9-]*' design/ists-design-system.scope.css | grep -qv 'var(--ists-'"
verifier_vrai "chaque sélecteur est porté par .ists-v9" \
              bash -c "! grep -E '^[^@/*[:space:]].*\{' design/ists-design-system.scope.css | grep -qv 'ists-v9'"

verifier "les 5 zones de démonstration sont balisées dans la maquette" \
         "5" "$(grep -c 'data-donnee-exemple' "$MAQUETTE")"
verifier "la règle donnee-exemple est active sur le bloc" \
         "5" "$(node tools/audit-ui.mjs docs/bloc-vue-ensemble.html --json | node -e '
                  let d = ""; process.stdin.on("data", (c) => d += c).on("end", () => {
                    const r = JSON.parse(d)[0].resultats.filter((x) => x.regle === "donnee-exemple");
                    process.stdout.write(String(r.length));
                  });')"

echo
echo "7. Bloc prêt à coller (documentation)"
if python3 tests/verifier-bloc.py > "$TRAVAIL/bloc.log" 2>&1; then
  ok "bloc autonome, isolé et conforme ($(grep -c '  OK' "$TRAVAIL/bloc.log") contrôles)"
else
  echec "bloc non conforme — voir : python3 tests/verifier-bloc.py"
fi

echo
echo "─────────────────────────────────────────────"
if [ "$echecs" -eq 0 ]; then
  printf ' %s : %d/%d contrôles réussis\n\n' "${VERT}SUCCÈS${RAZ}" "$controles" "$controles"
else
  printf ' %s : %d/%d contrôles réussis (%d en échec)\n\n' \
         "${ROUGE}ÉCHEC${RAZ}" "$((controles - echecs))" "$controles" "$echecs"
fi
exit $((echecs > 0))
