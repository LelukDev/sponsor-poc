"""Maquettes SVG : le logo du commerce posé sur un maillot, un minibus et un panneau."""

import base64
from xml.sax.saxutils import escape

from .club import CLUB

ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
MAX_LOGO_BYTES = 2 * 1024 * 1024


def logo_data_uri(data: bytes, mime: str) -> str:
    if mime not in ALLOWED_MIME:
        raise ValueError("Format de logo non pris en charge (png, jpg, webp, svg).")
    if len(data) > MAX_LOGO_BYTES:
        raise ValueError("Logo trop lourd (2 Mo maximum).")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _patch(x: int, y: int, w: int, h: int, name: str, logo_uri: str | None) -> str:
    """Pastille blanche qui porte le logo, ou le nom du commerce à défaut de logo."""
    rect = (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        'fill="#FFFFFF" stroke="#C9CED6" stroke-width="1"/>'
    )
    if logo_uri:
        pad = 6
        return rect + (
            f'<image href="{logo_uri}" x="{x + pad}" y="{y + pad}" '
            f'width="{w - 2 * pad}" height="{h - 2 * pad}" preserveAspectRatio="xMidYMid meet"/>'
        )
    label = name.strip()[:18]
    size = max(9, min(20, int((w - 12) / max(1, len(label) * 0.6))))
    return rect + (
        f'<text x="{x + w / 2}" y="{y + h / 2}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="{size}" font-weight="700" '
        f'fill="#1B2430">{escape(label)}</text>'
    )


CANVAS_W, CANVAS_H = 360, 262


def _wrap(view_w: int, view_h: int, body: str) -> str:
    """Centre chaque dessin dans une toile de même taille, pour des cartes alignées."""
    ox, oy = (CANVAS_W - view_w) / 2, (CANVAS_H - view_h) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
        f'width="{CANVAS_W}" height="{CANVAS_H}">'
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#F5F6F8"/>'
        f'<g transform="translate({ox} {oy})">{body}</g></svg>'
    )


def jersey_svg(name: str, logo_uri: str | None = None) -> str:
    main, accent = CLUB["color_main"], CLUB["color_accent"]
    body = (
        f'<path d="M70 24 L100 10 Q120 34 140 10 L170 24 L224 64 L198 104 L178 90 L178 244 '
        f'L62 244 L62 90 L42 104 L16 64 Z" fill="{main}" stroke="#16365F" stroke-width="2"/>'
        f'<path d="M100 10 Q120 34 140 10" fill="none" stroke="{accent}" stroke-width="5"/>'
        f'<rect x="62" y="232" width="116" height="12" fill="{accent}"/>'
        + _patch(82, 100, 76, 58, name, logo_uri)
        + f'<text x="120" y="190" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" '
        f'font-size="13" font-weight="700" fill="#FFFFFF">{escape(CLUB["name"])}</text>'
    )
    return _wrap(240, 262, body)


def van_svg(name: str, logo_uri: str | None = None) -> str:
    main, accent = CLUB["color_main"], CLUB["color_accent"]
    body = (
        f'<rect x="20" y="50" width="240" height="96" rx="8" fill="{main}" stroke="#16365F" stroke-width="2"/>'
        f'<path d="M260 70 L310 70 L338 108 L338 146 L260 146 Z" fill="{main}" stroke="#16365F" stroke-width="2"/>'
        '<path d="M268 78 L304 78 L324 108 L268 108 Z" fill="#DCE8F5" stroke="#16365F" stroke-width="1.5"/>'
        f'<rect x="20" y="124" width="240" height="12" fill="{accent}"/>'
        + _patch(62, 66, 156, 50, name, logo_uri)
        + f'<text x="160" y="130" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" '
        f'fill="#16365F">{escape(CLUB["name"])}</text>'
        '<circle cx="82" cy="156" r="18" fill="#2B2F36"/><circle cx="82" cy="156" r="7" fill="#B8BDC6"/>'
        '<circle cx="288" cy="156" r="18" fill="#2B2F36"/><circle cx="288" cy="156" r="7" fill="#B8BDC6"/>'
    )
    return _wrap(360, 190, body)


def panel_svg(name: str, logo_uri: str | None = None) -> str:
    main = CLUB["color_main"]
    body = (
        '<rect x="0" y="160" width="360" height="40" fill="#8FB872"/>'
        '<rect x="70" y="120" width="10" height="46" fill="#6B7280"/>'
        '<rect x="280" y="120" width="10" height="46" fill="#6B7280"/>'
        '<rect x="30" y="30" width="300" height="100" rx="4" fill="#FFFFFF" stroke="#16365F" stroke-width="2"/>'
        f'<rect x="30" y="30" width="300" height="22" rx="4" fill="{main}"/>'
        f'<text x="180" y="42" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">'
        f'{escape(CLUB["name"])} · Stade municipal</text>'
        + _patch(100, 60, 160, 56, name, logo_uri)
    )
    return _wrap(360, 200, body)


MOCKUPS = {"bronze": panel_svg, "argent": van_svg, "or": jersey_svg}
