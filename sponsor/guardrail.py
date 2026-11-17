"""Guardrail applied before any call to the AI."""

import re
import unicodedata
from dataclasses import dataclass

BLOCKED = {
    "alcohol": [
        "bar", "pub", "wine", "wines", "beer", "beers", "brewery", "whisky", "whiskey", "rum", "vodka", "liquor", "spirits",
        "alcohol", "cognac", "cocktail",
        "vin", "vins", "biere", "bieres", "brasserie", "spiritueux", "alcool", "caviste",
    ],
    "tobacco and vaping": [
        "tobacco", "cigarette", "cigarettes", "cigar", "vape", "vaping", "hookah", "shisha",
        "tabac", "vapotage", "cigare", "chicha",
    ],
    "gambling": ["casino", "pmu", "betting", "bookmaker", "poker", "lottery", "loto", "paris sportifs", "pari sportif"],
    "sensitive content": ["escort", "sex shop", "sexshop", "weapons", "weapon", "armes", "arme"],
}

GENERIC = {"business", "shop", "store", "company", "test", "asdf", "qwerty", "azerty", "xxx", "commerce", "magasin", "boutique"}


@dataclass(frozen=True)
class Verdict:
    status: str  # "ok", "blocked" or "unclear"
    category: str = ""
    message: str = ""


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def check_business(name: str, sector_hint: str = "") -> Verdict:
    norm_name = _normalize(name)
    norm_all = _normalize(f"{name} {sector_hint}")
    if len(norm_name) < 3 or norm_name in GENERIC:
        return Verdict("unclear", message="The business name is too vague. Enter its real name and, if you can, what it does.")
    for category, words in BLOCKED.items():
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", norm_all):
                return Verdict(
                    "blocked",
                    category=category,
                    message=(
                        f"This business is in the category \"{category}\": advertising is restricted or banned in sport. "
                        "No offer was generated. Please check with the federation. "
                        "Better targets: a local shop such as a bakery, a garage, a pharmacy or a restaurant."
                    ),
                )
    return Verdict("ok")
