"""Prépare les scènes : détecte les zones magenta, calcule leurs quadrilatères, efface le magenta.

Entrée : assets/scenes/raw/*.png (photos générées avec des repères magenta)
Sortie : assets/scenes/<scène>.jpg (plaque propre) et assets/scenes/zones.json
Outil de préparation, lancé une fois ; l'application n'en a pas besoin à l'exécution.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "assets" / "scenes" / "raw"
OUT = ROOT / "assets" / "scenes"

# mode : "fabric" = on prolonge le tissu autour ; "paint" = support blanc peint (panneau, bâche, carrosserie)
# order : "area" (plus grande d'abord) ou "x" (de gauche à droite)
SCENES = {
    "kit_front": {"mode": "fabric", "order": "area"},
    "jersey_back": {"mode": "fabric", "order": "x"},
    "bibs": {"mode": "fabric", "order": "x"},
    "pitch_boards": {"mode": "paint", "order": "area"},
    "minibus": {"mode": "paint", "order": "x"},
    "banner_gate": {"mode": "paint", "order": "x"},
    "tent": {"mode": "paint", "order": "x"},
}


def magenta_mask(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return ((np.minimum(r, b) - g) > 90) & (np.minimum(r, b) > 120)


def quad_of(ys: np.ndarray, xs: np.ndarray) -> list[list[float]]:
    s, d = xs + ys, xs - ys
    tl, br = np.argmin(s), np.argmax(s)
    tr, bl = np.argmax(d), np.argmin(d)
    return [[float(xs[i]), float(ys[i])] for i in (tl, tr, br, bl)]


def expand(quad, px=1.5):
    cx = sum(p[0] for p in quad) / 4
    cy = sum(p[1] for p in quad) / 4
    out = []
    for x, y in quad:
        dx, dy = x - cx, y - cy
        n = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        out.append([x + dx / n * px, y + dy / n * px])
    return out


def fill_fabric(img: np.ndarray, zone: np.ndarray, others: np.ndarray, rng) -> None:
    big = ndi.binary_dilation(zone, iterations=7)
    ring = ndi.binary_dilation(big, iterations=14) & ~big & ~others
    ys, xs = np.nonzero(ring)
    px = img[ys, xs]
    lum = px.mean(axis=1)
    med = np.median(lum)
    keep = np.abs(lum - med) < max(18, 2.5 * np.median(np.abs(lum - med)) * 1.4826)
    ys, xs, px = ys[keep], xs[keep], px[keep]
    A = np.stack([xs, ys, np.ones_like(xs)], axis=1).astype(float)
    coefs = [np.linalg.lstsq(A, px[:, c], rcond=None)[0] for c in range(3)]
    zy, zx = np.nonzero(big)
    Z = np.stack([zx, zy, np.ones_like(zx)], axis=1).astype(float)
    fill = np.stack([Z @ coefs[c] for c in range(3)], axis=1)
    resid = px - np.stack([A @ coefs[c] for c in range(3)], axis=1)
    sigma = np.minimum(resid.std(axis=0) * 0.5, 4.0)
    noise = rng.normal(0, 1, size=fill.shape) * sigma  # texture légère
    new = np.clip(fill + noise, 0, 255)
    soft = ndi.gaussian_filter(big.astype(float), 1.2)[zy, zx][:, None]
    img[zy, zx] = img[zy, zx] * (1 - soft) + new * soft


def fill_paint(img: np.ndarray, zone: np.ndarray, others: np.ndarray, rng) -> None:
    big = ndi.binary_dilation(zone, iterations=4)
    ring = ndi.binary_dilation(big, iterations=14) & ~big & ~others
    ys, xs = np.nonzero(ring)
    px = img[ys, xs]
    sat = (px.max(axis=1) - px.min(axis=1)) / np.maximum(px.max(axis=1), 1)
    lum = px.mean(axis=1)
    whites = (sat < 0.25) & (lum > 140)
    color = np.median(px[whites], axis=0) if whites.sum() > 40 else np.array([236.0, 237.0, 235.0])
    color = np.minimum(color, 244.0)
    if color.max() < 228.0:  # support peint blanc : on évite un gris trop sombre
        color = color * (228.0 / color.max())
    zy, zx = np.nonzero(big)
    noise = rng.normal(0, 1.2, size=(len(zy), 1))
    new = np.clip(color[None, :] + noise, 0, 255)
    soft = ndi.gaussian_filter(big.astype(float), 1.0)[zy, zx][:, None]
    img[zy, zx] = img[zy, zx] * (1 - soft) + new * soft


def main() -> None:
    rng = np.random.default_rng(7)
    zones_json = {}
    for name, cfg in SCENES.items():
        src = RAW / f"{name}.png"
        if not src.exists():
            print("absent :", name)
            continue
        rgb = np.asarray(Image.open(src).convert("RGB"), dtype=float)
        mask = magenta_mask(rgb)
        labels, n = ndi.label(ndi.binary_opening(mask, iterations=1))
        comps = []
        for k in range(1, n + 1):
            ys, xs = np.nonzero(labels == k)
            if len(ys) < 150:
                continue
            comps.append({"k": k, "area": int(len(ys)), "cx": float(xs.mean()), "quad": quad_of(ys, xs)})
        comps.sort(key=lambda c: -c["area"] if cfg["order"] == "area" else c["cx"])
        all_zones = ndi.binary_dilation(np.isin(labels, [c["k"] for c in comps]), iterations=5)
        out = rgb.copy()
        for c in comps:
            zone = labels == c["k"]
            others = all_zones & ~ndi.binary_dilation(zone, iterations=6)
            (fill_fabric if cfg["mode"] == "fabric" else fill_paint)(out, zone, others, rng)
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT / f"{name}.jpg", quality=90)
        h, w = rgb.shape[:2]
        zones_json[name] = {
            "mode": cfg["mode"],
            "size": [w, h],
            "zones": [{"quad": expand(c["quad"]), "area": c["area"]} for c in comps],
        }
        print(f"{name}: {len(comps)} zone(s), aires {[c['area'] for c in comps]}")
    (OUT / "zones.json").write_text(json.dumps(zones_json, indent=1))


if __name__ == "__main__":
    main()
