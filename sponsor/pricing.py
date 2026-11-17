"""Grille de prix : calcul déterministe, jamais produit par l'IA."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Package:
    key: str
    tier: str
    support: str
    price_eur: int


PACKAGES = (
    Package("bronze", "Bronze", "Panneau de stade", 500),
    Package("argent", "Argent", "Minibus du club", 800),
    Package("or", "Or", "Maillot (poitrine)", 1500),
)


def format_price(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " €"


def total_if_all(packages=PACKAGES) -> int:
    return sum(p.price_eur for p in packages)
