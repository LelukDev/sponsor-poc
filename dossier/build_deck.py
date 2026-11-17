"""Construit le deck de 10 slides (HTML puis PDF) à partir des chiffres du calculateur.

Usage : python dossier/build_deck.py
Entrées : dossier/calc.py (chiffres), dossier/deck_config.json (nom du produit, lien de la démo, équipe)
Sorties : dossier/deck.html et dossier/deck.pdf (via Chrome en mode sans fenêtre)
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
N = runpy.run_path(str(ROOT / "dossier" / "calc.py"))  # exécute le calculateur et réutilise ses variables
NAME = CFG["product_name"]
URL = CFG["demo_url"]

NAVY, YELLOW, INK, MUTED, PANEL, LINE = "#1F4E8C", "#F2B705", "#16243A", "#5B6678", "#F4F6FA", "#E3E7EE"


# ---------- Formats ----------
def eur(x, d=0):
    return ("-" if x < 0 else "") + f"€{abs(x):,.{d}f}"


def eur_k(x, d=1):
    return ("-" if x < 0 else "+" if x > 0 else "") + f"€{abs(x) / 1000:,.{d}f}k"


def pct(x, d=0):
    return f"{x * 100:.{d}f}%"


# ---------- Images ----------
def demo_logo() -> Image.Image:
    im = Image.new("RGBA", (760, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 30, 200, 210), fill=(217, 72, 15, 255))
    big = ImageFont.load_default(size=82)
    d.text((235, 40), "GARAGE", font=big, fill=(20, 40, 90, 255))
    d.text((235, 130), "MARTIN", font=big, fill=(217, 72, 15, 255))
    return scenes.prepare_logo(im)


def b64(img: Image.Image, w: int, q: int = 84) -> str:
    img = img.convert("RGB")
    img = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


logo = demo_logo()
img_empty = b64(scenes._plate("pitch_boards"), 700)
img_van = b64(scenes.render_scene("minibus", (0,), logo), 700)
boards_base = scenes.render_scene("pitch_boards", (0,), scenes.wordmark("Assurances Mercier"))
img_boards = b64(scenes.render_scene("pitch_boards", (1, 2, 3), logo, base=boards_base), 700)
kit_base = scenes.render_scene("kit_front", (0,), scenes.wordmark("Groupe Lacroix Immobilier"))
img_kit = b64(scenes.render_scene("jersey_back", (0,), logo), 700)
img_after = img_boards

# ---------- Chiffres ----------
I, P = N["I"], N["P"]
COST_TXT = f"${N['small_cost'] + 5e-6:.4f}"
months = list(range(0, 37))
cash, cum = [], 0.0
for t in months:
    if t > 0:
        n = N["som_clubs"] * t / 36
        cum += n * N["contrib"] - N["FIXED_MONTH"]
    cash.append(cum)
t_low = min(range(37), key=lambda t: cash[t])
be_month = N["be_month"]


def chart_svg() -> str:
    W, H, L, R, T, B = 600, 400, 70, 24, 24, 46
    ymin, ymax = -40000, 80000

    def X(t):
        return L + (W - L - R) * t / 36

    def Y(v):
        return T + (H - T - B) * (ymax - v) / (ymax - ymin)

    grid = "".join(
        f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W - R}" y2="{Y(v):.1f}" stroke="{LINE}" stroke-width="1"/>'
        f'<text x="{L - 10}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="13" fill="{MUTED}">{"-" if v < 0 else ""}€{abs(v) // 1000}k</text>'
        for v in range(ymin, ymax + 1, 20000)
    )
    xt = "".join(
        f'<text x="{X(t):.1f}" y="{H - 18}" text-anchor="middle" font-size="13" fill="{MUTED}">{t}</text>' for t in range(0, 37, 6)
    )
    pts = " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in zip(months, cash))
    zero = f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W - R}" y2="{Y(0):.1f}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 4"/>'
    low = (
        f'<circle cx="{X(t_low):.1f}" cy="{Y(cash[t_low]):.1f}" r="5" fill="{NAVY}" stroke="#fff" stroke-width="2"/>'
        f'<text x="{X(be_month) + 10:.1f}" y="{Y(cash[t_low]) + 30:.1f}" font-size="14" fill="{INK}">Low point {eur_k(cash[t_low])} (month {t_low})</text>'
    )
    be = (
        f'<line x1="{X(be_month):.1f}" y1="{T}" x2="{X(be_month):.1f}" y2="{H - B}" stroke="{YELLOW}" stroke-width="2"/>'
        f'<text x="{X(be_month) + 8:.1f}" y="{T + 14}" font-size="14" fill="{INK}">Monthly break-even · month {be_month}</text>'
    )
    end = (
        f'<circle cx="{X(36):.1f}" cy="{Y(cash[36]):.1f}" r="5" fill="{NAVY}" stroke="#fff" stroke-width="2"/>'
        f'<text x="{X(36) - 10:.1f}" y="{Y(cash[36]) - 12:.1f}" text-anchor="end" font-size="14" fill="{INK}">{eur_k(cash[36])} · month 36</text>'
    )
    return (
        f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Cumulative cash over 36 months">'
        f"{grid}{xt}{zero}{be}"
        f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        f'{low}{end}<text x="{(L + W - R) / 2:.0f}" y="{H - 2}" text-anchor="middle" font-size="13" fill="{MUTED}">Months after launch</text></svg>'
    )


# ---------- Contenu ----------
def foot(n, source=""):
    return f'<div class="foot"><span>{html.escape(source)}</span><span>{NAME} · Monetizing Data &amp; AI · {n}/10</span></div>'


def slide(n, kicker, title, body, source=""):
    return (
        f'<section class="slide"><div class="kicker">{n} · {kicker}</div><h1>{title}</h1>{body}{foot(n, source)}</section>'
    )


s = []

# 1 Problem
s.append(
    slide(
        1,
        "Problem",
        "Amateur clubs have space to sell and no time to sell it",
        f"""<div class="cols" style="grid-template-columns:1.1fr 1fr;gap:40px">
<div>
<p class="lead">Julien is the volunteer treasurer of a 320-member football club. Local sponsors bring about <b>9%</b> of a budget of roughly <b>€80,000</b>. He writes each pitch alone, in the evening.</p>
<ul class="pains">
<li><b>Generic pitches.</b> The same template goes to a bakery and a garage.</li>
<li><b>Offers that cannot be sold.</b> The jersey chest is already taken; a competitor of a current sponsor gets the same email.</li>
<li><b>No link to what the club needs.</b> The minibus must be replaced, but nobody asks the garage.</li>
</ul>
<p class="note">Julien is an illustrative persona. The three pains are hypotheses we will test with 10 club calls.</p>
</div>
<div><img class="photo" src="{img_empty}" alt="Empty advertising boards"><p class="cap">Empty boards: unsold inventory</p>
<div class="stats"><div><span class="n">37%</span>of clubs run a deficit</div><div><span class="n">63%</span>have under €10k budget</div></div></div>
</div>""",
        "Sources: CNOSF study on club financing (budgets, deficit); partnerships 9% of resources. Older data, orders of magnitude.",
    )
)

# 2 Solution
s.append(
    slide(
        2,
        "Solution",
        "Type a business name, get an offer that fits the club, with the logo already on the kit",
        f"""<p class="lead" style="max-width:1100px">For volunteer-run clubs that need local sponsors, <b>{NAME}</b> is an AI sponsorship assistant that turns any business name into a ready-to-send offer in seconds. Unlike proposal templates, it offers only slots that are actually free, avoids conflicts with current sponsors and ties each offer to the club's needs.</p>
<div class="steps">
<div class="step"><span class="num">1</span><b>The club describes itself</b><p>Slots, prices, current sponsors and their sector, needs for the season.</p></div>
<div class="step"><span class="num">2</span><b>AI chooses, code verifies</b><p>The model picks free slots and writes the mail. Code checks availability, price and sector conflicts.</p></div>
<div class="step"><span class="num">3</span><b>Photo-realistic mock-ups</b><p>The business logo is placed on the kit, boards, minibus and banners in perspective.</p></div>
</div>
<div class="ba"><figure><img src="{img_empty}"><figcaption>Before: an unsold board</figcaption></figure><figure><img src="{img_after}"><figcaption>After: the sponsor's logo, in perspective</figcaption></figure>
<div class="moment"><b>Moment of truth:</b> a business name goes in, a personalised offer with its logo on the minibus and the boards comes out.</div></div>""",
        "",
    )
)

# 3 Live demo
demo_line = f"Live: {URL}" if URL else "Live link: added at submission"
s.append(
    slide(
        3,
        "Live demo",
        "The jury picks the business and the logo, the offer adapts on the spot",
        f"""<div class="plan">
<div><b>1</b> Jury names a local business: offer in seconds</div>
<div><b>2</b> Jury uploads any logo: it appears on the kit, boards and minibus</div>
<div><b>3</b> Jury frees or takes a slot, or names a competitor of a sponsor: the offer changes</div>
<div><b>4</b> Wine bar: blocked before any AI call</div>
</div>
<div class="three">
<figure><img src="{img_van}"><figcaption>Minibus · €800 per season</figcaption></figure>
<figure><img src="{img_boards}"><figcaption>Boards · the main one is already sold</figcaption></figure>
<figure><img src="{img_kit}"><figcaption>Jersey back · €700 per season</figcaption></figure>
</div>
<div class="url">{html.escape(demo_line)}</div>
<p class="note">Measured on the PoC: about {COST_TXT} and 4 to 5 seconds per offer. The logo shown is an example.</p>""",
        "",
    )
)

# 4 Market
s.append(
    slide(
        4,
        "Market analysis",
        f"Bottom-up: {N['n_inter'] + N['n_phare']:,} clubs can pay; we start with {N['sam_clubs']:,}",
        f"""<div class="funnel">
<div class="card"><div class="lab">TAM · France</div><div class="big">{eur(N['TAM'] / 1e6, 1)}M</div><p>{N['n_inter']:,} mid-size + {N['n_phare']:,} flagship clubs × {eur(N['arpa']['intermediaire'])} / {eur(N['arpa']['phare'])} a year</p></div>
<div class="arrow">→</div>
<div class="card"><div class="lab">SAM · football + rugby</div><div class="big">{eur(N['SAM'] / 1e6, 2)}M</div><p>{N['sam_inter']:,} + {N['sam_phare']:,} = {N['sam_clubs']:,} clubs in the networks we can reach today</p></div>
<div class="arrow">→</div>
<div class="card hl"><div class="lab">SOM · 3 years</div><div class="big">{eur(N['SOM'])}</div><p>{N['som_clubs']} clubs ({N['som_clubs'] / N['sam_clubs']:.1%} of SAM) · annual recurring revenue</p></div>
</div>
<div class="formula">Customers who sign × price per club = market. Every figure is an assumption we can be challenged on.</div>
<p class="lead" style="margin-top:22px"><b>Check:</b> {N['som_clubs']} clubs in 36 months is <b>{N['som_per_month']:.0f} new clubs a month</b>. Who signs them? District and league partnerships that relay the tool, plus direct calls.</p>
<p class="note">We exclude the 66% of small neighbourhood clubs: their sponsoring (about €1,060 a year) leaves under €100 of net gain, so they cannot pay. Total club count is a weak source (about 165,000, 2020).</p>""",
        "Sources: CNOSF club typology (31% mid-size, 3% flagship); FFF about 12,000 clubs; FFR over 1,900 clubs. Prices are our assumptions.",
    )
)

SENS = "".join(
    f"<tr><td>{a:.0%}</td><td>{eur(I['full'] * a * N['NET_RATIO'])} a year</td><td>{pct(N['PRICE_MONTH']['intermediaire'] / (I['full'] * a * N['NET_RATIO'] / 12))}</td></tr>"
    for a in (0.30, 0.40, 0.50, 0.60)
)

# 5 Business model
s.append(
    slide(
        5,
        "Business model and price",
        f"€15 a month is {pct(I['capture'])} of the value we create for a mid-size club",
        f"""<div class="two">
<div class="card"><div class="lab">Club plan · mid-size club</div><div class="big">€{N['PRICE_MONTH']['intermediaire']}<small>/month</small></div>
<p>Value created: <b>{eur(I['y1_month'])}</b> a month ({eur(I['y1'])} net in year 1)<br>Cost to serve: €{N['COST_SERVE_MONTH']['intermediaire']} · margin <b>{pct(I['margin'])}</b></p></div>
<div class="card"><div class="lab">Club+ plan · flagship club</div><div class="big">€{N['PRICE_MONTH']['phare']}<small>/month</small></div>
<p>Value created: <b>{eur(P['y1_month'])}</b> a month ({eur(P['y1'])} net in year 1)<br>Cost to serve: €{N['COST_SERVE_MONTH']['phare']} · margin <b>{pct(P['margin'])}</b></p></div>
</div>
<p class="lead" style="margin-top:22px"><b>Model:</b> SaaS subscription per club, priced on value (10 to 30% of the gain), below the €19 to €49 a month clubs already pay for management software. Archetype for the club: <b>revenue uplift</b> from signing more local sponsors.</p>
<table class="tbl small" style="margin-top:10px;max-width:760px"><tr><th>Year-1 adoption</th><th>Net gain, mid-size club</th><th>€15 a month as share of value</th></tr>{SENS}</table>
<p class="note">Value = sponsoring today (9% of budget) × {pct(N['UPLIFT'])} possible uplift × {pct(N['ADOPTION'])} year-1 adoption × {pct(N['NET_RATIO'])} net. Uplift is our main unproven assumption: pilots will measure it. The €300 to €1,500 slot prices are what the club charges its sponsors.</p>""",
        "",
    )
)

# 6 Traction
s.append(
    slide(
        6,
        "Traction",
        "No paying club yet: here is what is proven today and what we will prove in 30 days",
        f"""<div class="cols" style="grid-template-columns:1fr 1fr;gap:32px">
<div class="panel"><h3>Proven today</h3>
<ul>
<li>A working PoC online, on any business the jury names</li>
<li>Measured cost: about {COST_TXT} per offer, 4 to 5 seconds</li>
<li>Offers never use a taken slot (checked by code, tested)</li>
<li>Sector conflict with a current sponsor is flagged</li>
<li>Alcohol, tobacco and gambling blocked before any AI call</li>
<li>25 automated tests, all passing</li>
</ul></div>
<div class="panel"><h3>To prove in the next 30 days</h3>
<ul>
<li>10 calls to mid-size clubs: do they recognise the three pains, would they pay €15?</li>
<li>3 pilot clubs for one season, sponsoring measured before and after</li>
<li>2 conversations with district or league contacts</li>
<li><b>Success:</b> at least +15% sponsoring, or 2 new sponsors per pilot club</li>
</ul></div>
</div>
<div class="moment" style="margin-top:14px">We prefer to show an honest plan than invented customers.</div>""",
        "",
    )
)

# 7 Competition
rows = [
    ("All Sponsored", "Scans clubs' social networks to measure brand visibility and broker sponsoring", "No offer personalised per business, no photo mock-up of the club's own kit"),
    ("Leedeel", "Platform connecting brands with athletes, clubs and federations", "A marketplace; does not prepare the club's offer for each local lead"),
    ("Spencer.club", "Intermediary for introductions, contracts and structuring", "Human service, not an instant tool"),
    ("SPONSO+", "Participatory sponsoring by many small contributors", "Different model: not packages for local businesses"),
    ("Proposal and deck tools", "Templates, AI-assisted proposals, e-signature (Storydoc, Playbook, SignNow)", "Generic: no club inventory, no sector rule, no mock-ups"),
]
trs = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
s.append(
    slide(
        7,
        "Competition and defensibility",
        "Competitors write proposals or broker deals; we show the sponsor his logo on the club's real kit",
        f"""<div class="cols" style="grid-template-columns:1.5fr 1fr;gap:28px">
<table class="tbl"><tr><th>Player</th><th>What it does</th><th>Gap we address</th></tr>{trs}</table>
<div><div class="panel"><h3>What clubs hire today</h3><p>A volunteer's own pitch, free templates, or nothing. This is our real competition.</p></div>
<div class="panel" style="margin-top:14px"><h3>Moats</h3><ul>
<li><b>Data:</b> which offers close, by sector and price</li>
<li><b>Distribution:</b> districts and leagues</li>
<li><b>Workflow:</b> inventory, sponsor history, renewals</li></ul></div></div>
</div>
<p class="note">Biggest threat: a prompt and a UI can be rebuilt in a weekend (barriers to entry are low). Our answer is the three moats above, not the model. Competitor descriptions come from their own pages and press, not tested.</p>""",
        "Sources: press and vendor pages, 2026.",
    )
)

# 8 Team
names = CFG["team"]
cards = "".join(
    f'<div class="person"><div class="avatar">{(m["name"] or "?")[0]}</div><b>{html.escape(m["name"]) if m["name"] else "Name to add"}</b><p>{html.escape(m["role"])}</p></div>'
    for m in names
).replace("AI and product build</p>", "AI and product build</p><p class='task'>PoC, prompts, tests</p>").replace("Clubs and partnerships</p>", "Clubs and partnerships</p><p class='task'>Club calls, districts, pilots</p>").replace("Finance and pricing</p>", "Finance and pricing</p><p class='task'>Market, price, cash plan</p>").replace("Design and communication</p>", "Design and communication</p><p class='task'>Deck, visuals, rehearsal</p>")
s.append(
    slide(
        8,
        "Team",
        "Four people cover the build, the clubs, the numbers and the story",
        f"""<div class="team">{cards}</div>
<p class="lead" style="margin-top:30px">Everyone speaks in the defence and can explain every figure. What we still need: one district or league partner who opens the door to clubs.</p>""",
        "",
    )
)

# 9 Financials
months_rows = [12, 24, 36]
tb = "".join(
    f"<tr><td>{m}</td><td>{N['som_clubs'] * m / 36:.0f}</td><td>{eur(N['som_clubs'] * m / 36 * N['blend_price'])}</td><td>{eur(cash[m])}</td></tr>"
    for m in months_rows
)
s.append(
    slide(
        9,
        "Financials",
        f"Break-even at {N['breakeven_clubs']} clubs in month {be_month}, with a cash low point of {eur(-N['trough'])}",
        f"""<div class="cols" style="grid-template-columns:600px 1fr;gap:30px">
<div><div class="lab">Cumulative cash, € thousands</div>{chart_svg()}</div>
<div>
<div class="kpis"><div><span class="n">{pct(N['contrib'] / N['blend_price'])}</span>gross margin</div><div><span class="n">{N['breakeven_clubs']}</span>clubs to break even</div><div><span class="n">${N['ai_small']:.0f}</span>AI cost a month at {N['som_clubs']} clubs</div></div>
<table class="tbl small"><tr><th>Month</th><th>Clubs</th><th>Monthly revenue</th><th>Cumulative cash</th></tr>{tb}</table>
<p class="note">Fixed costs {eur(N['FIXED_MONTH'])} a month; linear ramp to {N['som_clubs']} clubs. Revenue at month 36: {eur(N['mrr_full'])} a month ({eur(N['SOM'])} a year).</p></div>
</div>""",
        "All figures from the numbers dossier; assumptions are tagged [H] there.",
    )
)

# 10 The ask
s.append(
    slide(
        10,
        "The ask",
        f"We ask for {eur(N['ask'])} to run 18 months and reach {N['breakeven_clubs']} paying clubs",
        f"""<div class="cols" style="grid-template-columns:1fr 1.2fr;gap:36px">
<div class="card hl" style="padding:32px 30px"><div class="lab">The ask</div><div class="big" style="font-size:78px">{eur(N['ask'])}</div><p>18 months · covers the cash low point ({eur(-N['trough'])}) plus a 6-month buffer of fixed costs ({eur(6 * N['FIXED_MONTH'])}), rounded up</p></div>
<div><h3>Milestones within 18 months</h3>
<ul class="pains" style="font-size:25px">
<li><b>3 pilot clubs</b> with sponsoring measured before and after</li>
<li><b>At least 1 district or league agreement</b> that relays the tool</li>
<li><b>{N['breakeven_clubs']} paying clubs</b>, the monthly break-even point</li></ul>
<h3 style="margin-top:20px">What we also ask for</h3>
<p style="font-size:22px;line-height:1.4">Introductions to two district or league contacts, and the jury's feedback on the pricing assumption.</p></div>
</div>""",
        "",
    )
)

CSS = f"""
@page {{ size: 1280px 720px; margin: 0 }}
* {{ box-sizing: border-box }}
body {{ margin:0; font-family:"Helvetica Neue",Helvetica,Arial,sans-serif; color:{INK} }}
.slide {{ width:1280px; height:720px; position:relative; padding:52px 72px 56px; page-break-after:always; overflow:hidden; background:#fff }}
.slide:after {{ content:""; position:absolute; left:0; top:0; width:14px; height:100%; background:{NAVY} }}
.kicker {{ font-size:16px; letter-spacing:.08em; text-transform:uppercase; color:{NAVY}; font-weight:700 }}
h1 {{ font-size:38px; line-height:1.16; margin:10px 0 22px; max-width:1120px }}
h3 {{ font-size:22px; margin:0 0 10px; color:{NAVY} }}
.lead {{ font-size:24px; line-height:1.4; margin:0 0 16px }}
.note {{ font-size:15px; color:{MUTED}; line-height:1.4; margin-top:12px }}
.cap {{ font-size:14px; color:{MUTED}; margin:6px 0 0 }}
.foot {{ position:absolute; left:72px; right:72px; bottom:22px; font-size:12px; color:{MUTED}; display:flex; justify-content:space-between }}
.cols {{ display:grid }}
.photo {{ width:100%; border-radius:10px; display:block }}
.pains {{ font-size:21px; line-height:1.38; padding-left:22px; margin:8px 0 }}
.pains li {{ margin-bottom:10px }}
.stats {{ display:flex; gap:20px; margin-top:12px; font-size:15px; color:{MUTED} }}
.stats .n {{ display:block; font-size:34px; font-weight:700; color:{NAVY} }}
.steps {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin:16px 0 }}
.step {{ background:{PANEL}; border-radius:12px; padding:18px 20px; font-size:20px }}
.step p {{ font-size:17px; color:{MUTED}; margin:8px 0 0; line-height:1.35 }}
.num {{ display:inline-block; width:30px; height:30px; border-radius:15px; background:{NAVY}; color:#fff; text-align:center; line-height:30px; margin-right:10px; font-weight:700 }}
.moment {{ background:{YELLOW}22; border-left:6px solid {YELLOW}; padding:14px 20px; font-size:21px; border-radius:6px }}
.plan {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; font-size:16px; margin-bottom:14px }}
.plan div {{ background:{PANEL}; border-radius:10px; padding:10px 14px; line-height:1.3 }}
.plan b {{ color:{NAVY}; margin-right:4px }}
.three {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px }}
figure {{ margin:0 }} figure img {{ width:100%; border-radius:8px; display:block }}
figcaption {{ font-size:15px; color:{MUTED}; margin-top:6px }}
.url {{ margin-top:12px; font-size:22px; font-weight:700; color:{NAVY} }}
.funnel {{ display:grid; grid-template-columns:1fr 30px 1fr 30px 1fr; align-items:center; gap:6px }}
.arrow {{ font-size:30px; color:{MUTED}; text-align:center }}
.card {{ background:{PANEL}; border-radius:14px; padding:20px 22px }}
.card.hl {{ background:{NAVY}; color:#fff }} .card.hl .lab, .card.hl .big {{ color:#fff }}
.card p {{ font-size:17px; line-height:1.4; margin:8px 0 0 }}
.lab {{ font-size:15px; text-transform:uppercase; letter-spacing:.06em; color:{MUTED}; font-weight:700 }}
.big {{ font-size:48px; font-weight:700; color:{NAVY}; margin-top:6px }} .big small {{ font-size:22px; font-weight:400 }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:24px }}
.panel {{ background:{PANEL}; border-radius:12px; padding:18px 22px }}
.panel ul {{ margin:0; padding-left:20px; font-size:19px; line-height:1.42 }} .panel li {{ margin-bottom:8px }} .panel p {{ font-size:19px; margin:0; line-height:1.4 }}
.tbl {{ border-collapse:collapse; width:100%; font-size:16px }}
.tbl th {{ text-align:left; background:{NAVY}; color:#fff; padding:8px 10px; font-size:15px }}
.tbl td {{ padding:9px 10px; border-bottom:1px solid {LINE}; vertical-align:top; line-height:1.3 }}
.tbl.small td, .tbl.small th {{ font-size:15px; padding:7px 8px }}
.team {{ display:grid; grid-template-columns:repeat(4,1fr); gap:20px }}
.person {{ background:{PANEL}; border-radius:14px; padding:40px 20px; text-align:center; font-size:21px }}
.person p {{ color:{MUTED}; font-size:17px; margin:6px 0 0 }}
.avatar {{ width:84px; height:84px; border-radius:42px; background:{NAVY}22; color:{NAVY}; font-size:40px; line-height:84px; margin:0 auto 14px; font-weight:700 }}
.formula {{ background:{PANEL}; border-radius:10px; padding:12px 18px; font-size:20px; margin-top:20px; color:{INK} }}
.ba {{ display:grid; grid-template-columns:1fr 1fr 1.25fr; gap:16px; align-items:center }}
.ba img {{ height:150px; object-fit:cover; width:100% }}
.task {{ font-size:16px !important; color:{INK} !important; margin-top:10px !important }}
.kpis {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; font-size:14px; color:{MUTED}; margin-bottom:14px }}
.kpis .n {{ display:block; font-size:32px; font-weight:700; color:{NAVY} }}
"""

doc = f"<!doctype html><html><head><meta charset='utf-8'><title>{NAME} deck</title><style>{CSS}</style></head><body>{''.join(s)}</body></html>"
out_html = ROOT / "dossier" / "deck.html"
out_pdf = ROOT / "dossier" / "deck.pdf"
out_html.write_text(doc, encoding="utf-8")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run(
    [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", f"file://{out_html}"],
    check=True,
    capture_output=True,
    timeout=120,
)
print(out_pdf, out_pdf.stat().st_size // 1024, "Ko")
