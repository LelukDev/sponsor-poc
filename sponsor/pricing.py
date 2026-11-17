"""Mise en forme des prix. Les prix eux-mêmes viennent de l'inventaire du club (sponsor/club.py), jamais de l'IA."""


def format_price(value: int) -> str:
    return f"{int(value):,}".replace(",", " ") + " €"
