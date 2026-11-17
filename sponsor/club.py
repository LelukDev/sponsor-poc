"""Profil du club de démonstration. Tout est fictif : hypothèses du PoC."""

CLUB = {
    "name": "AS Val de Saône",
    "sport": "football",
    "area": "agglomération lyonnaise",
    "licensees": 320,
    "teams": 14,
    "home_matches_per_season": 60,
    "families": 250,
    "color_main": "#1F4E8C",
    "color_accent": "#F2B705",
}

CLUB_FACTS = (
    f"Club : {CLUB['name']} ({CLUB['sport']}, {CLUB['area']}). "
    f"{CLUB['licensees']} licenciés, {CLUB['teams']} équipes, "
    f"environ {CLUB['home_matches_per_season']} matchs à domicile par saison, "
    f"environ {CLUB['families']} familles touchées. "
    "Supports proposés : panneau de stade, minibus du club, maillot (poitrine)."
)
