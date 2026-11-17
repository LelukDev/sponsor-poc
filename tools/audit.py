"""Audit automatique des livrables : ponctuation, cohérence des chiffres, PDF, champs à remplir.

Usage : python tools/audit.py   (code de sortie 1 si une vérification échoue)
"""

import re
import runpy
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
N = runpy.run_path(str(ROOT / "dossier" / "calc.py"))
fails, notes = [], []


def text_of_html(path):
    h = path.read_text(encoding="utf-8")
    h = re.sub(r"<style.*?</style>|<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"data:image/[^\"')]+", " ", h)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))


docs = {
    "deck": text_of_html(ROOT / "dossier" / "deck.html"),
    "report": text_of_html(ROOT / "dossier" / "report.html"),
    "script": (ROOT / "dossier" / "script_soutenance.md").read_text(encoding="utf-8"),
    "mail": (ROOT / "dossier" / "mail_prof.md").read_text(encoding="utf-8"),
    "chiffres": (ROOT / "dossier" / "chiffres.md").read_text(encoding="utf-8"),
    "readme": (ROOT / "README.md").read_text(encoding="utf-8"),
}

# 1. Ponctuation : aucun tiret long, demi-cadratin, flèche, point médian ; pas de tiret spacé comme ponctuation
for name, txt in docs.items():
    bad = re.findall(r"[—–―→←⇒·]", txt)
    if bad:
        fails.append(f"{name}: caractères interdits {sorted(set(bad))}")
    spaced = re.findall(r".{20} - .{20}", txt)
    if spaced:
        fails.append(f"{name}: tiret spacé comme ponctuation, par exemple « {spaced[0]} »")

# 2. Cohérence des chiffres entre le deck, le rapport et le script
def digits(s):
    return re.sub(r"[^0-9]", "", s)

checks = {
    "demande": (f"{N['ask']:,}", ["deck", "report"]),
    "seuil de rentabilité": (str(N["breakeven_clubs"]), ["deck", "report", "script"]),
    "mois de rentabilité": (f"month {N['be_month']}", ["deck", "report"]),
    "prix club": (f"€{N['PRICE_MONTH']['intermediaire']}", ["deck", "report"]),
    "prix club+": (f"€{N['PRICE_MONTH']['phare']}", ["deck", "report"]),
    "part de valeur": (f"{N['I']['capture'] * 100:.0f}%", ["deck", "report"]),
    "marge brute": (f"{N['contrib'] / N['blend_price'] * 100:.0f}%", ["deck", "report"]),
    "clubs SAM": (f"{N['sam_clubs']:,}", ["deck", "report"]),
    "clubs TAM": (f"{N['n_inter'] + N['n_phare']:,}", ["deck", "report"]),
    "clubs à 3 ans": (str(N["som_clubs"]), ["deck", "report", "script"]),
}
for label, (needle, where) in checks.items():
    for w in where:
        hay = docs[w]
        ok = needle in hay or digits(needle) in digits(hay)
        if not ok:
            fails.append(f"{w}: « {label} » ({needle}) introuvable")

# 3. PDF
for name, expect_pages, expect_size in (("deck", 10, (960, 540)), ("report", None, (595, 842))):
    path = ROOT / "dossier" / f"{name}.pdf"
    doc = pymupdf.open(path)
    w, h = doc[0].rect.width, doc[0].rect.height
    if expect_pages and len(doc) != expect_pages:
        fails.append(f"{name}.pdf: {len(doc)} pages au lieu de {expect_pages}")
    if abs(w - expect_size[0]) > 3 or abs(h - expect_size[1]) > 3:
        fails.append(f"{name}.pdf: format {w:.0f}x{h:.0f} au lieu de {expect_size}")
    empty = [i + 1 for i, p in enumerate(doc) if len(p.get_text().strip()) < 40]
    if empty:
        fails.append(f"{name}.pdf: pages presque vides {empty}")
    notes.append(f"{name}.pdf: {len(doc)} pages, {w:.0f}x{h:.0f} pt")

# 4. Texte par slide : peu de mots (le deck doit rester sobre)
deck = pymupdf.open(ROOT / "dossier" / "deck.pdf")
for i, p in enumerate(deck, 1):
    words = len(p.get_text().split())
    if words > 110:
        fails.append(f"deck: slide {i} a {words} mots (limite 110)")
    notes.append(f"slide {i}: {words} mots")

# 5. Champs à remplir avant l'envoi
pending = []
for name, txt in docs.items():
    for token in ("Name to add", "name to add", "LIEN DE LA DÉMO", "NOMS", "SIGNATURE", "added at submission", "given in the submission"):
        if token in txt:
            pending.append(f"{name}: « {token} »")
if pending:
    notes.append("À compléter : " + " ; ".join(pending))

print("\n".join(notes))
if fails:
    print("\nÉCHECS :")
    print("\n".join(" - " + f for f in fails))
    sys.exit(1)
print("\nAudit : toutes les vérifications automatiques passent.")
