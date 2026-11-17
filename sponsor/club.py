"""Demo club profile: slots, inventory state, needs. Everything here is fictional."""

from dataclasses import dataclass

CLUB = {
    "name": "AS Val de Saône",
    "sport": "football",
    "area": "Lyon area",
    "licensees": 320,
    "teams": 14,
    "home_matches_per_season": 60,
    "families": 250,
}

SECTORS = [
    "food",
    "restaurants",
    "automotive",
    "banking and insurance",
    "real estate and construction",
    "health and wellness",
    "retail and equipment",
    "business services",
    "energy and telecom",
    "sport and leisure",
    "other",
]

STATUS_FREE, STATUS_TAKEN = "free", "taken"


@dataclass(frozen=True)
class Slot:
    id: str
    label: str
    price: int  # per season, example grid
    scene: str
    zones: tuple
    where: str  # where the slot is seen, used by the AI
    crop: bool = False  # close-up for small slots


SLOTS = (
    Slot("poitrine", "Jersey, chest", 1500, "kit_front", (0,), "worn by every player, match photos, club social media"),
    Slot("dos", "Jersey, back (above the number)", 700, "jersey_back", (0,), "seen by opponents and by spectators behind the players"),
    Slot("manche", "Jersey, sleeve", 600, "kit_front", (2,), "visible on every profile photo", True),
    Slot("short", "Shorts", 400, "kit_front", (1,), "visible on team photos", True),
    Slot("barriere_a", "Main pitch board", 600, "pitch_boards", (0,), "in front of the stand, seen by every spectator"),
    Slot("barrieres_b", "Pitch boards (3 panels)", 900, "pitch_boards", (1, 2, 3), "along the touchline, seen by families"),
    Slot("minibus", "Club minibus", 800, "minibus", (0,), "drives around the area at every away game"),
    Slot("banderole", "Stadium entrance banner", 500, "banner_gate", (0,), "seen by every visitor when they arrive"),
    Slot("chasubles", "Training bibs (set)", 350, "bibs", (0, 1, 2), "worn at football school training, seen by parents"),
    Slot("barnum", "Refreshment tent", 300, "tent", (0,), "at the centre of tournaments and match days"),
)
SLOT_BY_ID = {s.id: s for s in SLOTS}

DEFAULT_TAKEN = {
    "poitrine": ("Lacroix Real Estate", "real estate and construction"),
    "barriere_a": ("Mercier Insurance", "banking and insurance"),
    "barnum": ("Da Marco Pizzeria", "restaurants"),
}

DEFAULT_NEEDS = (
    "Replace the club minibus (quote: €9,000). "
    "Equip the football school with training bibs for September. "
    "Fund the U13 tournament in May."
)
DEFAULT_GOAL = 12_000

COLUMNS = ("Slot", "Price (€)", "Status", "Current sponsor", "Sector")


def default_inventory() -> list[dict]:
    rows = []
    for s in SLOTS:
        taken = DEFAULT_TAKEN.get(s.id)
        rows.append(
            {
                "id": s.id,
                "Slot": s.label,
                "Price (€)": s.price,
                "Status": STATUS_TAKEN if taken else STATUS_FREE,
                "Current sponsor": taken[0] if taken else "",
                "Sector": taken[1] if taken else "",
            }
        )
    return rows


def summarize(inventory: list[dict], goal: int) -> dict:
    taken = [r for r in inventory if r["Status"] == STATUS_TAKEN]
    free = [r for r in inventory if r["Status"] != STATUS_TAKEN]
    signed = sum(int(r["Price (€)"]) for r in taken)
    free_value = sum(int(r["Price (€)"]) for r in free)
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
        f"- {r['id']}: {r['Slot']} (€{r['Price (€)']} per season); {SLOT_BY_ID[r['id']].where}" for r in s["free"]
    ) or "- none"
    taken_lines = "\n".join(
        f"- {r['id']}: {r['Slot']}, already taken by {r['Current sponsor'] or 'a sponsor'} (sector: {r['Sector'] or 'unknown'})"
        for r in s["taken"]
    ) or "- none"
    return (
        f"Club: {CLUB['name']} ({CLUB['sport']}, {CLUB['area']}). {CLUB['licensees']} members, {CLUB['teams']} teams, "
        f"about {CLUB['home_matches_per_season']} home matches per season, about {CLUB['families']} families reached.\n"
        f"Declared needs of the club: {needs.strip() or 'not given'}\n"
        f"Fundraising goal for the season: €{goal}; already signed: €{s['signed']}; left to raise: €{s['remaining']}.\n"
        f"FREE slots:\n{free_lines}\nTAKEN slots:\n{taken_lines}"
    )


def _text(value) -> str:
    return "" if value is None or value != value else str(value).strip()


def inventory_from_frame(df) -> list[dict]:
    """Turn the edited table into a clean inventory. Empty cells, bad statuses and unknown sectors are fixed here."""
    rows = []
    for slot, rec in zip(SLOTS, df.to_dict("records")):
        price = rec.get("Price (€)")
        try:
            price = 0 if price is None or price != price else max(0, int(price))
        except (TypeError, ValueError):
            price = slot.price
        status = _text(rec.get("Status"))
        sector = _text(rec.get("Sector"))
        rows.append(
            {
                "id": slot.id,
                "Slot": slot.label,
                "Price (€)": price,
                "Status": status if status in (STATUS_FREE, STATUS_TAKEN) else STATUS_FREE,
                "Current sponsor": _text(rec.get("Current sponsor")),
                "Sector": sector if sector in SECTORS else "",
            }
        )
    return rows
