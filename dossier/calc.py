"""Calculateur du dossier : une seule source pour tous les chiffres du pitch.

Légende : [S] source citée ; [M] mesuré sur le PoC ; [H] hypothèse à tester.
Lancer : python dossier/calc.py  (écrit dossier/chiffres.md)
"""

import math
from pathlib import Path

# ---------- Entrées ----------
# Typologie des clubs (étude CNOSF reprise en 2025 ; données anciennes, ordres de grandeur) [S]
SHARE = {"proximite": 0.66, "intermediaire": 0.31, "phare": 0.03}
BUDGET = {"proximite": 11_832, "intermediaire": 80_145, "phare": 917_857}
SPONSOR_SHARE = 0.09          # partenariats = 9 % des ressources (CNOSF 2020) [S]
CLUBS_FRANCE = 165_000        # ~165 900 en 2020 (Wikipédia, source faible) [S]
CLUBS_FOOT = 12_000           # réseau FFF d'environ 12 000 clubs amateurs [S]
CLUBS_RUGBY = 1_900           # FFR : plus de 1 900 clubs [S]

UPLIFT = 0.30                 # hausse du sponsoring permise par l'outil, plein régime [H]
ADOPTION = 0.40               # adoption moyenne en année 1 (cours : 30 à 60 %) [H]
NET_RATIO = 0.90              # part nette après coûts d'activation (impression, flocage) [H]

PRICE_MONTH = {"intermediaire": 15, "phare": 150}   # € par mois [H]
COST_SERVE_MONTH = {"intermediaire": 3, "phare": 12}  # hébergement, support, IA [H]
PROPOSALS_MONTH = {"intermediaire": 15, "phare": 60}  # propositions générées / club / mois [H]

SOM_CLUBS = {"intermediaire": 360, "phare": 40}     # clubs gagnés en 36 mois [H]
MONTHS = 36
FIXED_MONTH = 3_000           # 2 indemnités de 1 000 € + outils, juridique, déplacements [H]

# Coût mesuré d'une proposition (PoC, OpenRouter) [M]
TOK_IN, TOK_OUT = 1560, 780   # moyenne de 6 essais réels avec l'inventaire du club
P_SMALL = (0.10, 0.50)        # $ par million de tokens, claude-haiku-5.5
P_LARGE = (2.00, 10.00)       # claude-sonnet-5.5
USD_EUR = 1.0                 # hypothèse de calcul [H]

# Prix des supports de la démo [S/H]
GRID = {"Barnum 300": 300, "Chasubles 350": 350, "Short 400": 400, "Bâche d'entrée 500": 500, "Manche 600": 600, "Barrière principale 600": 600, "Dos 700": 700, "Minibus 800": 800, "Barrières x3 900": 900, "Maillot poitrine 1 500": 1_500}


def eur(x, d=0):
    return f"{x:,.{d}f}".replace(",", " ") + " €"


def call_cost(p):
    return (TOK_IN * p[0] + TOK_OUT * p[1]) / 1e6 * USD_EUR


# ---------- Calculs ----------
res = {}
for seg in ("intermediaire", "phare"):
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

n_inter = round(SHARE["intermediaire"] * CLUBS_FRANCE)
n_phare = round(SHARE["phare"] * CLUBS_FRANCE)
arpa = {s: PRICE_MONTH[s] * 12 for s in PRICE_MONTH}
TAM = n_inter * arpa["intermediaire"] + n_phare * arpa["phare"]

sam_base = CLUBS_FOOT + CLUBS_RUGBY
sam_inter = round(SHARE["intermediaire"] * sam_base)
sam_phare = round(SHARE["phare"] * sam_base)
SAM = sam_inter * arpa["intermediaire"] + sam_phare * arpa["phare"]
sam_clubs = sam_inter + sam_phare

som_clubs = sum(SOM_CLUBS.values())
SOM = sum(SOM_CLUBS[s] * arpa[s] for s in SOM_CLUBS)
som_per_month = som_clubs / MONTHS

mrr_full = sum(SOM_CLUBS[s] * PRICE_MONTH[s] for s in SOM_CLUBS)
cost_full = sum(SOM_CLUBS[s] * COST_SERVE_MONTH[s] for s in SOM_CLUBS)
blend_price = mrr_full / som_clubs
blend_cost = cost_full / som_clubs
contrib = blend_price - blend_cost
breakeven_clubs = math.ceil(FIXED_MONTH / contrib)

# Simulation mensuelle : montée linéaire jusqu'au SOM au mois 36
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

# IA à l'échelle du SOM
calls = sum(SOM_CLUBS[s] * PROPOSALS_MONTH[s] for s in SOM_CLUBS)
small_cost, large_cost = call_cost(P_SMALL), call_cost(P_LARGE)
ai_small, ai_large = calls * small_cost, calls * large_cost

# ---------- Choix du use case : méthode du cours ----------
# Impact = hausse du budget du club en % ; échelle ICE : >=2,5 % -> 8 ; 2-2,5 % -> 7 ; 1-2 % -> 5
usecases = [
    # nom, pay, switch, degrade, preuve
    ("Propositions de sponsoring + maquettes", 1, 0, 1, "sponsoring = 9 % des ressources ; 45 % des clubs peinent à couvrir leurs dépenses"),
    ("Convocations / dispos depuis WhatsApp", 0, 0, 1, "des outils gratuits existent (ClubPal, Kalisport Core)"),
    ("Relances de cotisations", 1, 0, 1, "cotisations = 68 % des ressources ; outils déjà payés (19 à 49 €/mois)"),
    ("Dossiers de subvention", 1, 0, 1, "subventions = 16 % des ressources ; rédaction longue pour des bénévoles"),
    ("Comptes rendus de match (site, réseaux)", 0, 0, 0, "aucun chiffre ne bouge si on le retire"),
    ("Planning des bénévoles (buvette, tournois)", 0, 0, 1, "gain de temps sans euro mesurable"),
]
# RICE pour les must-have : (nom, R par trimestre, I, C, E en mois-personne)
rice = [
    ("Relances de cotisations", 150, 1, 0.8, 3),
    ("Propositions de sponsoring + maquettes", 15 * 3, 3, 0.5, 2),
    ("Dossiers de subvention", 1.5, 3, 0.5, 3),
]
rice = sorted([(n, r, i, c, e, r * i * c / e) for (n, r, i, c, e) in rice], key=lambda x: -x[5])
# ICE : impact (hausse de budget), confiance, facilité
ice = [
    ("Propositions de sponsoring + maquettes", 8, 5, 6, "+2,7 % du budget (30 % de 9 %)"),
    ("Relances de cotisations", 5, 8, 7, "+1,4 % du budget (2 pts de 68 %)"),
    ("Dossiers de subvention", 7, 5, 4, "+2,4 % du budget (15 % de 16 %)"),
]


def quad(i, e):
    if i > 5.5 and e > 5.5:
        return "Quick win"
    if i > 5.5:
        return "Big bet"
    if e > 5.5:
        return "Fill-in (acheter du tout fait)"
    return "Money pit"


# ---------- Rapport ----------
I, P = res["intermediaire"], res["phare"]
md = []
w = md.append
w("# Dossier de chiffres : une seule source pour tout le pitch\n")
w("Légende : **[S]** source citée ; **[M]** mesuré sur le PoC ; **[H]** hypothèse à tester auprès de vrais clubs.\n")
w("Généré par `dossier/calc.py`. Changer une hypothèse en tête du fichier, relancer, et tous les chiffres suivent.\n")

w("## 1. Fiche de faits : le marché des clubs sportifs amateurs\n")
w("| Fait | Valeur | Statut |\n|---|---|---|")
w(f"| Clubs en France | ~{CLUBS_FRANCE:,} | [S] source faible (Wikipédia 2020) |".replace(",", " "))
w(f"| Clubs intermédiaires | {SHARE['intermediaire']:.0%} des clubs, budget moyen {eur(BUDGET['intermediaire'])} | [S] CNOSF, données anciennes |")
w(f"| Clubs phares | {SHARE['phare']:.0%} des clubs, budget moyen {eur(BUDGET['phare'])} | [S] idem |")
w(f"| Clubs de proximité | {SHARE['proximite']:.0%} des clubs, budget moyen {eur(BUDGET['proximite'])} | [S] idem, **exclus** (trop petit pour payer) |")
w(f"| Part des partenariats dans les ressources | {SPONSOR_SHARE:.0%} | [S] CNOSF 2020 |")
w(f"| Prix d'un logiciel de gestion de club | 19 à 49 € / mois | [S] comparateurs 2026 |")
w(f"| Prix des supports | panneau 500-750 € HT ; maillot 1 500-5 000 € / saison ; minibus : aucune donnée | [S] une plaquette de rugby et un blog d'agence |")
w(f"| Grille de la démo (10 emplacements, € par saison) | {', '.join(GRID)} | [H] bas de fourchette |\n")

w("## 2. Choix du use case (S1)\n")
w("**Test des 3 questions** (payer, changer de concurrent, dégrader un chiffre) : 2 ou 3 oui = must-have.\n")
w("| Use case | Pay | Switch | Degrade | Total | Fait |\n|---|---|---|---|---|---|")
for n, p, s, d, f in usecases:
    t = p + s + d
    w(f"| {n} | {'oui' if p else 'non'} | {'oui' if s else 'non'} | {'oui' if d else 'non'} | {t}/3 {'**must-have**' if t >= 2 else 'nice-to-have'} | {f} |")
w("\n**RICE** (must-have seulement) : R = événements par trimestre, I = 3 massif / 1 moyen, C = confiance, E = mois-personne [H].\n")
w("| Use case | R | I | C | E | RICE |\n|---|---|---|---|---|---|")
for n, r, i, c, e, sc in rice:
    w(f"| {n} | {r:g} | {i} | {c:.0%} | {e} | {sc:.1f} |")
w("\n**ICE et grille impact-facilité** (impact = hausse du budget du club ; seuil 5,5).\n")
w("| Use case | Impact | Confiance | Facilité | ICE | Quadrant | Calcul de l'impact |\n|---|---|---|---|---|---|---|")
for n, i, c, e, note in sorted(ice, key=lambda x: -(x[1] * x[2] * x[3])):
    w(f"| {n} | {i} | {c} | {e} | {i*c*e} | {quad(i, e)} | {note} |")
w("\n**Lecture honnête.** Les relances de cotisations gagnent au RICE et à l'ICE grâce au volume et à la confiance, mais leur impact reste sous le seuil : "
  "des outils bon marché existent déjà, donc c'est un « fill-in » à acheter. Les propositions de sponsoring sont le seul use case à la fois "
  "must-have, à fort impact et facile : un quick win. Toutes les notes de confiance sont des hypothèses : la première action est d'appeler 10 clubs pour les tester.\n")

w("## 3. ROI : hausse du sponsoring (S1)\n")
w("Archétype : **revenue uplift**. Mécanisme nommé : *le club présente plus de propositions personnalisées et signe plus de sponsors locaux.*\n")
w("| | Club intermédiaire | Club phare |\n|---|---|---|")
w(f"| Budget moyen [S] | {eur(BUDGET['intermediaire'])} | {eur(BUDGET['phare'])} |")
w(f"| Sponsoring actuel (9 %) | {eur(I['base'])} | {eur(P['base'])} |")
w(f"| Hausse possible à plein régime ({UPLIFT:.0%}) [H] | {eur(I['full'])} | {eur(P['full'])} |")
w(f"| Gain net année 1 (adoption {ADOPTION:.0%}, {NET_RATIO:.0%} net) [H] | **{eur(I['y1'])}** | **{eur(P['y1'])}** |")
w(f"| Valeur par mois | {eur(I['y1_month'], 1)} | {eur(P['y1_month'], 1)} |")
w(f"| Prix de l'outil par an | {eur(I['price_year'])} | {eur(P['price_year'])} |")
w(f"| ROI année 1 | {I['roi']:.0%} | {P['roi']:.0%} |")
w(f"\n**Phrase du cours :** « En année 1, un club intermédiaire signe pour {eur(I['y1'])} de sponsoring net en plus (hausse de {UPLIFT:.0%} du sponsoring, adoption de {ADOPTION:.0%}) ; un club phare, {eur(P['y1'])}. »\n")
w("**Sensibilité à l'adoption :**\n")
w("| Adoption | Gain net intermédiaire | Gain net phare | Prix en % de la valeur (inter. / phare) |\n|---|---|---|---|")
for a in (0.30, 0.40, 0.50, 0.60):
    gi = I["full"] * a * NET_RATIO
    gp = P["full"] * a * NET_RATIO
    w(f"| {a:.0%} | {eur(gi)} | {eur(gp)} | {PRICE_MONTH['intermediaire']/(gi/12):.0%} / {PRICE_MONTH['phare']/(gp/12):.0%} |")
w("")

w("## 4. Marché bottom-up (S4)\n")
w("Client qui signe : **le club** (le trésorier ou le président). Deux plans : Club intermédiaire et Club phare.\n")
w("| | Clubs | × ARPA | = Marché |\n|---|---|---|---|")
w(f"| **TAM** : clubs intermédiaires + phares en France | {n_inter:,} + {n_phare:,} | {eur(arpa['intermediaire'])} / {eur(arpa['phare'])} | **{eur(TAM/1e6, 1).replace(' €', '')} M€** |".replace(",", " "))
w(f"| **SAM** : football + rugby (démo et réseaux de districts) | {sam_inter:,} + {sam_phare:,} = {sam_clubs:,} | idem | **{eur(SAM/1e6, 2).replace(' €', '')} M€** |".replace(",", " "))
w(f"| **SOM** : 3 ans | {SOM_CLUBS['intermediaire']} + {SOM_CLUBS['phare']} = {som_clubs} clubs ({som_clubs/sam_clubs:.1%} du SAM) | idem | **{eur(SOM)} ARR** |")
w(f"\nContrôle : {som_clubs} clubs en {MONTHS} mois = **{som_per_month:.1f} nouveaux clubs par mois**. Qui les signe ? Les districts et les ligues, qui relaient l'outil à leurs clubs (partenariat à négocier [H]), plus de l'appel direct.\n")
w("Les petits clubs de proximité sont exclus du TAM : leur sponsoring (9 % de ~11 800 €, soit ~1 060 €) laisse moins de 100 € de gain net par an.\n")

w("## 5. Modèle économique et prix (S4)\n")
w("Modèle : **abonnement SaaS par club**, deux plans selon la taille (le prix suit la valeur créée, qui augmente avec le budget).\n")
w("| | Club intermédiaire | Club phare |\n|---|---|---|")
w(f"| Prix | **{PRICE_MONTH['intermediaire']} € / mois** | **{PRICE_MONTH['phare']} € / mois** |")
w(f"| Part de la valeur captée | {I['capture']:.0%} | {P['capture']:.0%} |")
w(f"| Coût de service [H] | {COST_SERVE_MONTH['intermediaire']} € / mois | {COST_SERVE_MONTH['phare']} € / mois |")
w(f"| Marge brute | {I['margin']:.0%} | {P['margin']:.0%} |")
w(f"\n**Phrase du cours :** « {PRICE_MONTH['intermediaire']} € par mois, soit {I['capture']:.0%} des {eur(I['y1_month'])} de valeur mensuelle créée, pour un coût de service de {COST_SERVE_MONTH['intermediaire']} € ; {PRICE_MONTH['phare']} € par mois pour un club phare, soit {P['capture']:.0%} de {eur(P['y1_month'])}. »\n")
w("Le prix reste sous les 19 à 49 € d'un logiciel de gestion : l'outil est un complément léger, pas un remplaçant. À 10-30 % de la valeur, il suit la règle du cours.\n")
w("**Ne pas confondre deux prix.** Les 500 / 800 / 1 500 € de la démo sont ce que **le club** facture **au commerce sponsor**, par saison. "
  "Les 15 et 150 € par mois sont ce que **nous** facturons **au club**.\n")
w("## 5 bis. Traction (slide 6) : ce qu'on peut dire honnêtement\n")
w("- Aucun client à ce jour : ne pas en prétendre.")
w("- Prouvé : un PoC en ligne qui produit une proposition en 4 à 5 s pour environ 0,0006 $, sur n'importe quel commerce choisi par le jury.")
w("- Plan de pilote chiffré : 3 clubs intermédiaires, 1 saison, mesure avant/après du sponsoring signé (hypothèse +30 %). Succès : au moins +15 % ou 2 nouveaux sponsors par club.")
w("- À obtenir avant la soutenance si possible : 10 appels à des clubs, 2 ou 3 retours à citer, et une lettre d'intention d'un club ou d'un district. Seulement des retours réels.\n")

w("## 6. Coût de l'IA, mesuré puis projeté (S3 et S5)\n")
w(f"- Une proposition = 1 appel (le modèle lit l'inventaire du club et choisit les emplacements), {TOK_IN} tokens en entrée, {TOK_OUT} en sortie **[M]**.")
w("- Les photos réalistes sont générées une seule fois (7 images, environ 0,47 $ au total) ; la pose du logo se fait ensuite par code, sans coût ni appel réseau.")
w(f"- Petit modèle (claude-haiku-5.5, 0,10 / 0,50 $ par million) : **{small_cost:.5f} $** par proposition ; temps de rédaction mesuré : 3,5 à 4,5 s.")
w(f"- Grand modèle (claude-sonnet-5.5, 2 / 10 $ par million) : {large_cost:.5f} $ par proposition.")
calls_txt = f"{calls:,}".replace(",", " ")
w(f"- À l'échelle du SOM : {calls_txt} propositions par mois, soit **{ai_small:.1f} $ par mois** avec le petit modèle ({ai_small/mrr_full:.2%} du chiffre d'affaires mensuel), {ai_large:.0f} $ avec le grand modèle ({ai_large/mrr_full:.1%}).")
w("- Le coût de l'IA n'est donc pas le sujet : l'hébergement et le support dominent. Le temps de rédaction mesuré (3,5 à 4,5 s) dépasse la cible de 3 s du cours ; piste : afficher le texte au fil de l'eau.\n")

w("## 7. Financiers (S4 et S5)\n")
w(f"- Clients à 36 mois : {som_clubs} ({SOM_CLUBS['intermediaire']} + {SOM_CLUBS['phare']}), montée linéaire.")
w(f"- Revenu mensuel à 36 mois : **{eur(mrr_full)}** ({eur(SOM)} ARR). Prix moyen {blend_price:.1f} €, coût de service moyen {blend_cost:.1f} €, marge brute **{contrib/blend_price:.0%}**.")
w(f"- Charges fixes : {eur(FIXED_MONTH)} par mois [H].")
w(f"- **Seuil de rentabilité : {breakeven_clubs} clubs**, atteint au **mois {be_month}**.")
w(f"- Trésorerie la plus basse avant rentabilité : **{eur(-trough)}**.")
w(f"- **Demande : {eur(ask)} pour 18 mois**, soit le creux de trésorerie plus 6 mois de charges de marge. Jalon : {breakeven_clubs} clubs payants (dont une dizaine de plans phares) et un accord avec au moins un district.\n")
w("| Mois | Clubs | Revenu mensuel | Résultat du mois | Trésorerie cumulée |\n|---|---|---|---|---|")
for t, n, rev, m, c in rows:
    w(f"| {t} | {n:.0f} | {eur(rev)} | {eur(m)} | {eur(c)} |")
w("")

w("## 8. Ce qui reste à prouver\n")
w("1. Que l'outil fait vraiment monter le sponsoring : l'hypothèse +30 % est la plus fragile. Test : 3 clubs pilotes, avant/après sur une saison.")
w("2. Que des clubs paient 15 ou 150 € par mois : appeler 10 clubs intermédiaires cette semaine.")
w("3. Que les districts relaient l'outil : 2 ou 3 conversations.")
w("4. Les données de répartition des clubs datent de 2011-2012 et le total national est une source faible : à recouper avec le ministère des Sports ou l'INJEP.")
w("5. Aucun tarif de minibus trouvé : le prix de 800 € est une hypothèse.\n")

import re

out = Path(__file__).with_name("chiffres.md")
text = "\n".join(md)
text = re.sub(r"(\d)\.(\d)", r"\1,\2", text)  # décimales à la française
text = text.replace("haiku-5,5", "haiku-5.5").replace("sonnet-5,5", "sonnet-5.5")
out.write_text(text, encoding="utf-8")
print(out)
print(f"TAM {TAM/1e6:.1f} M | SAM {SAM/1e6:.2f} M | SOM {SOM:,.0f} | BE {breakeven_clubs} clubs mois {be_month} | trough {trough:,.0f} | ask {ask:,}")
print(f"capture inter {I['capture']:.1%} phare {P['capture']:.1%} | y1 {I['y1']:.0f} / {P['y1']:.0f} | cost/call {small_cost:.5f}")
