"""Build the project report (HTML, then A4 PDF) in plain English from the numbers calculator.

Run: python dossier/build_report.py
Layout: justified text, 1.5 line spacing, 22 mm margins, numbered captions, page numbers.
This report is a support document. The brief only asks for the deck and the live link.
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
INK, NAVY, GREY, LINE, ACCENT = "#1B2430", "#1F4E8C", "#6B7280", "#D9DDE4", "#F2B705"
I, P = N["I"], N["P"]
COST = f"{N['small_cost'] + 5e-6:.4f}"


def eur(x, d=0):
    return ("-" if x < 0 else "") + f"€{abs(x):,.{d}f}"


def num(x, d=0):
    return f"{x:,.{d}f}"


def demo_logo() -> Image.Image:
    im = Image.new("RGBA", (760, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 30, 200, 210), fill=(217, 72, 15, 255))
    big = ImageFont.load_default(size=82)
    d.text((235, 40), "GARAGE", font=big, fill=(20, 40, 90, 255))
    d.text((235, 130), "MARTIN", font=big, fill=(217, 72, 15, 255))
    return scenes.prepare_logo(im)


def b64(img: Image.Image, w: int = 1000, q: int = 86) -> str:
    img = img.convert("RGB")
    img = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


logo = demo_logo()
img_empty = b64(scenes._plate("pitch_boards"))
img_van = b64(scenes.render_scene("minibus", (0,), logo))
base = scenes.render_scene("pitch_boards", (0,), scenes.wordmark("Mercier Insurance"))
img_boards = b64(scenes.render_scene("pitch_boards", (1, 2, 3), logo, base=base))
img_back = b64(scenes.render_scene("jersey_back", (0,), logo))

cash, cum = [], 0.0
for t in range(37):
    if t > 0:
        cum += N["som_clubs"] * t / 36 * N["contrib"] - N["FIXED_MONTH"]
    cash.append(cum)
t_low = min(range(37), key=lambda t: cash[t])
be = N["be_month"]


def fig_cash() -> str:
    W, H, L, R, T, B = 600, 300, 64, 20, 18, 40
    ymin, ymax = -40000, 80000
    X = lambda t: L + (W - L - R) * t / 36  # noqa: E731
    Y = lambda v: T + (H - T - B) * (ymax - v) / (ymax - ymin)  # noqa: E731
    grid = "".join(
        f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W - R}" y2="{Y(v):.1f}" stroke="{LINE}"/>'
        f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="12" fill="{GREY}">{"-" if v < 0 else ""}€{abs(v) // 1000}k</text>'
        for v in range(ymin, ymax + 1, 40000)
    )
    xt = "".join(f'<text x="{X(t):.1f}" y="{H - 18}" text-anchor="middle" font-size="12" fill="{GREY}">{t}</text>' for t in range(0, 37, 6))
    pts = " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in zip(range(37), cash))
    return (
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Cash over 36 months">{grid}{xt}'
        f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W - R}" y2="{Y(0):.1f}" stroke="{GREY}" stroke-dasharray="4 3"/>'
        f'<line x1="{X(be):.1f}" y1="{T}" x2="{X(be):.1f}" y2="{H - B}" stroke="{ACCENT}" stroke-width="2.5"/>'
        f'<text x="{X(be) + 8:.1f}" y="{T + 12}" font-size="13" fill="{INK}">Break-even, month {be}</text>'
        f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="2.8" stroke-linejoin="round"/>'
        f'<circle cx="{X(t_low):.1f}" cy="{Y(cash[t_low]):.1f}" r="4" fill="{NAVY}"/>'
        f'<text x="{X(be) + 10:.1f}" y="{Y(cash[t_low]) + 26:.1f}" font-size="13" fill="{INK}">Lowest cash {eur(cash[t_low])}</text>'
        f'<circle cx="{X(36):.1f}" cy="{Y(cash[36]):.1f}" r="4" fill="{NAVY}"/>'
        f'<text x="{X(36) - 8:.1f}" y="{Y(cash[36]) + 5:.1f}" text-anchor="end" font-size="13" fill="{INK}">{eur(cash[36])}</text>'
        f'<text x="{(L + W - R) / 2:.0f}" y="{H - 2}" text-anchor="middle" font-size="12" fill="{GREY}">Months after launch</text></svg>'
    )


def fig_stack() -> str:
    rows = [
        ("7", "Watching", "cost and time of each offer", "Buy", "#E7EAF0"),
        ("6", "Distribution", "district and league partners", "Partner", "#FBEBB5"),
        ("5", "App", "club profile, offer page, photos", "Build", "#C9D6EA"),
        ("4", "Workflow", "fixed steps, one AI call", "Build", "#C9D6EA"),
        ("3", "AI model", "small model first, large as backup", "Buy", "#E7EAF0"),
        ("2", "Storage", "club profiles, offers, results", "Buy", "#E7EAF0"),
        ("1", "Data sources", "club slots, public business lists", "Partner", "#FBEBB5"),
    ]
    out = []
    for i, (n, lab, desc, tag, col) in enumerate(rows):
        y = 6 + i * 40
        out.append(
            f'<rect x="0" y="{y}" width="600" height="34" rx="4" fill="{col}"/>'
            f'<text x="12" y="{y + 22}" font-size="13" font-weight="700" fill="{INK}">{n}  {lab}</text>'
            f'<text x="170" y="{y + 22}" font-size="13" fill="{INK}">{desc}</text>'
            f'<text x="588" y="{y + 22}" text-anchor="end" font-size="13" font-weight="700" fill="{INK}">{tag}</text>'
        )
    return f'<svg viewBox="0 0 600 290" role="img" aria-label="Seven layers of the product">{"".join(out)}</svg>'


def fig_bars() -> str:
    rows = [("Value created", I["y1_month"], "#B9C9E2"), ("Our price", N["PRICE_MONTH"]["mid"], NAVY), ("Cost to serve", N["COST_SERVE_MONTH"]["mid"], "#9AA3AF")]
    out = []
    for i, (lab, v, col) in enumerate(rows):
        y = 8 + i * 50
        w = max(6, 330 * v / I["y1_month"])
        out.append(f'<text x="0" y="{y + 24}" font-size="14" fill="{INK}">{lab}</text><rect x="120" y="{y}" width="{w:.0f}" height="32" rx="3" fill="{col}"/><text x="{120 + w + 10:.0f}" y="{y + 22}" font-size="15" font-weight="700" fill="{INK}">{eur(v)}</text>')
    return f'<svg viewBox="0 0 600 170" role="img" aria-label="Value, price and cost per month">{"".join(out)}</svg>'


def table(head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{body}</table>"


fig_n, tab_n = {"n": 0}, {"n": 0}


def figure(content, caption, cls=""):
    fig_n["n"] += 1
    return f'<figure class="{cls}">{content}<figcaption>Figure {fig_n["n"]}. {caption}</figcaption></figure>'


def captioned_table(caption, head, rows):
    tab_n["n"] += 1
    return f'<div class="tab"><div class="tcap">Table {tab_n["n"]}. {caption}</div>{table(head, rows)}</div>'


demo = f"The live demo is at {html.escape(URL)}." if URL else "The link to the live demo is in the submission email."
secs = []

secs.append(f"""
<h1>1. Summary</h1>
<p>Amateur sports clubs need local sponsors. The volunteers who write the offers have little time, and they often offer slots that are already sold. {NAME} is an AI assistant that turns the name of a local business into an offer that is ready to send. It offers only the slots that are free. It avoids a business that competes with a current sponsor. It links the offer to what the club needs. It shows the logo of the business on realistic photos of the club's kit, boards and minibus.</p>
<p>We aim at mid-size and big clubs. There are about {num(N['n_mid'] + N['n_flag'])} of them in France. The price is €{N['PRICE_MONTH']['mid']} a month for a mid-size club and €{N['PRICE_MONTH']['flagship']} a month for a big club. This is about {I['capture'] * 100:.0f}% and {P['capture'] * 100:.0f}% of the value we create for them. After three years, with {N['som_clubs']} clubs, the yearly revenue is {eur(N['SOM'])}. We break even at {N['breakeven_clubs']} clubs, in month {be}. We ask for {eur(N['ask'])} to run for 18 months.</p>
<p>The prototype works and we measured it. An offer costs about ${COST} and takes four to five seconds to write. We have no paying client yet. Our weakest assumption is how much the tool raises sponsoring. Pilots with three clubs will measure it. {demo}</p>
""")

secs.append(f"""
<h1>2. The problem</h1>
<p>Sponsoring is a small but useful part of a club's money. A study by the French Olympic Committee says partnerships bring about {N['SPONSOR_SHARE'] * 100:.0f}% of the resources of sports clubs. It also says that up to 37% of clubs lose money, depending on the type of club. Budgets are very different. 63% of clubs have less than €10,000. An average mid-size club has {eur(N['BUDGET']['mid'])}. An average big club has {eur(N['BUDGET']['flagship'])}.</p>
<p>Our example person is Julien, a volunteer treasurer of a football club with 320 members. He writes every sponsor pitch alone, in the evening. We think there are three problems. The pitches are all the same, so a bakery and a garage get the same text. The offers include slots that are already sold, or a business that competes with a current sponsor. Nothing links the offer to what the club needs this season. These three problems are our own guesses. We have not yet checked them with clubs. The first step of our plan is to call ten mid-size clubs.</p>
{figure(f'<div class="pair"><img src="{img_empty}"><img src="{img_boards}"></div>', "Left: unsold advertising boards. Right: the same boards with a sponsor's logo placed by the tool. The logo is an example.")}
""")

secs.append(f"""
<h1>3. The solution</h1>
<p>Our moment of truth is simple. A business name goes in, and an offer with its logo already on the club's equipment comes out. The jury can type any business and upload any logo.</p>
<p>The tool has five steps. First, the club lists ten slots. Each slot has a price, a status (free or taken), the current sponsor and its sector. The club also gives its needs and its fundraising goal. Second, a guardrail stops alcohol, tobacco and gambling businesses before any call to the AI. Third, the AI model picks three offers among the free slots and writes the email. Fourth, the code checks the result. A taken slot is removed. Prices come from the club's list. A business in the same sector as a current sponsor is flagged for a person to check. Fifth, the logo is placed on photos, with the right angle and light.</p>
<p>The tool adapts to each case. A garage gets the minibus and the entrance banner, and the offer is linked to the club's need to replace the minibus. A sports shop gets the training bibs and the boards. An estate agency triggers a warning, because a real estate company already sponsors the club. A business whose activity is not clear from its name, such as "Chez Momo", is sent to a person.</p>
{figure(f'<div class="trio"><img src="{img_van}"><img src="{img_boards}"><img src="{img_back}"></div>', "Photos made by the tool for an example business: the minibus, the pitch boards and the back of the jersey. Current sponsors stay visible.")}
""")

secs.append(f"""
<h1>4. How it is built</h1>
<p>We use the seven layers of the course. The rule is simple: buy the AI model, build what makes us different, buy the common tools, and work with partners where they own the access. Figure 3 shows the choice for each layer.</p>
<p>The prototype covers layers 3 to 5 and a light version of layer 7. Storage, distribution and public business lists are for later. We chose the simplest shape: a fixed workflow with one AI call. It is cheaper, faster and easier to test than an agent that loops.</p>
<p>The photos are made once with an image model. Seven scenes cost $0.47 in total. After that, the logo is placed by code, so the images are free and instant. This also makes the demo reliable in front of a jury.</p>
<p>On the prototype, one offer uses about {N['TOK_IN']} input tokens and {N['TOK_OUT']} output tokens with the small model, which costs about ${COST}. The writing takes 3.5 to 4.5 seconds, and the whole offer shows in four to eight seconds. This is slower than the three-second target of the course. Showing the text as it is written is the first thing we would improve.</p>
{figure(fig_stack(), "The seven layers of the product, and the choice for each: build, buy or partner.", "narrow")}
""")

secs.append(f"""
<h1>5. Market</h1>
<p>We size the market from the bottom up. We count the clubs that sign, and we multiply by the price for one club. The club, through its treasurer or president, is the customer. We leave out small neighbourhood clubs. They are 66% of all clubs, but their sponsoring is only about €1,060 a year. That leaves under €100 of net gain, which is too little to pay for a tool.</p>
{captioned_table(f"Market size, with yearly prices of €{num(N['arpa']['mid'])} for a mid-size club and €{num(N['arpa']['flagship'])} for a big club.", ["Level", "Clubs", "Yearly value"], [
    ["Total market in France", f"{num(N['n_mid'])} mid-size, {num(N['n_flag'])} big ({num(N['n_mid'] + N['n_flag'])} in total)", f"{eur(N['TAM'] / 1e6, 1)}M"],
    ["Market we can reach (football and rugby)", f"{num(N['sam_mid'])} mid-size, {num(N['sam_flag'])} big ({num(N['sam_clubs'])} in total)", f"{eur(N['SAM'] / 1e6, 2)}M"],
    ["Our target in three years", f"{N['SOM_CLUBS']['mid']} mid-size, {N['SOM_CLUBS']['flagship']} big", eur(N['SOM'])],
])}
<p>The target of {N['som_clubs']} clubs in 36 months means {N['som_per_month']:.0f} new clubs a month, or {N['som_clubs'] / N['sam_clubs'] * 100:.1f}% of the clubs we can reach. We expect most of them to come from districts and leagues that pass the tool to their clubs, plus some direct calls. We have no agreement yet.</p>
<p>Our sources are not perfect. The split of clubs by size comes from a study that reuses data from 2011 and 2012. The total number of clubs in France, about {num(165000)}, comes from a weak source dated 2020. The counts for football (about 12,000) and rugby (more than 1,900) come from the federations. These numbers give the right size, but they should be checked with the Ministry of Sports.</p>
""")

sens_rows = [[f"{a * 100:.0f}%", eur(I['full'] * a * N['NET_RATIO']), f"{N['PRICE_MONTH']['mid'] / (I['full'] * a * N['NET_RATIO'] / 12) * 100:.0f}%"] for a in (0.30, 0.40, 0.50, 0.60)]
secs.append(f"""
<h1>6. Business model and price</h1>
<p>Our model is a software subscription for each club, with two plans by club size. For the club, the gain is more sponsoring: the tool helps it send better offers and sign more local sponsors. We count the net gain, after the cost of signs and kit. The course says a price should take 10 to 30% of the value created. A price based on our costs would leave most of the value unused.</p>
{captioned_table("The two plans and the value they create in year 1.", ["", "Mid-size club", "Big club"], [
    ["Sponsoring today (9% of the budget)", eur(I['base']), eur(P['base'])],
    ["Possible rise at full use (30%)", eur(I['full']), eur(P['full'])],
    ["Net gain in year 1 (40% use, 90% net)", eur(I['y1']), eur(P['y1'])],
    ["Value per month", eur(I['y1_month'], 1), eur(P['y1_month'], 1)],
    ["Price per month", f"€{N['PRICE_MONTH']['mid']}", f"€{N['PRICE_MONTH']['flagship']}"],
    ["Share of the value we take", f"{I['capture'] * 100:.0f}%", f"{P['capture'] * 100:.0f}%"],
    ["Cost to serve per month", f"€{N['COST_SERVE_MONTH']['mid']}", f"€{N['COST_SERVE_MONTH']['flagship']}"],
    ["Gross margin", f"{I['margin'] * 100:.0f}%", f"{P['margin'] * 100:.0f}%"],
])}
{figure(fig_bars(), "Value created, price and cost to serve per month for a mid-size club.", "narrow")}
<p>The price of €{N['PRICE_MONTH']['mid']} is lower than the €19 to €49 a month that clubs already pay for management software. So the tool is a small add-on, not a replacement. Please do not mix two prices. The €300 to €1,500 a season in the demo is what the club charges its sponsors. The €{N['PRICE_MONTH']['mid']} and €{N['PRICE_MONTH']['flagship']} a month are what we charge the club.</p>
{captioned_table("What happens to the mid-size plan if clubs use the tool less or more.", ["Use in year 1", "Net gain per year", "Our price as a share of value"], sens_rows)}
""")

secs.append("""
<h1>7. Competition and defensibility</h1>
<p>We found several players around sports sponsoring in France. As far as we can tell from their websites and from press articles, none of them writes one offer per business from the club's free slots and shows the logo on the club's own equipment. We did not test these products ourselves.</p>
""" + captioned_table("Players around sports sponsoring and the gap we fill.", ["Player", "What it does", "The gap we fill"], [
    ["All Sponsored", "Scans clubs' social media to measure brand visibility, and finds deals", "No offer for each business, no photo of the club's own kit"],
    ["Leedeel", "Website that connects brands with athletes, clubs and federations", "It is a marketplace, not a tool that writes the club's offer"],
    ["Spencer.club", "Intermediary for introductions, contracts and deals", "A person, not an instant tool"],
    ["SPONSO+", "Sponsoring by many small contributors", "A different model, not packages for local businesses"],
    ["Proposal and deck tools", "Templates, AI-written proposals, e-signature", "Generic: no club slots, no sector rule"],
]) + """
<p>Today, clubs often use a volunteer's own pitch, free templates, or nothing. This is our real competition. We use the five forces of the course. The AI model providers have medium power, and we lower it by using two models. New entrants are a strong threat, because a prompt and a screen can be copied in a weekend. Substitutes are strong, such as free templates and general chat assistants. Buyers, the clubs, can leave easily at the start. Rivalry is medium for now.</p>
<p>A copied model is easy, so we rely on three protections. The first is data: we learn which offers are accepted, by sector and price. The second is distribution through districts and leagues. The third is workflow: once the club keeps its slots, sponsors and renewals in our tool, leaving costs time.</p>
""")

rows_fin = [[str(t), f"{n:.0f}", eur(rev), eur(m), eur(c)] for (t, n, rev, m, c) in N["rows"]]
secs.append(f"""
<h1>8. Financial plan</h1>
<p>We assume the number of clubs grows in a straight line to {N['som_clubs']} in 36 months. The average price is €{N['blend_price']:.1f} a month and the average cost to serve is €{N['blend_cost']:.1f}. Fixed costs are {eur(N['FIXED_MONTH'])} a month, for two small stipends and tools. The gross margin is {N['contrib'] / N['blend_price'] * 100:.0f}%. The monthly result becomes positive in month {be}, at {N['breakeven_clubs']} clubs. Cash is lowest in month {t_low}, at {eur(-N['trough'])}.</p>
{figure(fig_cash(), "Cash over 36 months.")}
{captioned_table("Some months of the financial plan.", ["Month", "Clubs", "Monthly revenue", "Result of the month", "Cash so far"], rows_fin)}
<p>We ask for {eur(N['ask'])} to run for 18 months. This is the lowest cash point of {eur(-N['trough'])} plus six months of fixed costs ({eur(6 * N['FIXED_MONTH'])}), rounded up. In 18 months we want three pilot clubs with measured results, at least one agreement with a district or a league, and {N['breakeven_clubs']} paying clubs.</p>
""")

secs.append(f"""
<h1>9. Responsible and scalable by design</h1>
<p><b>Data protection.</b> The prototype uses no personal data. It uses business names and a made-up club. In real use, the tool would hold club data and business contacts. We would keep only what we need, set how long we keep it, sign a data agreement with the AI provider and prefer hosting in the European Union. Sales emails to businesses follow special rules, which we still have to check.</p>
<p><b>AI Act.</b> We see the tool as limited risk. It writes sales offers and does not make decisions about people. The rule on transparency applies, so the app says under each email that the text was written with the help of AI and must be read before sending. The dates of the law have changed over time, so we must check the official calendar before a real launch.</p>
<p><b>Fairness.</b> The tool does not score or rank people. Its rules are about businesses. Alcohol, tobacco and gambling are left out because their advertising is limited in sport, and a competitor of a current sponsor is flagged. We still need to confirm these rules with a federation.</p>
<p><b>Accountability.</b> The model card would say what the tool is for (offers for local sponsors) and what it is not for (legal advice, regulated products). The data sheet would describe the club slot fields and who updates them. The audit trail would keep, for each offer, the input, the slots chosen, the model, the cost and the time. The prototype already shows cost and time for each offer.</p>
<p><b>Cost and speed at scale.</b> With {N['som_clubs']} clubs, about {num(N['calls'])} offers a month cost about ${N['ai_small']:.1f} with the small model, which is {N['ai_small'] / N['mrr_full'] * 100:.2f}% of monthly revenue. With the large model the bill would be about ${N['ai_large']:.0f}, or {N['ai_large'] / N['mrr_full'] * 100:.1f}%. So the AI cost is not the main risk. The four to five seconds of writing time is the main thing to improve.</p>
""")

secs.append(f"""
<h1>10. Risks, assumptions and next steps</h1>
<p>Our results depend on assumptions that we have not tested with clubs yet. This table lists the main ones and how we will test them.</p>
{captioned_table("Main assumptions and how to test them.", ["Assumption", "Value used", "How we will test it"], [
    ["Rise in sponsoring at full use", "30%", "Three pilot clubs for one season, before and after"],
    ["Use of the tool in year 1", "40%", "How much the pilot clubs use it"],
    ["Clubs pay for the tool", f"€{N['PRICE_MONTH']['mid']} and €{N['PRICE_MONTH']['flagship']} a month", "Ten calls to mid-size clubs"],
    ["Districts pass the tool on", "11 new clubs a month", "Two or three talks with districts or leagues"],
    ["Cost to serve", f"€{N['COST_SERVE_MONTH']['mid']} and €{N['COST_SERVE_MONTH']['flagship']} a month", "Real hosting and support time in the pilots"],
    ["Price of the minibus slot", "€800", "No public price found, to confirm with clubs"],
])}
<p>Other risks matter too. Competitors may add similar features, so distribution and data matter more than the screen. A business must agree before we show its logo in a photo, and the photo is only a proposal. The market is small, which is why the amount we ask for is small, and the plan does not need a big raise.</p>
<p>In the next 30 days we will call ten mid-size clubs, start three pilot clubs and meet two district or league contacts. A pilot is a success if sponsoring rises by at least 15%, or if the club signs two new sponsors.</p>
""")

secs.append("""
<h1 style="break-before: page">Sources</h1>
<ul class="refs">
<li>French Olympic Committee (CNOSF), study on the funding of sports clubs: club types and average budgets, 2025 edition.</li>
<li>CNOSF, resources of sports clubs (memberships, grants and partnerships), 2020, mos.episciences.org.</li>
<li>Regional football league document on club funding, ligueoccitanie.ffr.fr (clubs that struggle to cover costs).</li>
<li>Price comparisons of club management software, getapp.fr and lafabriquedunet.fr, 2026 (€19 to €49 a month).</li>
<li>Sponsoring prices: an agency blog (jersey sponsoring from €1,500 to €5,000 a season) and a club brochure (pitch boards from €500 to €750 excluding tax).</li>
<li>Competitor websites and press: All Sponsored (radiosports.fr), Leedeel, Spencer.club, SPONSO+, SignNow, Storydoc, Playbook.</li>
<li>Club counts: French football federation (about 12,000 clubs), French rugby federation (more than 1,900 clubs), total clubs from an online encyclopedia (2020, weak source).</li>
</ul>
<p>We read all sources in November 2026. Numbers that come from our own assumptions are marked as such in the text.</p>
""")

team_txt = ", ".join(html.escape(m["name"]) if m["name"] else "[name to add]" for m in CFG["team"])
cover = f"""
<section class="cover">
<div class="bar"></div>
<h1 class="title">{NAME}</h1>
<p class="subtitle">An AI assistant that helps amateur clubs find local sponsors</p>
<p class="meta">Final project report<br>Monetizing Data and AI, MSc 1<br>November 2026</p>
<p class="meta">Team: {team_txt}</p>
</section>
"""

CSS = f"""
@page {{ size: A4; margin: 24mm 22mm 24mm 22mm; @bottom-center {{ content: counter(page); font: 9pt "Helvetica Neue", Arial, sans-serif; color: {GREY} }} }}
@page :first {{ @bottom-center {{ content: none }} }}
* {{ box-sizing: border-box }}
body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: {INK}; text-align: justify; hyphens: manual; margin: 0 }}
p {{ margin: 0 0 8pt; orphans: 3; widows: 3 }}
h1 {{ font-size: 15pt; line-height: 1.25; margin: 20pt 0 8pt; color: {NAVY}; text-align: left; break-after: avoid }}
.cover {{ height: 240mm; display: flex; flex-direction: column; justify-content: center; text-align: left; break-after: page }}
.cover .bar {{ width: 48pt; height: 5pt; background: {ACCENT}; margin-bottom: 18pt }}
.cover h1.title {{ font-size: 40pt; margin: 0 0 8pt; color: {INK} }}
.cover .subtitle {{ font-size: 16pt; color: {NAVY}; margin-bottom: 40pt; text-align: left }}
.cover .meta {{ font-size: 11pt; color: {GREY}; text-align: left }}
figure {{ margin: 12pt 0; break-inside: avoid; text-align: center }}
figure svg {{ width: 100%; height: auto }} figure.narrow svg {{ width: 82%; margin: 0 auto; display: block }}
figcaption {{ font-size: 9pt; color: {GREY}; text-align: left; margin-top: 4pt; line-height: 1.35 }}
.pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8pt }} .trio {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6pt }}
figure img {{ width: 100%; height: auto; border-radius: 3pt; display: block }}
.tab {{ margin: 10pt 0; break-inside: avoid }} .tcap {{ font-size: 9pt; color: {GREY}; margin-bottom: 4pt; text-align: left }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; line-height: 1.35; text-align: left }}
th {{ background: {NAVY}; color: #fff; padding: 4pt 6pt; text-align: left; font-weight: 700 }}
td {{ padding: 4pt 6pt; border-bottom: 0.5pt solid {LINE}; vertical-align: top }}
ul.refs {{ font-size: 9.5pt; padding-left: 14pt; text-align: left }} ul.refs li {{ margin-bottom: 4pt }}
"""
doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{NAME} report</title><style>{CSS}</style></head><body>{cover}{"".join(secs)}</body></html>'
out_html, out_pdf = ROOT / "dossier" / "report.html", ROOT / "dossier" / "report.pdf"
out_html.write_text(doc, encoding="utf-8")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", f"file://{out_html}"], check=True, capture_output=True, timeout=120)
print(out_pdf, out_pdf.stat().st_size // 1024, "KB")
