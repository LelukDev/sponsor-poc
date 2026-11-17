"""Étape de rédaction : un appel à un modèle via OpenRouter, avec mesure du coût."""

import json
import os
import re
import time

from openai import OpenAI

from .club import CLUB_FACTS, CLUB

BASE_URL = "https://openrouter.ai/api/v1"
SMALL_MODEL = "anthropic/claude-haiku-5.5"
LARGE_MODEL = "anthropic/claude-sonnet-5.5"
# Prix en USD par million de tokens (entrée, sortie), relevés sur OpenRouter.
PRICES = {SMALL_MODEL: (0.10, 0.50), LARGE_MODEL: (2.00, 10.00)}

SYSTEM = (
    "Tu rédiges des propositions de sponsoring pour un club sportif amateur français. "
    "Réponds uniquement par un objet JSON valide, sans texte autour. "
    "Règles : utilise uniquement les faits du club fournis ; n'invente aucun chiffre ni aucune "
    "information sur le commerce ; ne cite aucun prix (l'application les ajoute) ; vouvoiement ; "
    "ton simple, chaleureux et direct, sans formules administratives. "
    "L'activité se déduit du nom quand il contient un mot d'activité (Boulangerie, Garage, Pharmacie, "
    "Fleuriste, Restaurant…) : dans ce cas needs_human vaut false et tu personnalises le texte en reliant "
    "cette activité à la vie du club (familles du quartier, jours de match), sans inventer de fait. "
    "Mets needs_human à true seulement si le nom ne permet vraiment pas de savoir quelle est l'activité "
    "(nom de personne, nom de fantaisie) : explique-le dans human_reason et rédige quand même une version "
    "générique prudente. Remplis toujours tous les champs, mail compris. "
    "Chaque formule correspond à un seul support, sans les cumuler : bronze = panneau de stade, "
    "argent = minibus du club, or = maillot (poitrine)."
)

SCHEMA_HINT = (
    '{"sector": "activité déduite du commerce", '
    '"fit_reason": "2 phrases : pourquoi ce commerce et ce club vont bien ensemble", '
    '"email_subject": "objet du mail", '
    f'"email_body": "5 à 8 lignes, signé « Le bureau de {CLUB["name"]} »", '
    '"benefits": {"bronze": "1 phrase", "argent": "1 phrase", "or": "1 phrase"}, '
    '"needs_human": false, "human_reason": ""}'
)


class LLMError(RuntimeError):
    pass


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        try:
            import streamlit as st

            key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            key = ""
    if not key:
        raise LLMError("Clé OPENROUTER_API_KEY absente.")
    return key


def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("pas de JSON dans la réponse")
    data = json.loads(match.group(0))
    for field in ("sector", "fit_reason", "email_subject", "email_body", "benefits"):
        if field not in data:
            raise ValueError(f"champ manquant : {field}")
    for tier in ("bronze", "argent", "or"):
        if tier not in data["benefits"]:
            raise ValueError(f"avantage manquant : {tier}")
    data.setdefault("needs_human", False)
    data.setdefault("human_reason", "")
    return data


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES[model]
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000


def _call(client, model: str, business: str, city: str, sector_hint: str) -> tuple[dict, dict]:
    user = (
        f"{CLUB_FACTS}\n\nCommerce à démarcher : {business}\n"
        f"Ville : {city or 'non précisée'}\nActivité indiquée : {sector_hint or 'non précisée'}\n\n"
        f"Format JSON attendu :\n{SCHEMA_HINT}"
    )
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.4,
        max_tokens=1200,
        extra_body={"reasoning": {"enabled": False}},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    )
    seconds = time.perf_counter() - start
    content = resp.choices[0].message.content or ""
    data = _extract_json(content)
    usage = resp.usage
    meta = {
        "model": model,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
        "cost_usd": cost_usd(model, usage.prompt_tokens, usage.completion_tokens),
        "seconds": seconds,
    }
    return data, meta


def generate_proposal(business: str, city: str = "", sector_hint: str = "", client=None) -> tuple[dict, dict]:
    """Petit modèle par défaut ; grand modèle si la réponse du petit est inutilisable."""
    if client is None:
        client = OpenAI(base_url=BASE_URL, api_key=get_api_key(), timeout=45)
    total = {"calls": 0, "cost_usd": 0.0, "seconds": 0.0, "tokens_in": 0, "tokens_out": 0}
    last_error = None
    for model in (SMALL_MODEL, LARGE_MODEL):
        try:
            data, meta = _call(client, model, business, city, sector_hint)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue
        total["calls"] += 1
        for k in ("cost_usd", "seconds", "tokens_in", "tokens_out"):
            total[k] += meta[k]
        total["model"] = model
        return data, total
    raise LLMError(f"Réponse inutilisable après deux modèles : {last_error}")
