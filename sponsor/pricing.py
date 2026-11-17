"""Price formatting. Prices come from the club inventory (sponsor/club.py), never from the AI."""


def format_price(value: int) -> str:
    return f"€{int(value):,}"
