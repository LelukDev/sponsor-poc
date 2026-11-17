"""Numbers calculator: one single source for every figure of the pitch.

Legend: [S] cited source; [M] measured on the PoC; [H] assumption to test.
Run: python dossier/calc.py   (writes dossier/numbers.md)
"""

import math
import re
from pathlib import Path

# ---------- Inputs ----------
# Club types (CNOSF study, reused in 2025; old data, so rough numbers) [S]
SHARE = {"small": 0.66, "mid": 0.31, "flagship": 0.03}
BUDGET = {"small": 11_832, "mid": 80_145, "flagship": 917_857}
SPONSOR_SHARE = 0.09          # partnerships = 9% of resources (CNOSF 2020) [S]
CLUBS_FRANCE = 165_000        # about 165,900 in 2020 (encyclopedia, weak source) [S]
CLUBS_FOOT = 12_000           # French football federation: about 12,000 amateur clubs [S]
CLUBS_RUGBY = 1_900           # French rugby federation: more than 1,900 clubs [S]

UPLIFT = 0.30                 # sponsoring increase allowed by the tool at full use [H]
ADOPTION = 0.40               # average adoption in year 1 (course: 30 to 60%) [H]
NET_RATIO = 0.90              # share kept after the cost of signs and kit [H]

PRICE_MONTH = {"mid": 15, "flagship": 150}          # euros per month [H]
COST_SERVE_MONTH = {"mid": 3, "flagship": 12}       # hosting, support, AI [H]
PROPOSALS_MONTH = {"mid": 15, "flagship": 60}       # offers generated per club per month [H]

SOM_CLUBS = {"mid": 360, "flagship": 40}            # clubs won in 36 months [H]
MONTHS = 36
FIXED_MONTH = 3_000           # 2 small stipends of 1,000 + tools, legal, travel [H]

# Measured cost of one offer (PoC, OpenRouter) [M]
TOK_IN, TOK_OUT = 1560, 780   # average of 6 real tests with the club inventory
P_SMALL = (0.10, 0.50)        # dollars per million tokens, claude-haiku-5.5
P_LARGE = (2.00, 10.00)       # claude-sonnet-5.5
USD_EUR = 1.0                 # calculation assumption [H]

GRID = {"Tent 300": 300, "Bibs 350": 350, "Shorts 400": 400, "Banner 500": 500, "Sleeve 600": 600, "Main board 600": 600,
        "Jersey back 700": 700, "Minibus 800": 800, "Boards x3 900": 900, "Jersey chest 1,500": 1_500}


def eur(x, d=0):
    return ("-" if x < 0 else "") + f"€{abs(x):,.{d}f}"


def call_cost(p):
    return (TOK_IN * p[0] + TOK_OUT * p[1]) / 1e6 * USD_EUR


# ---------- Calculations ----------
res = {}
for seg in ("mid", "flagship"):
    base = BUDGET[seg] * SPONSOR_SHARE
    full = base * UPLIFT
    y1 = full * ADOPTION * NET_RATIO
    res[seg] = {
        "base": base, "full": full, "y1": y1, "y1_month": y1 / 12,
        "price_year": PRICE_MONTH[seg] * 12,
        "capture": PRICE_MONTH[seg] / (y1 / 12),
        "roi": (y1 - PRICE_MONTH[seg] * 12) / (PRICE_MONTH[seg] * 12),
        "margin": 1 - COST_SERVE_MONTH[seg] / PRICE_MONTH[seg],
    }

n_mid = round(SHARE["mid"] * CLUBS_FRANCE)
n_flag = round(SHARE["flagship"] * CLUBS_FRANCE)
arpa = {s: PRICE_MONTH[s] * 12 for s in PRICE_MONTH}
TAM = n_mid * arpa["mid"] + n_flag * arpa["flagship"]

sam_base = CLUBS_FOOT + CLUBS_RUGBY
sam_mid = round(SHARE["mid"] * sam_base)
sam_flag = round(SHARE["flagship"] * sam_base)
SAM = sam_mid * arpa["mid"] + sam_flag * arpa["flagship"]
sam_clubs = sam_mid + sam_flag

som_clubs = sum(SOM_CLUBS.values())
SOM = sum(SOM_CLUBS[s] * arpa[s] for s in SOM_CLUBS)
som_per_month = som_clubs / MONTHS

mrr_full = sum(SOM_CLUBS[s] * PRICE_MONTH[s] for s in SOM_CLUBS)
cost_full = sum(SOM_CLUBS[s] * COST_SERVE_MONTH[s] for s in SOM_CLUBS)
blend_price = mrr_full / som_clubs
blend_cost = cost_full / som_clubs
contrib = blend_price - blend_cost
breakeven_clubs = math.ceil(FIXED_MONTH / contrib)

# Monthly simulation: linear ramp up to the target at month 36
cash, trough, be_month, rows = 0.0, 0.0, None, []
for t in range(1, MONTHS + 1):
    n = som_clubs * t / MONTHS
    margin = n * contrib - FIXED_MONTH
    cash += margin
    trough = min(trough, cash)
    if be_month is None and margin >= 0:
        be_month = t
    if t in (6, 12, 18, 24, 36):
        rows.append((t, n, n * blend_price, margin, cash))
ask = math.ceil((-trough + 6 * FIXED_MONTH) / 5_000) * 5_000

# AI at the scale of the target
calls = sum(SOM_CLUBS[s] * PROPOSALS_MONTH[s] for s in SOM_CLUBS)
small_cost, large_cost = call_cost(P_SMALL), call_cost(P_LARGE)
ai_small, ai_large = calls * small_cost, calls * large_cost

# ---------- Choice of the use case: method of the course ----------
# Impact = rise of the club budget in %; ICE scale: 2.5% or more = 8; 2 to 2.5% = 7; 1 to 2% = 5
usecases = [
    # name, pay, switch, degrade, evidence
    ("Sponsorship offers with mock-ups", 1, 0, 1, "sponsoring is 9% of resources; 45% of clubs struggle to cover costs"),
    ("Match availability from WhatsApp", 0, 0, 1, "free tools exist (ClubPal, Kalisport Core)"),
    ("Membership fee reminders", 1, 0, 1, "fees are 68% of resources; tools already paid (€19 to €49 a month)"),
    ("Grant applications", 1, 0, 1, "grants are 16% of resources; long to write for volunteers"),
    ("Match reports for the website", 0, 0, 0, "no number moves if we remove it"),
    ("Volunteer schedule (tent, tournaments)", 0, 0, 1, "saves time, but no measurable euro"),
]
# RICE for the must-haves: (name, reach per quarter, impact, confidence, effort in person-months)
rice = [
    ("Membership fee reminders", 150, 1, 0.8, 3),
    ("Sponsorship offers with mock-ups", 15 * 3, 3, 0.5, 2),
    ("Grant applications", 1.5, 3, 0.5, 3),
]
rice = sorted([(n, r, i, c, e, r * i * c / e) for (n, r, i, c, e) in rice], key=lambda x: -x[5])
# ICE: impact (budget rise), confidence, ease
ice = [
    ("Sponsorship offers with mock-ups", 8, 5, 6, "+2.7% of the budget (30% of 9%)"),
    ("Membership fee reminders", 5, 8, 7, "+1.4% of the budget (2 points of 68%)"),
    ("Grant applications", 7, 5, 4, "+2.4% of the budget (15% of 16%)"),
]


def quad(i, e):
    if i > 5.5 and e > 5.5:
        return "Quick win"
    if i > 5.5:
        return "Big bet"
    if e > 5.5:
        return "Fill-in (buy it ready-made)"
    return "Money pit"


# ---------- Report ----------
I, P = res["mid"], res["flagship"]
md = []
w = md.append
w("# Numbers dossier: one source for the whole pitch\n")
w("Legend: **[S]** cited source; **[M]** measured on the PoC; **[H]** assumption to test with real clubs.\n")
w("Generated by `dossier/calc.py`. Change an assumption at the top of the file, run it again, and every figure follows.\n")

w("## 1. Fact sheet: the amateur sports club market\n")
w("| Fact | Value | Status |\n|---|---|---|")
w(f"| Clubs in France | about {CLUBS_FRANCE:,} | [S] weak source (encyclopedia, 2020) |")
w(f"| Mid-size clubs | {SHARE['mid']:.0%} of clubs, average budget {eur(BUDGET['mid'])} | [S] CNOSF, old data |")
w(f"| Flagship clubs | {SHARE['flagship']:.0%} of clubs, average budget {eur(BUDGET['flagship'])} | [S] same |")
w(f"| Small neighbourhood clubs | {SHARE['small']:.0%} of clubs, average budget {eur(BUDGET['small'])} | [S] same, **left out** (too small to pay) |")
w(f"| Share of partnerships in resources | {SPONSOR_SHARE:.0%} | [S] CNOSF 2020 |")
w("| Price of club management software | €19 to €49 a month | [S] comparison sites 2026 |")
w("| Price of slots | board €500 to €750 excl. tax; jersey €1,500 to €5,000 a season; minibus: no data | [S] one rugby brochure and one agency blog |")
w(f"| Demo price grid (10 slots, € per season) | {', '.join(GRID)} | [H] low end of the range |\n")

w("## 2. Choice of the use case\n")
w("**Three-question test** (pay, switch, degrade): 2 or 3 yes means must-have.\n")
w("| Use case | Pay | Switch | Degrade | Total | Evidence |\n|---|---|---|---|---|---|")
for n, p, s, d, f in usecases:
    t = p + s + d
    w(f"| {n} | {'yes' if p else 'no'} | {'yes' if s else 'no'} | {'yes' if d else 'no'} | {t}/3 {'**must-have**' if t >= 2 else 'nice-to-have'} | {f} |")
w("\n**RICE** (must-haves only): R = events per quarter, I = 3 massive / 1 medium, C = confidence, E = person-months [H].\n")
w("| Use case | R | I | C | E | RICE |\n|---|---|---|---|---|---|")
for n, r, i, c, e, sc in rice:
    w(f"| {n} | {r:g} | {i} | {c:.0%} | {e} | {sc:.1f} |")
w("\n**ICE and impact-ease grid** (impact = rise of the club budget; threshold 5.5).\n")
w("| Use case | Impact | Confidence | Ease | ICE | Quadrant | How the impact is computed |\n|---|---|---|---|---|---|---|")
for n, i, c, e, note in sorted(ice, key=lambda x: -(x[1] * x[2] * x[3])):
    w(f"| {n} | {i} | {c} | {e} | {i*c*e} | {quad(i, e)} | {note} |")
w("\n**Honest reading.** Membership fee reminders win on RICE and ICE because of volume and confidence, but their impact stays under the threshold: "
  "cheap tools already exist, so it is a fill-in to buy. Sponsorship offers are the only use case that is must-have, high impact and easy: a quick win. "
  "All confidence scores are assumptions. The first action is to call 10 clubs to test them.\n")

w("## 3. ROI: more sponsoring\n")
w("Archetype: **revenue uplift**. Named mechanism: *the club sends more personal offers and signs more local sponsors.*\n")
w("| | Mid-size club | Flagship club |\n|---|---|---|")
w(f"| Average budget [S] | {eur(BUDGET['mid'])} | {eur(BUDGET['flagship'])} |")
w(f"| Sponsoring today (9%) | {eur(I['base'])} | {eur(P['base'])} |")
w(f"| Possible rise at full use ({UPLIFT:.0%}) [H] | {eur(I['full'])} | {eur(P['full'])} |")
w(f"| Net gain in year 1 (adoption {ADOPTION:.0%}, {NET_RATIO:.0%} net) [H] | **{eur(I['y1'])}** | **{eur(P['y1'])}** |")
w(f"| Value per month | {eur(I['y1_month'], 1)} | {eur(P['y1_month'], 1)} |")
w(f"| Price of the tool per year | {eur(I['price_year'])} | {eur(P['price_year'])} |")
w(f"| Year-1 ROI | {I['roi']:.0%} | {P['roi']:.0%} |")
w(f"\n**Course sentence:** \"In year 1, a mid-size club signs {eur(I['y1'])} of extra net sponsoring ({UPLIFT:.0%} uplift, {ADOPTION:.0%} adoption); a flagship club, {eur(P['y1'])}.\"\n")
w("**Sensitivity to adoption:**\n")
w("| Adoption | Net gain, mid-size | Net gain, flagship | Price as share of value (mid / flagship) |\n|---|---|---|---|")
for a in (0.30, 0.40, 0.50, 0.60):
    gi = I["full"] * a * NET_RATIO
    gp = P["full"] * a * NET_RATIO
    w(f"| {a:.0%} | {eur(gi)} | {eur(gp)} | {PRICE_MONTH['mid']/(gi/12):.0%} / {PRICE_MONTH['flagship']/(gp/12):.0%} |")
w("")

w("## 4. Bottom-up market\n")
w("Customer who signs: **the club** (treasurer or president). Two plans: Club and Club+.\n")
w("| | Clubs | × price a year | = Market |\n|---|---|---|---|")
w(f"| **Total market**: mid-size + flagship clubs in France | {n_mid:,} + {n_flag:,} | {eur(arpa['mid'])} / {eur(arpa['flagship'])} | **{eur(TAM/1e6, 1)}M** |")
w(f"| **Reachable**: football + rugby (demo and district networks) | {sam_mid:,} + {sam_flag:,} = {sam_clubs:,} | same | **{eur(SAM/1e6, 2)}M** |")
w(f"| **Target in 3 years** | {SOM_CLUBS['mid']} + {SOM_CLUBS['flagship']} = {som_clubs} clubs ({som_clubs/sam_clubs:.1%} of reachable) | same | **{eur(SOM)} a year** |")
w(f"\nCheck: {som_clubs} clubs in {MONTHS} months = **{som_per_month:.1f} new clubs a month**. Who signs them? Districts and leagues that pass the tool to their clubs (partnership still to negotiate [H]), plus direct calls.\n")
w("Small neighbourhood clubs are left out: their sponsoring (9% of about €11,800, so about €1,060) leaves under €100 of net gain a year.\n")

w("## 5. Business model and price\n")
w("Model: **software subscription per club**, two plans by size (the price follows the value created, which grows with the budget).\n")
w("| | Mid-size club | Flagship club |\n|---|---|---|")
w(f"| Price | **€{PRICE_MONTH['mid']} a month** | **€{PRICE_MONTH['flagship']} a month** |")
w(f"| Share of value captured | {I['capture']:.0%} | {P['capture']:.0%} |")
w(f"| Cost to serve [H] | €{COST_SERVE_MONTH['mid']} a month | €{COST_SERVE_MONTH['flagship']} a month |")
w(f"| Gross margin | {I['margin']:.0%} | {P['margin']:.0%} |")
w(f"\n**Course sentence:** \"€{PRICE_MONTH['mid']} a month, which is {I['capture']:.0%} of the {eur(I['y1_month'])} of value created each month, for a cost to serve of €{COST_SERVE_MONTH['mid']}; €{PRICE_MONTH['flagship']} a month for a flagship club, which is {P['capture']:.0%} of {eur(P['y1_month'])}.\"\n")
w("The price stays under the €19 to €49 of management software: the tool is a light add-on, not a replacement. At 10 to 30% of the value, it follows the course rule.\n")
w("**Do not mix two prices.** The €300 to €1,500 slot prices of the demo are what **the club** charges **its sponsors**, per season. "
  "The €15 and €150 a month are what **we** charge **the club**.\n")
w("## 5b. Traction: what we can honestly say\n")
w("- No client yet: do not claim one.")
w("- Proven: an online PoC that writes an offer in 4 to 5 seconds for about $0.0006, for any business the jury names.")
w("- Pilot plan: 3 mid-size clubs, 1 season, sponsoring measured before and after (assumption +30%). Success: at least +15%, or 2 new sponsors per club.")
w("- To get before the defence if possible: 10 calls to clubs, 2 or 3 real quotes, and a letter of intent from a club or a district. Real feedback only.\n")

w("## 6. Cost of the AI, measured then projected\n")
w(f"- One offer = 1 call (the model reads the club inventory and picks the slots), {TOK_IN} input tokens, {TOK_OUT} output tokens **[M]**.")
w("- The realistic photos are generated once (7 images, about $0.47 in total). Placing the logo is then done by code, with no cost and no network call.")
w(f"- Small model (claude-haiku-5.5, $0.10 / $0.50 per million tokens): **${small_cost:.5f}** per offer; measured writing time: 3.5 to 4.5 s.")
w(f"- Large model (claude-sonnet-5.5, $2 / $10 per million tokens): ${large_cost:.5f} per offer.")
w(f"- At the scale of the target: {calls:,} offers a month, which is **${ai_small:.1f} a month** with the small model ({ai_small/mrr_full:.2%} of monthly revenue), ${ai_large:.0f} with the large model ({ai_large/mrr_full:.1%}).")
w("- So the cost of the AI is not the issue: hosting and support are bigger. The measured writing time (3.5 to 4.5 s) is above the 3 s target of the course; idea: show the text as it is written.\n")

w("## 7. Financials\n")
w(f"- Clients at 36 months: {som_clubs} ({SOM_CLUBS['mid']} + {SOM_CLUBS['flagship']}), linear ramp.")
w(f"- Monthly revenue at 36 months: **{eur(mrr_full)}** ({eur(SOM)} a year). Average price €{blend_price:.1f}, average cost to serve €{blend_cost:.1f}, gross margin **{contrib/blend_price:.0%}**.")
w(f"- Fixed costs: {eur(FIXED_MONTH)} a month [H].")
w(f"- **Break-even: {breakeven_clubs} clubs**, reached in **month {be_month}**.")
w(f"- Lowest cash before break-even: **{eur(-trough)}**.")
w(f"- **Ask: {eur(ask)} for 18 months**, which is the cash low point plus 6 months of fixed costs. Milestones: {breakeven_clubs} paying clubs and an agreement with at least one district.\n")
w("| Month | Clubs | Monthly revenue | Result of the month | Cumulative cash |\n|---|---|---|---|---|")
for t, n, rev, m, c in rows:
    w(f"| {t} | {n:.0f} | {eur(rev)} | {eur(m)} | {eur(c)} |")
w("")

w("## 8. What is still to prove\n")
w("1. That the tool really raises sponsoring: the +30% assumption is the weakest. Test: 3 pilot clubs, before and after one season.")
w("2. That clubs pay €15 or €150 a month: call 10 mid-size clubs this week.")
w("3. That districts pass the tool on: 2 or 3 conversations.")
w("4. The club size data dates from 2011 and 2012 and the national total is a weak source: cross-check with the Ministry of Sports or INJEP.")
w("5. No minibus price was found: the €800 is an assumption.\n")

out = Path(__file__).with_name("numbers.md")
out.write_text("\n".join(md), encoding="utf-8")
print(out)
print(f"TAM {TAM/1e6:.1f} M | SAM {SAM/1e6:.2f} M | SOM {SOM:,.0f} | BE {breakeven_clubs} clubs month {be_month} | trough {trough:,.0f} | ask {ask:,}")
print(f"capture mid {I['capture']:.1%} flagship {P['capture']:.1%} | y1 {I['y1']:.0f} / {P['y1']:.0f} | cost/call {small_cost:.5f}")
