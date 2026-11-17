"""Profil du club de démonstration : emplacements, état de l'inventaire, besoins. Tout est fictif."""

from dataclasses import dataclass

CLUB = {
    "name": "AS Val de Saône",
    "sport": "football",
    "area": "agglomération lyonnaise",
    "licensees": 320,
    "teams": 14,
    "home_matches_per_season": 60,
    "families": 250,
}

SECTORS = [
    "alimentation",
    "restauration",
    "automobile",
    "banque-assurance",
    "immobilier-bâtiment",
    "santé-bien-être",
    "commerce-équipement",
    "services-entreprises",
    "énergie-télécom",
    "sport-loisirs",
    "autre",
]


@dataclass(frozen=True)
class Slot:
    id: str
    label: str
    price: int  # par saison, grille d'exemple
    scene: str
    zones: tuple
    where: str  # où le support est vu, pour l'IA
    crop: bool = False  # gros plan pour les petits supports


SLOTS = (
    Slot("poitrine", "Maillot, poitrine", 1500, "kit_front", (0,), "porté par tous les joueurs, photos de match, réseaux du club"),
    Slot("dos", "Maillot, dos (au-dessus du numéro)", 700, "jersey_back", (0,), "vu par les adversaires et les spectateurs derrière les joueurs"),
    Slot("manche", "Maillot, manche", 600, "kit_front", (2,), "visible sur toutes les photos de profil", True),
    Slot("short", "Short", 400, "kit_front", (1,), "visible sur les photos d'équipe", True),
    Slot("barriere_a", "Barrière principale du terrain", 600, "pitch_boards", (0,), "face à la tribune, vue de tous les spectateurs"),
    Slot("barrieres_b", "Barrières du terrain (3 panneaux)", 900, "pitch_boards", (1, 2, 3), "le long de la touche, vues par les familles"),
    Slot("minibus", "Minibus du club", 800, "minibus", (0,), "circule dans toute l'agglomération à chaque déplacement"),
    Slot("banderole", "Bâche de l'entrée du stade", 500, "banner_gate", (0,), "vue par chaque visiteur à son arrivée"),
    Slot("chasubles", "Chasubles d'entraînement (lot)", 350, "bibs", (0, 1, 2), "portées aux entraînements de l'école de foot, vues des parents"),
    Slot("barnum", "Barnum de la buvette", 300, "tent", (0,), "au centre des tournois et des jours de match"),
)
SLOT_BY_ID = {s.id: s for s in SLOTS}

DEFAULT_TAKEN = {
    "poitrine": ("Groupe Lacroix Immobilier", "immobilier-bâtiment"),
    "barriere_a": ("Assurances Mercier", "banque-assurance"),
    "barnum": ("Pizzeria Da Marco", "restauration"),
}

DEFAULT_NEEDS = (
    "Renouveler le minibus du club (devis : 9 000 €). "
    "Équiper l'école de foot en chasubles pour septembre. "
    "Financer le tournoi des U13 en mai."
)
DEFAULT_GOAL = 12_000


def default_inventory() -> list[dict]:
    rows = []
    for s in SLOTS:
        taken = DEFAULT_TAKEN.get(s.id)
        rows.append(
            {
                "id": s.id,
                "Emplacement": s.label,
                "Prix (€)": s.price,
                "Statut": "pris" if taken else "libre",
                "Sponsor actuel": taken[0] if taken else "",
                "Secteur": taken[1] if taken else "",
            }
        )
    return rows


def summarize(inventory: list[dict], goal: int) -> dict:
    taken = [r for r in inventory if r["Statut"] == "pris"]
    free = [r for r in inventory if r["Statut"] != "pris"]
    signed = sum(int(r["Prix (€)"]) for r in taken)
    free_value = sum(int(r["Prix (€)"]) for r in free)
    return {
        "signed": signed,
        "remaining": max(goal - signed, 0),
        "free_value": free_value,
        "free": free,
        "taken": taken,
        "gap": max(goal - signed - free_value, 0),
    }


def club_facts(inventory: list[dict], needs: str, goal: int) -> str:
    s = summarize(inventory, goal)
    free_lines = "\n".join(
        f"- {r['id']} : {r['Emplacement']} ({r['Prix (€)']} € par saison) ; {SLOT_BY_ID[r['id']].where}" for r in s["free"]
    ) or "- aucun"
    taken_lines = "\n".join(
        f"- {r['id']} : {r['Emplacement']}, déjà pris par {r['Sponsor actuel'] or 'un sponsor'} (secteur : {r['Secteur'] or 'inconnu'})"
        for r in s["taken"]
    ) or "- aucun"
    return (
        f"Club : {CLUB['name']} ({CLUB['sport']}, {CLUB['area']}). {CLUB['licensees']} licenciés, {CLUB['teams']} équipes, "
        f"environ {CLUB['home_matches_per_season']} matchs à domicile par saison, environ {CLUB['families']} familles touchées.\n"
        f"Besoins déclarés du club : {needs.strip() or 'non précisés'}\n"
        f"Objectif de collecte de la saison : {goal} € ; déjà signé : {s['signed']} € ; reste à lever : {s['remaining']} €.\n"
        f"Emplacements LIBRES :\n{free_lines}\nEmplacements DÉJÀ PRIS :\n{taken_lines}"
    )
