"""Automatic audit of the deliverables: punctuation, language, plain words, numbers, brief, PDFs.

Run: python tools/audit.py   (exit code 1 if a check fails)
"""

import re
import runpy
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
N = runpy.run_path(str(ROOT / "dossier" / "calc.py"))
fails, notes = [], []


def html_text(path):
    h = path.read_text(encoding="utf-8")
    h = re.sub(r"<style.*?</style>|<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"data:image/[^\"')]+", " ", h)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


docs = {
    "deck": html_text(ROOT / "dossier" / "deck.html"),
    "report": html_text(ROOT / "dossier" / "report.html"),
    "script": read("dossier/defence_script.md"),
    "email": read("dossier/email_to_professor.md"),
    "numbers": read("dossier/numbers.md"),
    "readme": read("README.md"),
}
code = {p.name: p.read_text(encoding="utf-8") for p in [*sorted((ROOT / "sponsor").glob("*.py")), ROOT / "app.py", *sorted((ROOT / "tests").glob("*.py"))]}

# 1. Natural punctuation: no long dash, en dash, arrow, middle dot; no spaced hyphen used as a dash
for name, txt in {**docs, **code}.items():
    if name.startswith("test_units"):
        continue  # the tests contain these characters on purpose
    bad = re.findall(r"[—–―→←⇒·]", txt)
    if bad:
        fails.append(f"{name}: forbidden characters {sorted(set(bad))}")
    if name in docs:
        spaced = re.findall(r".{20} - .{20}", txt)
        if spaced:
            fails.append(f"{name}: spaced hyphen used as a dash, for example: {spaced[0]}")

# 2. English only (French business names used as examples are allowed)
ALLOWED = ["Pharmacie des Tilleuls", "Agence immobilière Century", "Cave à vins du Rhône", "Cave à vins", "AS Val de Saône", "Chez Momo", "Wine cellar of the Rhône", "Saône", "Rhône",
           "Boulangerie de Paris", "Boulangerie Dupont", "Pharmacie du Centre", "Garage Vincent", "Casino de Lyon", "Tabac Presse Centrale", "Agence immobilière", "Boulangerie", "Pharmacie"]
FRENCH_WORDS = re.compile(r"\b(le|la|les|des|une|pour|avec|dans|est|sont|aux|chaque|nous|vous|aucun|plus)\b")
for name, txt in {**docs, **code}.items():
    t = txt
    for a in sorted(ALLOWED, key=len, reverse=True):
        t = t.replace(a, " ")
    if name == "guardrail.py":
        continue  # keyword lists contain French words on purpose
    accents = sorted(set(re.findall(r"\w*[éèêëàâùûçôîïÉÈÀ]\w*", t)))
    if accents:
        fails.append(f"{name}: French accents found: {accents[:6]}")
    if name in docs:
        words = sorted(set(FRENCH_WORDS.findall(t)) & {"le", "la", "les", "des", "une", "pour", "avec", "dans", "sont", "aux", "chaque", "nous", "vous", "aucun"})
        if words:
            fails.append(f"{name}: French words found: {words}")

# 3. Plain vocabulary: no showy words
SHOWY = ["leverage", "utilize", "robust", "seamless", "comprehensive", "furthermore", "moreover", "delve", "synergy", "holistic",
         "cutting-edge", "state-of-the-art", "game-changer", "revolutionize", "empower", "streamline", "paradigm", "ecosystem", "orchestrat"]
for name in ("deck", "report", "script", "email"):
    low = docs[name].lower()
    hits = [w for w in SHOWY if w in low]
    if hits:
        fails.append(f"{name}: showy words {hits}")
report_html = (ROOT / "dossier" / "report.html").read_text(encoding="utf-8")
paragraphs = [re.sub(r"<[^>]+>", " ", m) for m in re.findall(r"<p>(.*?)</p>", report_html, flags=re.S)]
sentences = [s for para in paragraphs for s in re.split(r"(?<=[.!?])\s+", " ".join(para.split())) if len(s.split()) > 3]
long = [s for s in sentences if len(s.split()) > 38]
avg = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
notes.append(f"report: average sentence length {avg:.1f} words")
if long:
    fails.append(f"report: {len(long)} sentence(s) over 38 words, for example: {long[0][:90]}")

# 4. Numbers agree between deck, report and script
def digits(s):
    return re.sub(r"[^0-9]", "", s)


checks = {
    "ask": (f"{N['ask']:,}", ["deck", "report", "script"]),
    "break-even clubs": (str(N["breakeven_clubs"]), ["deck", "report", "script"]),
    "break-even month": (f"month {N['be_month']}", ["deck", "report", "script"]),
    "mid price": (f"€{N['PRICE_MONTH']['mid']}", ["deck", "report", "script"]),
    "big price": (f"€{N['PRICE_MONTH']['flagship']}", ["deck", "report"]),
    "share of value": (f"{N['I']['capture'] * 100:.0f}%", ["deck", "report", "script"]),
    "gross margin": (f"{N['contrib'] / N['blend_price'] * 100:.0f}%", ["deck", "report"]),
    "reachable clubs": (f"{N['sam_clubs']:,}", ["deck", "report", "script"]),
    "total clubs": (f"{N['n_mid'] + N['n_flag']:,}", ["deck", "report", "script"]),
    "target clubs": (str(N["som_clubs"]), ["deck", "report", "script"]),
    "target revenue": (f"{N['SOM']:,.0f}", ["report", "script"]),
}
for label, (needle, where) in checks.items():
    for w in where:
        if needle not in docs[w] and digits(needle) not in digits(docs[w]):
            fails.append(f"{w}: '{label}' ({needle}) not found")

# 5. The brief: 10 slides in the right order, with the right names
LABELS = ["1 Problem", "2 Solution", "3 Live demo", "4 Market analysis", "5 Business model and price", "6 Traction",
          "7 Competition and defensibility", "8 Team", "9 Financials", "10 The ask"]
deck = pymupdf.open(ROOT / "dossier" / "deck.pdf")
if len(deck) != 10:
    fails.append(f"deck.pdf has {len(deck)} pages, the brief asks for 10")
for i, (p, label) in enumerate(zip(deck, LABELS), 1):
    first = " ".join(p.get_text().split())[: len(label) + 2]
    if not first.startswith(label):
        fails.append(f"slide {i}: expected the section name '{label}', found '{first}'")
    words = len(p.get_text().split())
    notes.append(f"slide {i}: {words} words")
    if words > 110:
        fails.append(f"slide {i}: {words} words (limit 110)")
if "moment of truth" not in docs["deck"].lower():
    fails.append("deck: the moment of truth is not stated")
if "mailto" in docs["email"].lower() or "report" in docs["email"].lower().split("---")[0]:
    fails.append("email: the email mentions something the brief does not ask for")

# 6. PDF format
for name, pages, size in (("deck", 10, (960, 540)), ("report", None, (595, 842))):
    doc = pymupdf.open(ROOT / "dossier" / f"{name}.pdf")
    w, h = doc[0].rect.width, doc[0].rect.height
    if abs(w - size[0]) > 3 or abs(h - size[1]) > 3:
        fails.append(f"{name}.pdf: size {w:.0f}x{h:.0f} instead of {size}")
    empty = [i + 1 for i, p in enumerate(doc) if len(p.get_text().strip()) < 40]
    if empty:
        fails.append(f"{name}.pdf: almost empty pages {empty}")
    notes.append(f"{name}.pdf: {len(doc)} pages, {w:.0f}x{h:.0f} pt")

# 7. What still has to be filled in before sending
pending = []
for name in ("deck", "report", "email"):
    for token in ("Name to add", "name to add", "PASTE THE LIVE LINK", "FIRST NAMES", "SIGNATURE", "Live link added at submission", "in the submission email"):
        if token in docs[name]:
            pending.append(f"{name}: '{token}'")
if pending:
    notes.append("To fill in: " + "; ".join(pending))

print("\n".join(notes))
if fails:
    print("\nFAILED:")
    print("\n".join(" - " + f for f in fails))
    sys.exit(1)
print("\nAudit: all automatic checks pass.")
