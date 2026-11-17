"""Génère une photo de base avec des zones magenta repères (outil de préparation, hors application).

Usage : python tools/gen_scene.py <nom> "<prompt>" [modèle]
Écrit assets/scenes/raw/<nom>.png et affiche le coût réel relevé par OpenRouter.
"""

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sponsor.llm import load_dotenv  # noqa: E402

load_dotenv(str(ROOT / ".env"))

MODEL = "google/gemini-3.1-flash-image"


def generate(name: str, prompt: str, model: str = MODEL) -> Path:
    body = json.dumps(
        {
            "model": model,
            "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
        },
    )
    data = json.load(urllib.request.urlopen(req, timeout=180))
    msg = data["choices"][0]["message"]
    images = msg.get("images") or []
    if not images:
        raise SystemExit("Pas d'image renvoyée : " + json.dumps(msg)[:400])
    url = images[0]["image_url"]["url"]
    raw = base64.b64decode(url.split(",", 1)[1])
    out = ROOT / "assets" / "scenes" / "raw" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    usage = data.get("usage", {})
    print(f"{out}  ({len(raw)//1024} Ko)  coût: {usage.get('cost')}  usage: {usage}")
    return out


if __name__ == "__main__":
    generate(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else MODEL)
