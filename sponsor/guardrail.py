"""Garde-fou appliqué avant tout appel à l'IA."""

import re
import unicodedata
from dataclasses import dataclass

BLOCKED = {
    "alcool": [
        "bar", "vin", "vins", "biere", "bieres", "brasserie", "whisky", "rhum",
        "spiritueux", "alcool", "cognac", "vodka", "pub", "cave a vins", "caviste",
    ],
    "tabac et vapotage": ["tabac", "cigarette", "cigarettes", "vape", "vapotage", "cigare", "chicha"],
    "jeux d'argent": ["casino", "pmu", "paris sportifs", "pari sportif", "poker", "loto"],
    "contenu sensible": ["escort", "sex shop", "sexshop", "armes", "arme"],
}

GENERIC = {
    "commerce", "magasin", "boutique", "entreprise", "societe", "test", "asdf",
    "azerty", "xxx", "machin", "truc",
}


@dataclass(frozen=True)
class Verdict:
    status: str  # "ok", "blocked" ou "unclear"
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
        return Verdict(
            "unclear",
            message="Le nom du commerce est trop vague. Donnez son nom réel et, si possible, son activité.",
        )
    for category, words in BLOCKED.items():
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", norm_all):
                return Verdict(
                    "blocked",
                    category=category,
                    message=(
                        f"Ce commerce relève de la catégorie « {category} » : la publicité y est "
                        "encadrée ou interdite dans le sport. Proposition non générée. "
                        "À valider avec la fédération ; cible alternative conseillée : un commerce de proximité "
                        "(boulangerie, garage, pharmacie, restauration)."
                    ),
                )
    return Verdict("ok")
