"""Collect all final deliverables in one folder (default: the Desktop).

Usage: python tools/package_deliverables.py [target_folder]
Builds the script PDF, then copies deck, email, script, report, numbers and moodboard.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOSSIER = ROOT / "dossier"
TARGET = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Desktop" / "Monetizing-AI-Livrables"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "https://sponsio-club.streamlit.app"

CSS = """
@page { size: A4; margin: 18mm 16mm }
body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1B2430 }
h1 { font-size: 22pt; color: #1F4E8C } h2 { font-size: 15pt; margin-top: 22px; border-bottom: 2px solid #F2B705; padding-bottom: 3px }
h3 { font-size: 12.5pt; margin-top: 16px; color: #1F4E8C }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10pt } th, td { border: 1px solid #D5DAE0; padding: 5px 8px; text-align: left; vertical-align: top } th { background: #F1F3F6 }
p { margin: 6px 0 } li { margin: 3px 0 } em { color: #6B7280 }
"""


def md_to_pdf(src: Path, dst: Path) -> None:
    body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"])
    html = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    tmp = dst.with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={dst}", f"file://{tmp}"], check=True, capture_output=True, timeout=120)
    tmp.unlink()


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    send, defence, support = TARGET / "1_A_ENVOYER_AU_PROF", TARGET / "2_SOUTENANCE", TARGET / "3_SUPPORT"
    for d in (send, defence, support):
        d.mkdir(parents=True)

    shutil.copy(DOSSIER / "deck.pdf", send / "Sponsio_pitch_deck.pdf")
    shutil.copy(DOSSIER / "email_to_professor.md", send / "mail_au_prof.md")
    (send / "LIEN_DEMO.txt").write_text(URL + "\n", encoding="utf-8")

    md_to_pdf(DOSSIER / "defence_script.md", defence / "Script_de_soutenance.pdf")
    shutil.copy(DOSSIER / "defence_script.md", defence / "Script_de_soutenance.md")

    shutil.copy(DOSSIER / "report.pdf", support / "Rapport_d_appui.pdf")
    shutil.copy(DOSSIER / "numbers.md", support / "Chiffres.md")
    shutil.copy(DOSSIER / "moodboard.png", support / "Moodboard.png")

    (TARGET / "LISEZ-MOI.txt").write_text(
        f"""PROJET MONETIZING DATA & AI : SPONSIO
=====================================

1_A_ENVOYER_AU_PROF   -> le SEUL dossier a envoyer (avant lundi 23 novembre 2026)
   - Sponsio_pitch_deck.pdf : le deck de 10 slides (piece jointe)
   - mail_au_prof.md        : le texte du mail, pret a copier
   - LIEN_DEMO.txt          : le lien de la demo ({URL})

2_SOUTENANCE          -> pour vous 4, ne pas envoyer
   - Script_de_soutenance.pdf : qui dit quoi, slide par slide, avec les temps
     (Joshai ouvre, Eyal conclut, environ 13 minutes) + questions du jury

3_SUPPORT             -> ne pas envoyer (le prof ne le demande pas)
   - Rapport_d_appui.pdf, Chiffres.md, Moodboard.png

Code source : https://github.com/LelukDev/sponsor-poc

Repartition : Joshai (intro, 1, 6) / Lucas (2, 3 demo) / Henry (4, 7, 8) / Eyal (5, 9, 10 + conclusion)
Avant la soutenance : ouvrir le lien 10 minutes avant, telephone en partage de connexion en secours.
""",
        encoding="utf-8",
    )
    print(TARGET)
    for p in sorted(TARGET.rglob("*")):
        if p.is_file():
            print(" ", p.relative_to(TARGET), p.stat().st_size // 1024, "KB")


main()
