"""Place a logo on realistic photos: perspective, light of the support, texture of the fabric.

The base photos (clean plates) and the zone shapes are prepared once by tools/prepare_scenes.py.
At run time: no network call, no cost, a few tens of milliseconds.
"""

import functools
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "scenes"
MAX_LOGO_BYTES = 2 * 1024 * 1024


@functools.lru_cache(maxsize=1)
def _zones() -> dict:
    return json.loads((ASSETS / "zones.json").read_text())


@functools.lru_cache(maxsize=16)
def _plate(scene: str) -> Image.Image:
    return Image.open(ASSETS / f"{scene}.jpg").convert("RGB")


# ---------- Logo ----------
def load_logo(data: bytes) -> Image.Image:
    if len(data) > MAX_LOGO_BYTES:
        raise ValueError("The logo file is too heavy (2 MB maximum).")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        raise ValueError("The logo file is unreadable. Please use png, jpg or webp.") from exc
    img = img.convert("RGBA")
    if max(img.size) > 1600:
        img.thumbnail((1600, 1600))
    return prepare_logo(img)


def prepare_logo(img: Image.Image) -> Image.Image:
    """Remove a plain light background if the logo has no transparency, then crop."""
    arr = np.asarray(img).astype(float)
    alpha = arr[..., 3]
    if alpha.min() >= 250:  # pas de vraie transparence
        border = np.concatenate([arr[0, :, :3], arr[-1, :, :3], arr[:, 0, :3], arr[:, -1, :3]])
        bg = np.median(border, axis=0)
        if bg.mean() > 200:  # light background: make it transparent
            dist = np.abs(arr[..., :3] - bg).max(axis=2)
            alpha = np.clip((dist - 18) / 40.0, 0, 1) * 255
            arr[..., 3] = alpha
    ys, xs = np.nonzero(arr[..., 3] > 12)
    if len(ys) == 0:
        raise ValueError("The logo is empty.")
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    pad = max(2, int(0.02 * max(out.size)))
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad + 1, out.width), min(ys.max() + pad + 1, out.height))
    return out.crop(box)


def wordmark(name: str) -> Image.Image:
    """Replacement logo: the name of the business in dark letters."""
    text = " ".join(name.strip().split())[:28] or "Partner"
    words = text.split()
    lines = [text] if len(text) <= 14 or len(words) < 2 else [" ".join(words[: len(words) // 2 or 1]), " ".join(words[len(words) // 2 or 1:])]
    font = ImageFont.load_default(size=120)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    sizes = [probe.textbbox((0, 0), ln, font=font, stroke_width=3) for ln in lines]
    w = max(b[2] - b[0] for b in sizes) + 40
    lh = max(b[3] - b[1] for b in sizes) + 24
    img = Image.new("RGBA", (w, lh * len(lines) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        bb = probe.textbbox((0, 0), ln, font=font, stroke_width=3)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], 10 + i * lh - bb[1] + 8), ln, font=font, fill=(27, 36, 48, 255), stroke_width=3, stroke_fill=(27, 36, 48, 255))
    return prepare_logo(img)


def _luma(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


# ---------- Geometry ----------
def _coeffs(quad, w, h):
    """PIL coefficients: output pixel (inside the quad) to pixel of the source rectangle."""
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(quad, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        B.extend([u, v])
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def _dist(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def _rect_size(quad):
    tl, tr, br, bl = quad
    return (_dist(tl, tr) + _dist(bl, br)) / 2, (_dist(tl, bl) + _dist(tr, br)) / 2


# ---------- Rendering one zone ----------
LIGHT_BG, DARK_BG = (252, 252, 250, 255), (28, 34, 46, 255)


def _card(w: int, h: int, logo: Image.Image, patch: bool, paint: bool, bg=LIGHT_BG) -> Image.Image:
    """Straightened rectangle: background (light, dark or transparent) plus the fitted logo."""
    if paint:
        card = Image.new("RGBA", (w, h), bg)
    elif patch:
        card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        r = int(min(w, h) * 0.12)
        ImageDraw.Draw(card).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=bg)
    else:
        card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pad = 0.10 if (paint or patch) else 0.04
    box_w, box_h = w * (1 - 2 * pad), h * (1 - 2 * pad)
    scale = min(box_w / logo.width, box_h / logo.height)
    lw, lh = max(1, int(logo.width * scale)), max(1, int(logo.height * scale))
    lg = logo.resize((lw, lh), Image.LANCZOS)
    card.alpha_composite(lg, ((w - lw) // 2, (h - lh) // 2))
    return card


def _logo_luma(logo: Image.Image) -> float:
    arr = np.asarray(logo).astype(float)
    a = arr[..., 3] / 255.0
    if a.sum() < 1:
        return 0.5
    return float((_luma(arr[..., :3]) / 255.0 * a).sum() / a.sum())


def _warp(card: Image.Image, quad, size) -> Image.Image:
    return card.transform(size, Image.PERSPECTIVE, _coeffs(quad, card.width, card.height), Image.BICUBIC)


def render_scene(scene: str, zone_ids, logo: Image.Image, base: Image.Image | None = None) -> Image.Image:
    cfg = _zones()[scene]
    paint = cfg["mode"] == "paint"
    plate = _plate(scene)
    arr = np.asarray(plate).astype(float) / 255.0
    luma_all = _luma(arr)
    blur = np.asarray(plate.filter(ImageFilter.GaussianBlur(3))).astype(float) / 255.0
    luma_blur = _luma(blur)
    tex = np.clip((luma_all - luma_blur) / np.maximum(luma_blur, 0.08), -0.4, 0.4)
    out = (np.asarray(base.convert("RGB")).astype(float) / 255.0) if base is not None else arr.copy()
    logo_l = _logo_luma(logo)
    lumas = []
    for zi in zone_ids:
        mi = Image.new("L", plate.size, 0)
        ImageDraw.Draw(mi).polygon([tuple(p) for p in cfg["zones"][zi]["quad"]], fill=255)
        mm = np.asarray(mi) > 128
        if mm.any():
            lumas.append(float(luma_all[mm].mean()))
    scene_luma = float(np.mean(lumas)) if lumas else 0.5
    bg = DARK_BG if logo_l > (0.78 if paint else 0.6) else LIGHT_BG
    patch = (not paint) and (abs(scene_luma - logo_l) < 0.45 or scene == "jersey_back")
    for zi in zone_ids:
        quad = cfg["zones"][zi]["quad"]
        zw, zh = _rect_size(quad)
        cw = int(min(max(zw * 1.6, 120), 1400))
        ch = int(max(cw * zh / max(zw, 1), 40))
        card = _card(cw, ch, logo, patch, paint, bg)
        layer = np.asarray(_warp(card, quad, plate.size)).astype(float) / 255.0
        a = layer[..., 3]
        a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(float) / 255.0
        rgb = layer[..., :3]
        if paint:
            # the logo "printed" on a lit white support: multiply by the light of the plate
            lit = arr * rgb  # the light always comes from the clean plate
            out = out * (1 - a[..., None]) + lit * a[..., None]
        else:
            ref = max(scene_luma, 0.05)
            light = np.clip(luma_blur / ref, 0.6, 1.12)[..., None]
            lit = rgb * light * 0.95 * (1 + 0.3 * tex[..., None])
            out = out * (1 - a[..., None]) + np.clip(lit, 0, 1) * a[..., None]
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def closeup(img: Image.Image, scene: str, zone_ids, min_frac: float = 0.62) -> Image.Image:
    """Close-up centred on the zones, with the same width to height ratio as the image."""
    cfg = _zones()[scene]
    pts = [p for zi in zone_ids for p in cfg["zones"][zi]["quad"]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    W, H = img.size
    w = max((max(xs) - min(xs)) * 2.2, W * min_frac)
    w = min(w, W)
    h = w * H / W
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h)))
