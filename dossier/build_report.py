"""Construit le rapport final (HTML puis PDF, A4) à partir des chiffres du calculateur.

Usage : python dossier/build_report.py
Mise en page : texte justifié, interligne 1,5, marges de 22 mm, figures numérotées et légendées,
tableaux sans justification, numéros de page. Ponctuation naturelle : aucun tiret long ni flèche.
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
INK, NAVY, GREY, LINE, ACCENT, PANEL = "#1B2430", "#1F4E8C", "#6B7280", "#D9DDE4", "#F2B705", "#F1F3F6"
I, P = N["I"], N["P"]
COST = f"{N['small_cost'] + 5e-6:.4f}"


def eur(x, d=0):
    return ("-" if x < 0 else "") + f"€{abs(x):,.{d}f}"


def num(x, d=0):
    return f"{x:,.{d}f}"


# ---------- Images ----------
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
base = scenes.render_scene("pitch_boards", (0,), scenes.wordmark("Assurances Mercier"))
img_boards = b64(scenes.render_scene("pitch_boards", (1, 2, 3), logo, base=base))
img_back = b64(scenes.render_scene("jersey_back", (0,), logo))

# ---------- Trésorerie ----------
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
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Cumulative cash over 36 months">{grid}{xt}'
        f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W - R}" y2="{Y(0):.1f}" stroke="{GREY}" stroke-dasharray="4 3"/>'
        f'<line x1="{X(be):.1f}" y1="{T}" x2="{X(be):.1f}" y2="{H - B}" stroke="{ACCENT}" stroke-width="2.5"/>'
        f'<text x="{X(be) + 8:.1f}" y="{T + 12}" font-size="13" fill="{INK}">Monthly break-even, month {be}</text>'
        f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="2.8" stroke-linejoin="round"/>'
        f'<circle cx="{X(t_low):.1f}" cy="{Y(cash[t_low]):.1f}" r="4" fill="{NAVY}"/>'
        f'<text x="{X(be) + 10:.1f}" y="{Y(cash[t_low]) + 26:.1f}" font-size="13" fill="{INK}">Low point {eur(cash[t_low])}</text>'
        f'<circle cx="{X(36):.1f}" cy="{Y(cash[36]):.1f}" r="4" fill="{NAVY}"/>'
        f'<text x="{X(36) - 8:.1f}" y="{Y(cash[36]) + 5:.1f}" text-anchor="end" font-size="13" fill="{INK}">{eur(cash[36])}</text>'
        f'<text x="{(L + W - R) / 2:.0f}" y="{H - 2}" text-anchor="middle" font-size="12" fill="{GREY}">Months after launch</text></svg>'
    )


def fig_stack() -> str:
    rows = [
        ("7", "Observability", "cost and time per offer, audit log", "Buy", "#E7EAF0"),
        ("6", "Distribution", "district and league partnerships, PDF export", "Partner", "#FBEBB5"),
        ("5", "Application", "club profile, offer page, mock-ups", "Build", "#C9D6EA"),
        ("4", "Orchestration", "fixed workflow, five steps", "Build", "#C9D6EA"),
        ("3", "Model", "small model by default, large as fallback", "Buy", "#E7EAF0"),
        ("2", "Data and storage", "club profiles, offers, outcomes", "Buy", "#E7EAF0"),
        ("1", "Sources", "club inventory, public business directories", "Partner", "#FBEBB5"),
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
    return f'<svg viewBox="0 0 600 290" role="img" aria-label="Seven-layer product stack">{"".join(out)}</svg>'


def fig_bars() -> str:
    rows = [("Value created", I["y1_month"], "#B9C9E2"), ("Our price", N["PRICE_MONTH"]["intermediaire"], NAVY), ("Cost to serve", N["COST_SERVE_MONTH"]["intermediaire"], "#9AA3AF")]
    out = []
    for i, (lab, v, col) in enumerate(rows):
        y = 8 + i * 50
        w = max(6, 330 * v / I["y1_month"])
        out.append(f'<text x="0" y="{y + 24}" font-size="14" fill="{INK}">{lab}</text><rect x="120" y="{y}" width="{w:.0f}" height="32" rx="3" fill="{col}"/><text x="{120 + w + 10:.0f}" y="{y + 22}" font-size="15" font-weight="700" fill="{INK}">{eur(v)}</text>')
    return f'<svg viewBox="0 0 600 170" role="img" aria-label="Value, price and cost per month">{"".join(out)}</svg>'


# ---------- Contenu ----------
def table(head, rows, widths=None):
    th = "".join(f"<th>{h}</th>" for h in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{body}</table>"


fig_n = {"n": 0}
tab_n = {"n": 0}


def figure(content, caption, cls=""):
    fig_n["n"] += 1
    return f'<figure class="{cls}">{content}<figcaption>Figure {fig_n["n"]}. {caption}</figcaption></figure>'


def captioned_table(caption, head, rows):
    tab_n["n"] += 1
    return f'<div class="tab"><div class="tcap">Table {tab_n["n"]}. {caption}</div>{table(head, rows)}</div>'


demo = f"The live demonstration is available at {html.escape(URL)}." if URL else "The link to the live demonstration is given in the submission email."

secs = []

secs.append(f"""
<h1>1. Summary</h1>
<p>Amateur sports clubs depend on local sponsors, yet the volunteers who prepare each offer have little time, and they often propose slots that are already sold. {NAME} is an AI assistant that turns the name of a local business into a ready-to-send offer. It proposes only the slots the club has free, avoids sector conflicts with current sponsors, links the offer to the club's declared needs, and shows the sponsor's logo on photo-realistic mock-ups of the club's kit, boards and minibus.</p>
<p>We target mid-size and flagship clubs, about {num(N['n_inter'] + N['n_phare'])} in France. The plan is a subscription of €{N['PRICE_MONTH']['intermediaire']} a month for mid-size clubs and €{N['PRICE_MONTH']['phare']} a month for flagship clubs, which is about {I['capture'] * 100:.0f}% and {P['capture'] * 100:.0f}% of the value created for them. With {N['som_clubs']} clubs after three years, annual recurring revenue reaches {eur(N['SOM'])}. The business breaks even at {N['breakeven_clubs']} clubs in month {be}, and we ask for {eur(N['ask'])} to cover 18 months.</p>
<p>The prototype is working and measured: an offer costs about ${COST} and takes four to five seconds to write. We have no paying client yet. The most fragile assumption is the uplift in sponsoring, which pilots with three clubs will measure. {demo}</p>
""")

secs.append(f"""
<h1>2. The problem</h1>
<p>Sponsorship is a modest but important share of a club's resources. A study by the French Olympic Committee estimates that partnerships bring about {N['SPONSOR_SHARE'] * 100:.0f}% of the resources of sports associations, and that 37% of clubs run a deficit. Budgets vary widely: 63% of clubs have less than €10,000, while the average mid-size club has {eur(N['BUDGET']['intermediaire'])} and the average flagship club {eur(N['BUDGET']['phare'])}.</p>
<p>Our persona is Julien, the volunteer treasurer of a football club with 320 members. He writes each sponsor pitch alone, in the evening. We believe three problems follow. The pitches are generic, so a bakery and a garage receive the same text. The offers include slots that are already sold, or sectors that conflict with a current sponsor. Nothing connects the offer to what the club needs this season. These three problems are hypotheses taken from the structure of the work, not findings from interviews. The first action of the pilot phase is to test them in ten calls with mid-size clubs.</p>
{figure(f'<div class="pair"><img src="{img_empty}"><img src="{img_boards}"></div>', "Left: the unsold advertising boards of a club. Right: the same boards with a sponsor's logo placed by the tool. The logo shown is an example.")}
""")

secs.append(f"""
<h1>3. The solution and its moment of truth</h1>
<p>The moment of truth is simple: a business name goes in, and a personalised offer comes out, with the business's logo already placed on the club's equipment. The jury can type any business and upload any logo.</p>
<p>The tool works in five steps. The club describes ten slots, each with a price, a status (free or taken), the current sponsor and its sector, as well as its needs and its fundraising goal. A guardrail then blocks alcohol, tobacco and gambling businesses before any call to the AI. The AI model chooses three offers among the free slots and writes the email. The code verifies the result: a taken slot is removed, prices come from the club's grid, and a business whose sector matches a current sponsor is flagged for human review. Finally, the logo is placed on photographs by perspective and lighting.</p>
<p>The behaviour is adapted to each case. A garage is offered the minibus and the entrance banner, and the offer is tied to the club's need to renew the minibus. A sports shop is offered the training bibs and the boards. An estate agency triggers a warning because a real estate group already sponsors the club. A business whose activity cannot be guessed from its name, such as "Chez Momo", is sent to a human.</p>
{figure(f'<div class="trio"><img src="{img_van}"><img src="{img_boards}"><img src="{img_back}"></div>', "Mock-ups produced by the tool for an example business: the minibus, the pitch boards and the back of the jersey. Existing sponsors stay visible on the photographs.")}
""")

secs.append(f"""
<h1>4. How it is built</h1>
<p>We apply the seven-layer model of the course. The default rule is to buy the model, build what makes the difference (orchestration and user experience), buy the commodity tools, and partner where someone else owns the access. Figure 3 gives the decision for each layer.</p>
<p>The prototype covers layers 3 to 5 and a light version of layer 7. Storage, distribution and public business directories belong to the roadmap and are not part of the demonstration. We chose the simplest agent shape that works, a fixed workflow with a single AI call, because it is cheaper, faster and easier to test than an agent loop.</p>
<p>The photographs are produced once with an image model, at a total cost of $0.47 for seven scenes. At run time the logo is placed by code, so images cost nothing and are instant. This also makes the demonstration reliable in front of a jury.</p>
<p>Measured on the prototype, one offer uses about {N['TOK_IN']} input tokens and {N['TOK_OUT']} output tokens with the small model, which costs about ${COST}. The writing takes 3.5 to 4.5 seconds, so the whole offer appears in four to eight seconds, above the three-second target of the course. Streaming the text is the first improvement.</p>
{figure(fig_stack(), "The seven layers of the product and the decision for each: build, buy or partner.", "narrow")}
""")

secs.append(f"""
<h1>5. Market</h1>
<p>We size the market from the bottom up: the clubs that sign, multiplied by the price per club. The club, represented by its treasurer or president, is the customer who signs. We exclude small neighbourhood clubs, which make up 66% of clubs: their sponsoring is about €1,060 a year, which leaves under €100 of net gain, too little to pay for a tool.</p>
{captioned_table(f"Market sizing, with annual prices of €{num(N['arpa']['intermediaire'])} for a mid-size club and €{num(N['arpa']['phare'])} for a flagship club.", ["Level", "Clubs", "Annual value"], [
    ["Total market in France", f"{num(N['n_inter'])} mid-size, {num(N['n_phare'])} flagship ({num(N['n_inter'] + N['n_phare'])} in total)", f"{eur(N['TAM'] / 1e6, 1)}M"],
    ["Reachable today (football and rugby)", f"{num(N['sam_inter'])} mid-size, {num(N['sam_phare'])} flagship ({num(N['sam_clubs'])} in total)", f"{eur(N['SAM'] / 1e6, 2)}M"],
    ["Target in three years", f"{N['SOM_CLUBS']['intermediaire']} mid-size, {N['SOM_CLUBS']['phare']} flagship", eur(N['SOM'])],
])}
<p>The target of {N['som_clubs']} clubs in 36 months equals {N['som_per_month']:.0f} new clubs a month, or {N['som_clubs'] / N['sam_clubs'] * 100:.1f}% of the reachable clubs. We expect most of them to come through district and league partnerships that relay the tool, with direct calls as a complement. No agreement exists yet.</p>
<p>The sources are imperfect. The split of clubs by size comes from a study that reuses data from 2011 and 2012. The total number of clubs in France, about {num(165000)}, comes from a weak source dated 2020. Club counts for football (about 12,000) and rugby (more than 1,900) come from the federations. These figures give orders of magnitude and should be cross-checked with the Ministry of Sports before any investor use.</p>
""")

sens_rows = [
    [f"{a * 100:.0f}%", eur(I['full'] * a * N['NET_RATIO']), f"{N['PRICE_MONTH']['intermediaire'] / (I['full'] * a * N['NET_RATIO'] / 12) * 100:.0f}%"]
    for a in (0.30, 0.40, 0.50, 0.60)
]
secs.append(f"""
<h1>6. Business model and price</h1>
<p>The model is a software subscription per club, with two plans that follow the size of the club. For a club, the archetype is revenue uplift: the tool helps it present more adapted offers and sign more local sponsors. We count the net gain, after the cost of making the signs and the kit. We follow the course rule that a price should capture 10 to 30% of the value created, because cost-plus pricing would leave most of the value unclaimed.</p>
{captioned_table("The two plans and the value they create in year 1.", ["", "Mid-size club", "Flagship club"], [
    ["Sponsoring today (9% of budget)", eur(I['base']), eur(P['base'])],
    ["Possible uplift at full use (30%)", eur(I['full']), eur(P['full'])],
    ["Net gain in year 1 (40% adoption, 90% net)", eur(I['y1']), eur(P['y1'])],
    ["Value per month", eur(I['y1_month'], 1), eur(P['y1_month'], 1)],
    ["Price per month", f"€{N['PRICE_MONTH']['intermediaire']}", f"€{N['PRICE_MONTH']['phare']}"],
    ["Share of value captured", f"{I['capture'] * 100:.0f}%", f"{P['capture'] * 100:.0f}%"],
    ["Cost to serve per month", f"€{N['COST_SERVE_MONTH']['intermediaire']}", f"€{N['COST_SERVE_MONTH']['phare']}"],
    ["Gross margin", f"{I['margin'] * 100:.0f}%", f"{P['margin'] * 100:.0f}%"],
])}
{figure(fig_bars(), "Value created, price and cost to serve per month for a mid-size club.", "narrow")}
<p>The price of €{N['PRICE_MONTH']['intermediaire']} stays below the €19 to €49 a month that clubs already pay for management software, so the tool is a light complement rather than a replacement. Two prices should not be confused: the €300 to €1,500 per season shown in the demonstration is what the club charges its sponsors, while the €{N['PRICE_MONTH']['intermediaire']} and €{N['PRICE_MONTH']['phare']} a month are what we charge the club.</p>
{captioned_table("Sensitivity of the mid-size plan to year-1 adoption.", ["Adoption", "Net gain per year", "Price as a share of value"], sens_rows)}
""")

secs.append("""
<h1>7. Competition and defensibility</h1>
<p>We found several players around sports sponsorship in France. None of them, as far as we could verify from their own pages and press, prepares an offer per business from the club's free slots and shows the logo on the club's own equipment. We did not test these products ourselves.</p>
""" + captioned_table("Players around sports sponsorship and the gap we address.", ["Player", "What it does", "Gap we address"], [
    ["All Sponsored", "Scans clubs' social networks to measure brand visibility and brokers sponsoring", "No offer per business, no mock-up of the club's own kit"],
    ["Leedeel", "Platform connecting brands with athletes, clubs and federations", "A marketplace, not a tool that prepares the club's offer"],
    ["Spencer.club", "Intermediary for introductions, contracts and structuring", "A human service, not an instant tool"],
    ["SPONSO+", "Participatory sponsoring by many small contributors", "A different model, not packages for local businesses"],
    ["Proposal and deck tools", "Templates, AI-assisted proposals, electronic signature", "Generic, with no club inventory or sector rule"],
]) + """
<p>What clubs hire today is the real competition: a volunteer's own pitch, free templates, or doing nothing. We apply the five forces of the course to this market. Suppliers, the model providers, hold medium power, and we reduce it by using two models. The threat of new entrants is high, because a prompt and a screen can be rebuilt in a weekend. Substitutes are strong, with free templates and general chat assistants. Buyers, the clubs, have low switching costs at first. Rivalry is medium for now.</p>
<p>Since the model cannot be defended, we rely on three moats. The first is data: which offers close, by sector and price, collected from the offers sent through the tool. The second is distribution through districts and leagues. The third is workflow: once the club keeps its inventory, sponsors and renewals in the tool, leaving costs time.</p>
""")

rows_fin = [[str(t), f"{n:.0f}", eur(rev), eur(m), eur(c)] for (t, n, rev, m, c) in N["rows"]]
secs.append(f"""
<h1>8. Financial plan</h1>
<p>The plan assumes a linear ramp to {N['som_clubs']} paying clubs over 36 months, a blended price of €{N['blend_price']:.1f} a month, a blended cost to serve of €{N['blend_cost']:.1f} and fixed costs of {eur(N['FIXED_MONTH'])} a month, which cover two small stipends and tools. The gross margin is {N['contrib'] / N['blend_price'] * 100:.0f}%. The monthly result turns positive in month {be}, after {N['breakeven_clubs']} clubs. The cumulative cash reaches its lowest point of {eur(-N['trough'])} in month {t_low}.</p>
{figure(fig_cash(), "Cumulative cash over 36 months.")}
{captioned_table("Selected months of the financial plan.", ["Month", "Clubs", "Monthly revenue", "Monthly result", "Cumulative cash"], rows_fin)}
<p>We ask for {eur(N['ask'])} to cover 18 months. This amount equals the cash low point of {eur(-N['trough'])} plus six months of fixed costs ({eur(6 * N['FIXED_MONTH'])}), rounded up. Within 18 months we aim for three pilot clubs with measured results, at least one agreement with a district or a league, and {N['breakeven_clubs']} paying clubs.</p>
""")

secs.append(f"""
<h1>9. Responsible and scalable by design</h1>
<p><b>Data protection.</b> The prototype processes no personal data: it uses business names and a fictional club. In production the tool would handle club data and professional contacts. We would collect only what is needed, set a retention period, sign a data processing agreement with the model provider, and prefer hosting in the European Union. Prospecting emails to businesses must follow the rules on business-to-business marketing, which we still need to verify.</p>
<p><b>AI Act.</b> We classify the tool as limited risk, since it is a text generator for sales offers, not a system that decides about people. The transparency duty applies, and the interface states under every email that the text was generated with the help of AI and must be reviewed before sending. The application dates of the regulation have evolved, so they must be checked on the official calendar before any commercial launch.</p>
<p><b>Fairness.</b> The tool does not score or rank people. Its rules concern businesses: alcohol, tobacco and gambling are excluded because their advertising is restricted in sport, and a competitor of an existing sponsor is flagged. These rules still need to be confirmed with a federation.</p>
<p><b>Accountability.</b> The model card would state the intended use (offers for local sponsors) and the out-of-scope uses (legal advice, regulated products). The datasheet would describe the club inventory fields and who updates them. The audit trail would record for each offer the input, the slots chosen, the model, the cost and the time. The prototype already displays cost and time for each offer.</p>
<p><b>Cost and latency at scale.</b> At {N['som_clubs']} clubs, about {num(N['calls'])} offers a month cost about ${N['ai_small']:.1f} with the small model, which is {N['ai_small'] / N['mrr_full'] * 100:.2f}% of monthly revenue. With the large model the bill would be about ${N['ai_large']:.0f}, or {N['ai_large'] / N['mrr_full'] * 100:.1f}%. The cost of the model is therefore not the main risk. The four to five seconds of writing time is the main technical point to improve.</p>
""")

secs.append(f"""
<h1>10. Risks, assumptions and next steps</h1>
<p>Our results rest on assumptions that we have not yet tested with clubs. We list the most important ones and how we will check them.</p>
{captioned_table("Main assumptions and how to test them.", ["Assumption", "Value used", "How we will test it"], [
    ["Sponsoring uplift at full use", "30%", "Three pilot clubs over one season, measured before and after"],
    ["Year-1 adoption", "40%", "Usage in the pilots"],
    ["Clubs pay for the tool", f"€{N['PRICE_MONTH']['intermediaire']} and €{N['PRICE_MONTH']['phare']} a month", "Ten calls to mid-size clubs"],
    ["Districts relay the tool", "11 new clubs a month", "Two or three conversations with districts or leagues"],
    ["Cost to serve", f"€{N['COST_SERVE_MONTH']['intermediaire']} and €{N['COST_SERVE_MONTH']['phare']} a month", "Real hosting and support time in the pilots"],
    ["Minibus slot price", "€800", "No public price found, to be confirmed with clubs"],
])}
<p>Other risks deserve attention. Competitors may add similar features, so distribution and data matter more than the interface. The use of a business's logo in a mock-up needs the business's consent, and the offer is only a proposal. The size of the market is small, which is why the amount requested is modest and the plan does not depend on a large raise.</p>
<p>The next steps for the next 30 days are to call ten mid-size clubs, to start three pilot clubs, and to meet two district or league contacts. The success criterion for a pilot is an increase of at least 15% in sponsoring, or two new sponsors per pilot club.</p>
""")

secs.append("""
<h1 style="break-before: page">Sources</h1>
<ul class="refs">
<li>Comité national olympique et sportif français, study on the financing of sports associations (typology of clubs and average budgets), 2025 edition.</li>
<li>CNOSF, resources of sports associations (share of memberships, subsidies and partnerships), 2020, mos.episciences.org.</li>
<li>Regional football league document on club financing, ligueoccitanie.ffr.fr (clubs struggling to cover expenses).</li>
<li>Club management software price comparisons, getapp.fr and lafabriquedunet.fr, 2026 (€19 to €49 a month).</li>
<li>Sponsorship price references: agency blog (jersey sponsoring from €1,500 to €5,000 a season) and a club commercial brochure (pitch-side boards from €500 to €750 excluding tax).</li>
<li>Competitor pages and press: All Sponsored (radiosports.fr), Leedeel, Spencer.club, SPONSO+, SignNow, Storydoc, Playbook.</li>
<li>Club counts: French football federation (about 12,000 clubs), French rugby federation (more than 1,900 clubs), total number of clubs from a general encyclopedia (2020, weak source).</li>
</ul>
<p>All sources were consulted in November 2026. Figures that come from our own assumptions are identified as such in the text.</p>
""")

cover = f"""
<section class="cover">
<div class="bar"></div>
<h1 class="title">{NAME}</h1>
<p class="subtitle">An AI assistant that helps amateur clubs find local sponsors</p>
<p class="meta">Final project report<br>Monetizing Data and AI, MSc 1<br>November 2026</p>
<p class="meta">Team: {", ".join(html.escape(m["name"]) if m["name"] else "[name to add]" for m in CFG["team"])}</p>
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
print(out_pdf, out_pdf.stat().st_size // 1024, "Ko")
