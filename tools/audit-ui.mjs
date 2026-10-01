#!/usr/bin/env node
/**
 * audit-ui.mjs — Audit d'interface pour les écrans ISTS Campus (Potter's Bible University).
 *
 * Repère automatiquement les défauts de finition qui rendent une interface
 * « peu professionnelle » : emojis utilisés comme icônes, libellés tronqués,
 * largeurs fixes qui débordent sur mobile, manques d'accessibilité.
 *
 * Usage :
 *   node tools/audit-ui.mjs <fichier.html> [autres.html ...]
 *   node tools/audit-ui.mjs --json design/index.html
 *
 * Code de sortie : 1 si au moins une erreur est détectée, 0 sinon.
 * Aucune dépendance externe.
 */

import { readFileSync } from 'node:fs';
import { basename } from 'node:path';
import { pathToFileURL } from 'node:url';

/* ------------------------------------------------------------------ règles */

// Pictogrammes Unicode (couvre 🔍 📥 🩺 📤 🔔 🏛️ ✅ ❌ ⚠️ …) + sélecteurs de variante
const RE_EMOJI = /\p{Extended_Pictographic}|\uFE0F|\u200D/gu;
// Symboles typographiques souvent détournés en icônes : tolérés mais signalés
const RE_SYMBOLE = /[✓✔✗✘★☆⇒➜➔⬅➡⬆⬇]/gu;

const REGLES = [
  {
    id: 'emoji',
    gravite: 'erreur',
    titre: 'Emoji utilisé comme icône',
    conseil: 'Remplacer par une icône SVG inline (trait currentColor, grille 24 × 24).',
  },
  {
    id: 'largeur-fixe',
    gravite: 'erreur',
    titre: 'Largeur fixe ≥ 240 px sur un conteneur',
    conseil: 'Utiliser minmax(0, 1fr), max-width: 100 % ou flex-wrap pour éviter le débordement.',
  },
  {
    id: 'troncature',
    gravite: 'avertissement',
    titre: 'Risque de libellé tronqué (nowrap/ellipsis sur du texte)',
    conseil: 'Autoriser le retour à la ligne (white-space: normal) plutôt que couper le libellé.',
  },
  {
    id: 'outline-none',
    gravite: 'erreur',
    titre: 'Contour de focus supprimé',
    conseil: 'Restaurer un anneau visible via :focus-visible (navigation clavier).',
  },
  {
    id: 'bouton-icone-sans-libelle',
    gravite: 'erreur',
    titre: 'Bouton-icône sans nom accessible',
    conseil: 'Ajouter un aria-label ou un texte visible.',
  },
  {
    id: 'img-sans-alt',
    gravite: 'erreur',
    titre: 'Image sans attribut alt',
    conseil: 'Ajouter alt="…" (ou alt="" si l’image est purement décorative).',
  },
  {
    id: 'viewport',
    gravite: 'erreur',
    titre: 'Balise meta viewport absente',
    conseil: 'Ajouter <meta name="viewport" content="width=device-width, initial-scale=1">.',
  },
  {
    id: 'lang',
    gravite: 'erreur',
    titre: 'Attribut lang absent de <html>',
    conseil: 'Ajouter lang="fr" sur la balise <html>.',
  },
  {
    id: 'titre-couleur-seule',
    gravite: 'avertissement',
    titre: 'Balise <font> ou style de couleur en ligne',
    conseil: 'Passer par les jetons de couleur du design system.',
  },
  {
    id: 'symbole-texte',
    gravite: 'avertissement',
    titre: 'Symbole typographique employé comme icône',
    conseil: 'Préférer une icône SVG pour un rendu homogène selon les polices.',
  },
];

/* ------------------------------------------------------------- utilitaires */

const lignes = (src) => src.split(/\r\n|\n|\r/);

/** Position (ligne, colonne) d'un index absolu. */
function position(src, index) {
  const avant = src.slice(0, index);
  const ligne = avant.split(/\r\n|\n|\r/).length;
  const derniere = avant.lastIndexOf('\n');
  return { ligne, colonne: index - derniere };
}

/** Retire les commentaires HTML pour ne pas signaler le code commenté. */
function sansCommentaires(src) {
  return src.replace(/<!--[\s\S]*?-->/g, (m) => m.replace(/[^\n]/g, ' '));
}

function signaler(resultats, regle, src, index, extrait) {
  const { ligne, colonne } = position(src, index);
  resultats.push({
    regle: regle.id,
    gravite: regle.gravite,
    titre: regle.titre,
    conseil: regle.conseil,
    ligne,
    colonne,
    extrait: extrait.replace(/\s+/g, ' ').trim().slice(0, 90),
  });
}

/* ------------------------------------------------------------------ règles */

function analyserEmojis(src, brut, res) {
  for (const m of brut.matchAll(RE_EMOJI)) {
    const cp = m[0].codePointAt(0).toString(16).toUpperCase().padStart(4, '0');
    signaler(res, REGLES[0], src, m.index, `U+${cp} « ${m[0]} » … ${brut.slice(m.index, m.index + 40)}`);
  }
  for (const m of brut.matchAll(RE_SYMBOLE)) {
    signaler(res, REGLES[9], src, m.index, `« ${m[0]} » … ${brut.slice(m.index, m.index + 40)}`);
  }
}

function analyserStyles(src, res) {
  const blocs = src.match(/<style[^>]*>([\s\S]*?)<\/style>/gi) || [];
  const css = blocs.map((b) => b.replace(/<\/?style[^>]*>/gi, '')).join('\n');
  const decalage = blocs.length ? src.indexOf(css.slice(0, 40).trim() || css) : 0;

  // Analyse règle par règle : éviter les faux positifs d'un sélecteur à l'autre.
  for (const regle of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const selecteur = regle[1].trim().replace(/\s+/g, ' ');
    const corps = regle[2];
    const index = decalage + regle.index;

    // Conteneurs à largeur fixe
    for (const m of corps.matchAll(/(?:^|[;\s])(min-)?width\s*:\s*(\d{3,})px/gi)) {
      if (Number(m[2]) >= 240) signaler(res, REGLES[1], src, index, `${selecteur} { ${m[0].trim()} }`);
    }

    // Libellés tronqués (on ignore le contenu masqué aux lecteurs d'écran)
    const masque = /clip\s*:\s*rect|clip-path|\.sr-only|visually-hidden/i.test(selecteur + corps);
    if (/white-space\s*:\s*nowrap/i.test(corps) && /text-overflow\s*:\s*ellipsis|overflow\s*:\s*hidden/i.test(corps) && !masque) {
      signaler(res, REGLES[2], src, index, `${selecteur} { white-space:nowrap + overflow }`);
    }

    // Contour de focus supprimé
    if (/outline\s*:\s*(?:none|0)/i.test(corps) && !/:focus-visible/.test(selecteur)) {
      signaler(res, REGLES[3], src, index, `${selecteur} { outline:none }`);
    }
  }
}

function analyserBalises(src, res) {
  // Boutons-icône : <button …> ne contenant qu'un <svg>/<img>/<i> et pas d'aria-label
  for (const m of src.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/gi)) {
    const attrs = m[1];
    const contenu = m[2].replace(/<[^>]+>/g, '').trim();
    const aUnLabel = /aria-label\s*=|aria-labelledby\s*=|title\s*=/i.test(attrs);
    if (!contenu && !aUnLabel) {
      signaler(res, REGLES[4], src, m.index, m[0]);
    }
  }
  for (const m of src.matchAll(/<img\b([^>]*)>/gi)) {
    if (!/\balt\s*=/i.test(m[1])) signaler(res, REGLES[5], src, m.index, m[0]);
  }
  if (!/<meta[^>]+name=["']viewport["']/i.test(src)) {
    signaler(res, REGLES[6], src, 0, '<head> : meta viewport manquante');
  }
  if (!/<html[^>]*\blang=/i.test(src)) {
    signaler(res, REGLES[7], src, 0, '<html> : attribut lang manquant');
  }
  for (const m of src.matchAll(/style\s*=\s*["'][^"']*color\s*:/gi)) {
    signaler(res, REGLES[8], src, m.index, m[0]);
  }
}

/** Vérifie la continuité de la hiérarchie des titres (h1 → h2 → h3). */
function analyserTitres(src, res) {
  const niveaux = [...src.matchAll(/<h([1-6])\b/gi)].map((m) => Number(m[1]));
  const probleme = (indice, message) => res.push({
    regle: 'hierarchie-titres', gravite: 'avertissement',
    titre: 'Hiérarchie de titres incohérente',
    conseil: 'Enchaîner les niveaux sans saut (h1 → h2 → h3) pour les lecteurs d’écran.',
    ligne: position(src, indice).ligne, colonne: position(src, indice).colonne,
    extrait: message,
  });
  if (!niveaux.length) return;
  if (niveaux.filter((n) => n === 1).length !== 1) {
    probleme(src.indexOf('<h1'), `${niveaux.filter((n) => n === 1).length} balise(s) h1 détectée(s) — il en faut une seule`);
  }
  for (let i = 1; i < niveaux.length; i++) {
    if (niveaux[i] - niveaux[i - 1] > 1) {
      probleme(src.indexOf(`<h${niveaux[i]}`), `saut de h${niveaux[i - 1]} à h${niveaux[i]}`);
    }
  }
}

/* --------------------------------------------------------------------- API */

export function auditer(chemin) {
  const brut = readFileSync(chemin, 'utf8');
  const src = sansCommentaires(brut);
  const res = [];

  analyserEmojis(src, brut, res);
  analyserStyles(src, res);
  analyserBalises(src, res);
  analyserTitres(src, res);

  res.sort((a, b) => a.ligne - b.ligne || a.colonne - b.colonne);
  return { fichier: chemin, resultats: res };
}

/* ---------------------------------------------------------------------- CLI */

function rendreRapport({ fichier, resultats }) {
  const erreurs = resultats.filter((r) => r.gravite === 'erreur');
  const avertissements = resultats.filter((r) => r.gravite === 'avertissement');

  console.log(`\n\u2500\u2500\u2500 Audit d'interface : ${basename(fichier)} \u2500\u2500\u2500`);
  if (!resultats.length) {
    console.log('  Aucun défaut détecté. Interface conforme aux conventions du projet.\n');
    return 0;
  }
  for (const [titre, lot] of [['ERREURS', erreurs], ['AVERTISSEMENTS', avertissements]]) {
    if (!lot.length) continue;
    console.log(`\n  ${titre} (${lot.length})`);
    for (const r of lot) {
      console.log(`   · ${r.titre}`);
      console.log(`     ligne ${r.ligne}, col. ${r.colonne} — ${r.extrait}`);
      console.log(`     → ${r.conseil}`);
    }
  }
  console.log(`\n  Total : ${erreurs.length} erreur(s), ${avertissements.length} avertissement(s).\n`);
  return erreurs.length ? 1 : 0;
}

const appeleDirectement = import.meta.url === pathToFileURL(process.argv[1] ?? '').href;
const args = appeleDirectement ? process.argv.slice(2) : [];
const enJson = args.includes('--json');
const fichiers = args.filter((a) => !a.startsWith('--'));

if (appeleDirectement && !fichiers.length) {
  console.error('Usage : node tools/audit-ui.mjs [--json] <fichier.html> [...]');
  process.exit(2);
}

let code = 0;
const rapports = [];
for (const f of fichiers) {
  try {
    const rapport = auditer(f);
    rapports.push(rapport);
    if (!enJson) code = rendreRapport(rapport) || code;
    else if (rapport.resultats.some((r) => r.gravite === 'erreur')) code = 1;
  } catch (e) {
    console.error(`Impossible de lire « ${f} » : ${e.message}`);
    code = 2;
  }
}
if (appeleDirectement) {
  if (enJson) console.log(JSON.stringify(rapports, null, 2));
  process.exit(code);
}
