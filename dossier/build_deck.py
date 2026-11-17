"""Build the 10-slide deck (HTML, then PDF): few words, one visual per slide, plain English.

Run: python dossier/build_deck.py
Inputs: dossier/calc.py (numbers), dossier/deck_config.json (product name, demo link, team)
Outputs: dossier/deck.html and dossier/deck.pdf (headless Chrome)
The 10 section labels follow the brief of the course, in the same order.
"""

import base64
import html
import io
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from sponsor import scenes  # noqa: E402

CFG = json.loads((ROOT / "dossier" / "deck_config.json").read_text())
N = runpy.run_path(str(ROOT / "dossier" / "calc.py"))
NAME, URL = CFG["product_name"], CFG["demo_url"]
INK, NAVY, PAPER, GREY, LINE, ACCENT, PANEL = "#1B2430", "#1F4E8C", "#FAFAF8", "#6B7280", "#E5E7EB", "#F2B705", "#F1F3F6"
I, P = N["I"], N["P"]
COST_TXT = f"${N['small_cost'] + 5e-6:.4f}"


def eur(x, d=0):
    return ("-" if x < 0 else "") + f"€{abs(x):,.{d}f}"


def eur_k(x, d=1):
    return ("-" if x < 0 else "+" if x > 0 else "") + f"€{abs(x) / 1000:,.{d}f}k"


# ---------- Images ----------
def demo_logo() -> Image.Image:
    im = Image.new("RGBA", (760, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 30, 200, 210), fill=(217, 72, 15, 255))
    big = ImageFont.load_default(size=82)
    d.text((235, 40), "GARAGE", font=big, fill=(20, 40, 90, 255))
    d.text((235, 130), "MARTIN", font=big, fill=(217, 72, 15, 255))
    return scenes.prepare_logo(im)


def b64(img: Image.Image, w: int, q: int = 85) -> str:
    img = img.convert("RGB")
    img = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


logo = demo_logo()
img_empty = b64(scenes._plate("pitch_boards"), 760)
img_van = b64(scenes.render_scene("minibus", (0,), logo), 760)
boards_base = scenes.render_scene("pitch_boards", (0,), scenes.wordmark("Mercier Insurance"))
img_boards = b64(scenes.render_scene("pitch_boards", (1, 2, 3), logo, base=boards_base), 760)
img_back = b64(scenes.render_scene("jersey_back", (0,), logo), 760)

# ---------- Cash ----------
cash, cum = [], 0.0
for t in range(37):
    if t > 0:
        cum += N["som_clubs"] * t / 36 * N["contrib"] - N["FIXED_MONTH"]
    cash.append(cum)
t_low = min(range(37), key=lambda t: cash[t])
be_month = N["be_month"]


def chart_svg() -> str:
    W, H, L, R, T, B = 640, 420, 70, 24, 24, 46
    ymin, ymax = -40000, 80000

    def X(t):
        return L + (W - L - R) * t / 36

    def Y(v):
        return T + (H - T - B) * (ymax - v) / (ymax - ymin)

    grid = "".join(
        f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W - R}" y2="{Y(v):.1f}" stroke="{LINE}" stroke-width="1"/>'
        f'<text x="{L - 10}" y="{Y(v) + 5:.1f}" text-anchor="end" font-size="15" fill="{GREY}">{"-" if v < 0 else ""}€{abs(v) // 1000}k</text>'
        for v in range(ymin, ymax + 1, 40000)
    )
    xt = "".join(f'<text x="{X(t):.1f}" y="{H - 20}" text-anchor="middle" font-size="15" fill="{GREY}">{t}</text>' for t in range(0, 37, 12))
    pts = " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in zip(range(37), cash))
    zero = f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W - R}" y2="{Y(0):.1f}" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="5 4"/>'
    be = f'<line x1="{X(be_month):.1f}" y1="{T}" x2="{X(be_month):.1f}" y2="{H - B}" stroke="{ACCENT}" stroke-width="3"/><text x="{X(be_month) + 10:.1f}" y="{T + 16}" font-size="16" fill="{INK}">Break-even, month {be_month}</text>'
    low = f'<circle cx="{X(t_low):.1f}" cy="{Y(cash[t_low]):.1f}" r="5" fill="{NAVY}" stroke="#fff" stroke-width="2"/><text x="{X(be_month) + 12:.1f}" y="{Y(cash[t_low]) + 32:.1f}" font-size="16" fill="{INK}">Lowest cash {eur_k(cash[t_low])}</text>'
    end = f'<circle cx="{X(36):.1f}" cy="{Y(cash[36]):.1f}" r="5" fill="{NAVY}" stroke="#fff" stroke-width="2"/><text x="{X(36) - 12:.1f}" y="{Y(cash[36]) + 6:.1f}" text-anchor="end" font-size="16" fill="{INK}">{eur_k(cash[36])}</text>'
    return (
        f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Cash over 36 months">{grid}{xt}{zero}{be}'
        f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>{low}{end}'
        f'<text x="{(L + W - R) / 2:.0f}" y="{H - 2}" text-anchor="middle" font-size="15" fill="{GREY}">Months after launch</text></svg>'
    )


def bars_svg() -> str:
    """Value created, price and cost to serve for a mid-size club, per month."""
    rows = [("Value created", I["y1_month"], "#B9C9E2"), ("Our price", N["PRICE_MONTH"]["mid"], NAVY), ("Cost to serve", N["COST_SERVE_MONTH"]["mid"], "#9AA3AF")]
    W, L, maxw = 620, 170, 380
    out = []
    for i, (lab, v, col) in enumerate(rows):
        y = 12 + i * 74
        w = max(8, maxw * v / I["y1_month"])
        out.append(f'<text x="0" y="{y + 30}" font-size="22" fill="{INK}">{lab}</text><rect x="{L}" y="{y}" width="{w:.0f}" height="44" rx="4" fill="{col}"/><text x="{L + w + 12:.0f}" y="{y + 31}" font-size="26" font-weight="700" fill="{INK}">{eur(v)}</text>')
    return f'<svg viewBox="0 0 {W} 240" width="{W}" height="240" role="img" aria-label="Value, price and cost per month for a mid-size club">{"".join(out)}</svg>'


# ---------- Layout ----------
def slide(n, label, title, body, source=""):
    return (
        f'<section class="slide"><div class="label">{n} {label}</div><h1>{title}</h1>{body}'
        f'<div class="foot"><span>{html.escape(source)}</span><span>{n} / 10</span></div></section>'
    )


def bullets(items):
    return "<ul class='b'>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


s = []


def chips(items):
    return "<div class='chips'>" + "".join(f"<span>{i}</span>" for i in items) + "</div>"


def kv(items):
    return "<div class='kv'>" + "".join(f"<div><strong>{a}</strong><span>{b}</span></div>" for a, b in items) + "</div>"


def lead(items):
    return "<ul class='b l'>" + "".join(f"<li><b>{a}</b><span>{b}</span></li>" for a, b in items) + "</ul>"


mid_base = I["base"]
s.append(slide(1, "Problem", "Clubs have space to sell but no time to sell it", f"""
<div class="two">
<div>{lead([("The same pitch for everyone", "one PDF sent to every business"), ("Sold slots are offered again", "nobody has the list in mind"), ("Offers ignore the club's needs", "no link to the minibus or the tournament")])}
<div class="persona"><b>Julien</b>, volunteer treasurer of a club with 320 members. He writes every offer alone, in the evening. (An example.)</div></div>
<div><img class="photo" src="{img_empty}" alt="Empty advertising boards"><div class="stats"><div><span>9%</span>of a club's money comes from sponsors</div><div><span>37%</span>of clubs lose money</div><div><span>{eur(mid_base)}</span>sponsoring a year, mid-size club</div></div></div>
</div>""", "Source: CNOSF study on club funding (old data, rough numbers). Club size: average budget of €80,145."))

s.append(slide(2, "Solution", "An AI assistant that writes the offer and shows the logo", f"""
<div class="moment"><b>Our moment of truth:</b> type a business name, get an offer with its logo on the kit.</div>
<div class="steps"><div><i>1</i><b>The club lists its slots</b><span>prices, sponsors, needs</span></div><div><i>2</i><b>AI picks, code checks</b><span>free slots, real prices</span></div><div><i>3</i><b>Realistic photos</b><span>logo placed on the kit</span></div></div>
<div class="ba"><figure><img src="{img_empty}"><figcaption>Before: empty boards</figcaption></figure><figure><img src="{img_boards}"><figcaption>After: the sponsor's logo on the boards</figcaption></figure></div>
{chips(["Only free slots", "Price from the club's list", "Sector conflicts flagged", "Alcohol, tobacco, betting blocked"])}""", "The logo and sponsors shown are examples."))

demo_line = f"Try it: {URL}" if URL else "Live link added at submission"
s.append(slide(3, "Live demo", "Live demo: you choose the business", f"""
<div class="two" style="grid-template-columns:.8fr 1.2fr">
<div>{bullets(["Name any local business", "Upload any logo", "See the offer: 3 packages, photos, email", "Free or take a slot, and the offer changes"])}<div class="url">{html.escape(demo_line)}</div><p class="small">About {COST_TXT} and 4 to 5 seconds per offer.</p>{chips(["Try a competitor of a sponsor", "Try a wine bar"])}</div>
<div class="mosaic"><figure class="wide"><img src="{img_van}"><figcaption>Minibus: linked to the club's need to replace it</figcaption></figure><figure><img src="{img_boards}"><figcaption>Pitch boards</figcaption></figure><figure><img src="{img_back}"><figcaption>Jersey back</figcaption></figure></div>
</div>""", "The logo shown is an example."))

s.append(slide(4, "Market analysis", "A small market that we can count", f"""
<div class="funnel">
<div class="card"><em>Total market</em><strong>{eur(N['TAM'] / 1e6, 1)}M</strong><span>{N['n_mid'] + N['n_flag']:,} clubs that can pay × €{N['arpa']['mid']} to €{N['arpa']['flagship']:,} a year</span></div>
<div class="card"><em>Market we can reach</em><strong>{eur(N['SAM'] / 1e6, 2)}M</strong><span>{N['sam_clubs']:,} football and rugby clubs</span></div>
<div class="card hl"><em>Our target in 3 years</em><strong>{eur(N['SOM'] / 1000)}k</strong><span>{N['som_clubs']} clubs, {N['som_per_month']:.0f} new clubs a month</span></div>
</div>
<table class="tbl t2"><tr><th>Club size</th><th>Share of clubs</th><th>Budget</th><th>Our answer</th></tr>
<tr><td>Mid-size</td><td>31%</td><td>about €80k</td><td>€15 a month</td></tr>
<tr><td>Flagship</td><td>3%</td><td>about €918k</td><td>€150 a month</td></tr>
<tr><td>Small</td><td>66%</td><td>about €12k</td><td>Left out: gain too small to pay</td></tr></table>""",
    "Sources: CNOSF club types, club counts from the football and rugby federations. Prices are our assumptions."))

s.append(slide(5, "Business model and price", f"€{N['PRICE_MONTH']['mid']} a month, which is {I['capture'] * 100:.0f}% of the value we create", f"""
<div class="two" style="grid-template-columns:1.1fr .9fr">
<div>{bars_svg()}<p class="small" style="margin-top:0">Mid-size club, per month. Value assumes 30% more sponsoring and 40% use in year 1.</p></div>
<div><ul class='b s'><li>Monthly subscription per club</li><li>Price is 10 to 30% of the gain</li><li>Cheaper than club software (€19 to €49)</li><li>Big clubs pay €{N['PRICE_MONTH']['flagship']} a month</li></ul></div>
</div>
{kv([(eur(I['y1']), "net gain for the club in year 1"), (eur(I['price_year']), "price for the club in a year"), (f"{I['roi'] * 100:.0f}%", "return for the club in year 1")])}""", "Prices and the 30% rise are assumptions, tested in pilots."))

s.append(slide(6, "Traction", "No paying club yet. Here is our plan.", f"""
<div class="three">
<div class="panel"><h3>Proven today</h3>{bullets(["Live demo on any business", f"{COST_TXT} and 4 to 5 s per offer", "Taken slots never offered", "Sector conflicts flagged"])}</div>
<div class="panel"><h3>Next 30 days</h3>{bullets(["Call 10 mid-size clubs", "Start 3 pilot clubs", "Meet 2 district or league contacts"])}</div>
<div class="panel"><h3>Still to prove</h3>{bullets(["Sponsoring really rises", "Clubs pay €15 a month", "Districts pass the tool on"])}</div>
</div>
<div class="moment" style="margin:26px 0 0">Pilot goal: <b>+15% sponsoring</b>, or <b>2 new sponsors</b> per club, over one season.</div>""", ""))

s.append(slide(7, "Competition and defensibility", "Others write offers or find deals. We show the logo on the kit.", """
<div class="two" style="grid-template-columns:1.35fr .65fr">
<table class="tbl"><tr><th>Player</th><th>What it does</th><th>What is missing</th></tr>
<tr><td>All Sponsored</td><td>Finds deals online</td><td>No logo mock-up</td></tr>
<tr><td>Leedeel</td><td>Brands and clubs site</td><td>No mock-up</td></tr>
<tr><td>Spencer.club</td><td>Human matchmaker</td><td>Slow, one by one</td></tr>
<tr><td>Proposal tools</td><td>Generic templates</td><td>No slots, no photos</td></tr></table>
<div class="panel"><h3>How we stay ahead</h3><ul class="b"><li>Data on which offers work</li><li>Links with districts and leagues</li><li>The club keeps its data with us</li></ul></div>
</div>
<p class="small">A prompt can be copied. Data, partners and habits cannot.</p>""", "Sources: company websites and press. We did not test these products."))

PEOPLE = [
    ("AI and product build", "Built the app, the checks and the photos", "Slides 2 and 3"),
    ("Clubs and partnerships", "Club needs, pilots, districts and leagues", "Slides 1 and 6"),
    ("Finance and pricing", "Market size, price and cash plan", "Slides 4, 5 and 9"),
    ("Design and communication", "Pitch, slides and competition", "Slides 7, 8 and 10"),
]
cards = "".join(
    f'<div class="person"><div class="avatar">{html.escape(m["name"][0])}</div><b>{html.escape(m["name"])}</b><span class="role">{html.escape(m["role"])}</span><span>{html.escape(PEOPLE[i][1])}</span><em>{html.escape(PEOPLE[i][2])}</em></div>'
    for i, m in enumerate(CFG["team"])
)
s.append(slide(8, "Team", "Four people, four parts of the project", f'<div class="team">{cards}</div><div class="moment" style="margin-top:26px">Product, clubs, finance and communication: <b>every part of the project has an owner</b>. We each present our own part and answer questions on it.</div><p class="small">MSc students at Albert School.</p>', ""))

rows = "".join(
    f"<tr><td>Month {t}</td><td>{n:.0f}</td><td>{eur(rev)}</td><td>{eur_k(c)}</td></tr>"
    for t, n, rev, m_, c in N["rows"] if t in (6, 12, 24, 36)
)
s.append(slide(9, "Financials", f"We break even at {N['breakeven_clubs']} clubs, in month {be_month}", f"""
<div class="two" style="grid-template-columns:640px 1fr">
<div>{chart_svg()}<p class="small">Cash over time. Fixed costs {eur(N['FIXED_MONTH'])} a month. Clubs grow in a straight line to {N['som_clubs']}.</p></div>
<div><div class="kpis row"><div><span>{N['contrib'] / N['blend_price'] * 100:.0f}%</span>gross margin</div><div><span>{N['breakeven_clubs']}</span>clubs to break even</div></div>
<table class="tbl t2"><tr><th></th><th>Clubs</th><th>Revenue a month</th><th>Cash</th></tr>{rows}</table></div>
</div>""", f"Prices: €{N['PRICE_MONTH']['mid']} and €{N['PRICE_MONTH']['flagship']} a month. These are our assumptions."))

s.append(slide(10, "The ask", f"We ask for {eur(N['ask'])} to reach break-even", f"""
<div class="two" style="grid-template-columns:.9fr 1.1fr">
<div class="ask">{eur(N['ask'])}<small>for 18 months</small></div>
<div><h3>Where the money goes</h3>
<table class="tbl t2"><tr><td>Cash gap before break-even</td><td>{eur(-N['trough'])}</td></tr><tr><td>6 months of safety (fixed costs)</td><td>{eur(6 * N['FIXED_MONTH'])}</td></tr><tr><td>Rounded up</td><td>{eur(N['ask'])}</td></tr></table>
<h3 style="margin-top:22px">What we will deliver</h3>{bullets(["3 pilot clubs with measured results", "1 district or league agreement", f"{N['breakeven_clubs']} paying clubs"])}</div>
</div>""", ""))

CSS = f"""
@page {{ size: 1280px 720px; margin: 0 }}
* {{ box-sizing: border-box }}
body {{ margin:0; font-family:"Helvetica Neue",Helvetica,Arial,sans-serif; color:{INK}; background:{PAPER} }}
.slide {{ width:1280px; height:720px; position:relative; padding:60px 84px 60px; page-break-after:always; overflow:hidden; background:{PAPER} }}
.label {{ display:inline-block; font-size:17px; font-weight:700; color:{NAVY}; border-left:6px solid {ACCENT}; padding-left:12px; margin-bottom:18px; letter-spacing:.02em }}
h1 {{ font-size:46px; line-height:1.14; margin:0 0 32px; max-width:1100px; font-weight:700 }}
h3 {{ font-size:22px; margin:0 0 14px; color:{NAVY} }}
.small {{ font-size:16px; color:{GREY}; margin:12px 0 0; line-height:1.4 }}
.foot {{ position:absolute; left:84px; right:84px; bottom:26px; font-size:13px; color:{GREY}; display:flex; justify-content:space-between }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:start }}
ul.b {{ margin:0; padding-left:26px; font-size:30px; line-height:1.35 }} ul.b li {{ margin-bottom:16px }}
.panel {{ background:{PANEL}; border-radius:14px; padding:26px 30px }} .panel ul.b {{ font-size:27px }}
.photo {{ width:100%; border-radius:10px; display:block }}
.stats {{ display:flex; gap:44px; margin-top:16px; font-size:17px; color:{GREY} }} .stats span {{ display:block; font-size:44px; font-weight:700; color:{NAVY} }}
.moment {{ background:{ACCENT}22; border-left:6px solid {ACCENT}; padding:14px 22px; font-size:24px; line-height:1.35; border-radius:6px; margin-bottom:18px }}
.steps {{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-bottom:24px }}
.steps div {{ background:{PANEL}; border-radius:12px; padding:18px 22px }} .steps i {{ font-style:normal; display:inline-block; width:34px; height:34px; border-radius:17px; background:{NAVY}; color:#fff; text-align:center; line-height:34px; font-weight:700; margin-bottom:8px }}
.steps b {{ display:block; font-size:23px }} .steps span {{ font-size:19px; color:{GREY} }}
.ba {{ display:grid; grid-template-columns:1fr 1fr; gap:24px }} .ba img {{ width:100%; height:128px; object-fit:cover; border-radius:10px; display:block }}
figure {{ margin:0 }} figcaption {{ font-size:15px; color:{GREY}; margin-top:6px }}
.mosaic {{ display:grid; grid-template-columns:1fr 1fr; gap:14px }} .mosaic img {{ width:100%; height:190px; object-fit:cover; border-radius:10px; display:block }} .mosaic .wide {{ grid-column:1/3 }} .mosaic .wide img {{ height:230px }}
.url {{ font-size:22px; font-weight:700; color:{NAVY}; margin-top:18px; word-break:break-all }}
.funnel {{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-bottom:30px }}
.card {{ background:{PANEL}; border-radius:14px; padding:26px 28px }} .card em {{ display:block; font-style:normal; font-size:17px; color:{GREY}; margin-bottom:8px }} .card strong {{ display:block; font-size:62px; color:{NAVY}; line-height:1 }} .card span {{ display:block; font-size:19px; margin-top:12px }}
.card.hl {{ background:{NAVY}; color:#fff }} .card.hl em, .card.hl strong {{ color:#fff }}
.tbl {{ border-collapse:collapse; width:100%; font-size:23px }} .tbl th {{ text-align:left; font-size:16px; color:{GREY}; padding:0 0 10px; border-bottom:2px solid {INK} }} .tbl td {{ padding:16px 0; border-bottom:1px solid {LINE} }} .tbl td:first-child {{ font-weight:700; padding-right:18px }}
.team {{ display:grid; grid-template-columns:repeat(4,1fr); gap:24px }}
.person {{ background:{PANEL}; border-radius:14px; padding:34px 18px; text-align:center }} .person b {{ display:block; font-size:25px }} .person span {{ display:block; font-size:19px; color:{GREY}; margin-top:8px }}
.avatar {{ width:92px; height:92px; border-radius:46px; background:#fff; border:2px solid {LINE}; color:{NAVY}; font-size:42px; line-height:88px; margin:0 auto 18px; font-weight:700 }}
.kpis div {{ font-size:19px; color:{GREY}; margin-bottom:26px }} .kpis span {{ display:block; font-size:54px; font-weight:700; color:{NAVY}; line-height:1.1 }}
.chips {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:16px }} .chips span {{ background:{PANEL}; border:1px solid {LINE}; border-radius:20px; padding:7px 16px; font-size:17px }}
ul.b.s {{ font-size:25px }} ul.b.s li {{ margin-bottom:10px }}
.kv {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-top:6px }} .kv div {{ background:{PANEL}; border-radius:12px; padding:16px 22px }} .kv strong {{ display:block; font-size:38px; color:{NAVY} }} .kv span {{ font-size:17px; color:{GREY} }}
ul.l {{ list-style:none; padding:0 }} ul.l li {{ margin-bottom:18px }} ul.l b {{ display:block; font-size:27px }} ul.l span {{ font-size:20px; color:{GREY} }}
.persona {{ background:{PANEL}; border-left:5px solid {NAVY}; border-radius:6px; padding:14px 20px; font-size:19px; line-height:1.4; margin-top:8px }}
.three {{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px }} .three .panel {{ padding:22px 24px }} .three .panel ul.b {{ font-size:23px }} .three .panel ul.b li {{ margin-bottom:12px }}
.t2 {{ font-size:20px }} .t2 td, .t2 th {{ padding-right:14px }} .t2 td {{ padding-top:11px; padding-bottom:11px }}
.person .role {{ color:{NAVY}; font-weight:700; font-size:18px }} .person em {{ display:block; font-style:normal; font-size:16px; margin-top:12px; color:{INK}; background:#fff; border-radius:12px; padding:4px 10px; display:inline-block }}
.kpis.row {{ display:flex; gap:44px; margin-bottom:12px }} .kpis.row div {{ margin:0 }}
.stats {{ gap:30px }} .stats span {{ font-size:38px }}
.ask {{ background:{NAVY}; color:#fff; border-radius:16px; padding:46px 40px; font-size:78px; font-weight:700; line-height:1.05 }} .ask small {{ display:block; font-size:20px; font-weight:400; margin-top:18px; line-height:1.4 }}
"""

doc = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{NAME}</title><style>{CSS}</style></head><body>{''.join(s)}</body></html>"
out_html, out_pdf = ROOT / "dossier" / "deck.html", ROOT / "dossier" / "deck.pdf"
out_html.write_text(doc, encoding="utf-8")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", f"file://{out_html}"], check=True, capture_output=True, timeout=120)
print(out_pdf, out_pdf.stat().st_size // 1024, "KB")
