"""Étape « intelligence » : choisir les emplacements adaptés et rédiger, via OpenRouter.

L'IA propose ; le code vérifie : seuls des emplacements réellement libres sont retenus, les prix
viennent de l'inventaire, et un conflit de secteur avec un sponsor existant est signalé.
"""

import json
import os
import re
import time

from openai import OpenAI

from .club import CLUB, SECTORS, SLOT_BY_ID, club_facts

BASE_URL = "https://openrouter.ai/api/v1"
SMALL_MODEL = "anthropic/claude-haiku-5.5"
LARGE_MODEL = "anthropic/claude-sonnet-5.5"
# Prix en USD par million de tokens (entrée, sortie), relevés sur OpenRouter.
PRICES = {SMALL_MODEL: (0.10, 0.50), LARGE_MODEL: (2.00, 10.00)}

SYSTEM = (
    "Tu es l'assistant sponsoring d'un club sportif amateur français. Tu choisis les emplacements les mieux "
    "adaptés à un commerce local, puis tu rédiges l'offre. Réponds uniquement par un objet JSON valide.\n"
    "Règles :\n"
    "- Ne propose QUE des identifiants d'emplacements LIBRES. Jamais un emplacement déjà pris.\n"
    "- Priorité 1 : l'adéquation entre l'audience de l'emplacement et la clientèle du commerce (familles du quartier "
    "pour un commerce alimentaire ou de santé, automobilistes pour un garage, parents d'enfants pour un magasin de sport…). "
    "Priorité 2 : les besoins déclarés du club. Relie l'offre à un besoin seulement si le rapport est naturel "
    "(un garage et le minibus, un magasin de sport et les chasubles) ; sinon laisse need_link vide. Ne cite pas le minibus "
    "pour un commerce qui n'a aucun rapport avec les déplacements.\n"
    "- Varie les emplacements d'entrée et recommandés selon le commerce ; ne propose pas toujours les mêmes.\n"
    "- Trois offres : entrée = 1 emplacement abordable ; recommandee = 1 ou 2 emplacements les mieux adaptés ; "
    "premium = 2 ou 3 emplacements incluant le meilleur. Si trop peu d'emplacements sont libres, réutilise-les.\n"
    "- Utilise uniquement les faits fournis ; n'invente aucun chiffre ni aucune information sur le commerce. "
    "Ne cite aucun prix (l'application les ajoute).\n"
    "- Vouvoiement, ton simple, chaleureux et direct, sans formules administratives.\n"
    "- L'activité se déduit du nom quand il contient un mot d'activité (Boulangerie, Garage, Pharmacie, Sport…) : "
    "dans ce cas needs_human vaut false, même si le champ « activité indiquée » est vide. "
    "needs_human vaut true seulement si le nom ne permet vraiment pas de connaître l'activité (nom de personne, "
    "nom de fantaisie) ; rédige alors une version générique prudente. Remplis toujours tous les champs.\n"
    "- Secteurs : un magasin ou club de sport relève de sport-loisirs ; boulangerie, boucherie, primeur : alimentation ; "
    "garage, concessionnaire : automobile ; pharmacie, kiné, optique : santé-bien-être.\n"
    "- Ponctuation naturelle : n'utilise jamais de tiret long, de demi-cadratin, de flèche ni de tiret pour couper une phrase ; "
    "utilise des virgules et des points.\n"
    f"- sector doit être exactement l'une de ces valeurs : {', '.join(SECTORS)}."
)

SCHEMA_HINT = (
    '{"sector": "valeur de la liste", '
    '"fit_reason": "2 phrases : pourquoi ce commerce et ces emplacements", '
    '"need_link": "1 phrase qui relie l\'offre à un besoin du club, ou chaîne vide", '
    '"offers": {"entree": ["id"], "recommandee": ["id"], "premium": ["id", "id"]}, '
    '"benefits": {"<id utilisé dans une offre>": "1 phrase concrète : où et par qui c\'est vu"}, '
    '"email_subject": "objet du mail", '
    f'"email_body": "6 à 9 lignes, signé « Le bureau de {CLUB["name"]} »", '
    '"needs_human": false, "human_reason": ""}'
)


_DASHES = re.compile(r"\s*[\u2014\u2013\u2015]\s*|\s+-\s+")
_ARROWS = re.compile(r"\s*[\u2192\u2190\u21d2]\s*")


def clean_text(text: str) -> str:
    """Retire les tirets longs, demi-cadratins, flèches et tirets de coupure typiques d'un texte généré."""
    text = _DASHES.sub(", ", str(text))
    text = _ARROWS.sub(" : ", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


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


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES[model]
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("pas de JSON dans la réponse")
    data = json.loads(match.group(0))
    for field in ("sector", "fit_reason", "email_subject", "email_body", "offers", "benefits"):
        if field not in data:
            raise ValueError(f"champ manquant : {field}")
    if not isinstance(data["offers"], dict) or not isinstance(data["benefits"], dict):
        raise ValueError("offers et benefits doivent être des objets")
    return data


def sanitize(data: dict, inventory: list[dict]) -> dict:
    """Vérifications faites par le code : disponibilité, doublons, conflit de secteur, offres de secours."""
    free = [r for r in inventory if r["Statut"] != "pris"]
    free_ids = [r["id"] for r in free]
    price = {r["id"]: int(r["Prix (€)"]) for r in inventory}
    notes = []

    offers = {}
    for key in ("entree", "recommandee", "premium"):
        ids = data["offers"].get(key) or []
        if isinstance(ids, str):
            ids = [ids]
        clean = []
        for i in ids:
            if i in free_ids and i not in clean:
                clean.append(i)
            elif i in SLOT_BY_ID and i not in free_ids:
                notes.append(f"« {SLOT_BY_ID[i].label} » écarté : déjà pris.")
        offers[key] = clean[:3]

    by_price = sorted(free_ids, key=lambda i: price[i])
    if free_ids:
        if not offers["recommandee"]:
            offers["recommandee"] = by_price[len(by_price) // 2 : len(by_price) // 2 + 1]
            notes.append("Offre recommandée complétée par une règle (choix du modèle inutilisable).")
        if not offers["entree"]:
            offers["entree"] = by_price[:1]
        if not offers["premium"]:
            offers["premium"] = sorted(by_price[-3:], key=lambda i: price[i])
    sector = data.get("sector") if data.get("sector") in SECTORS else "autre"

    conflict = None
    if sector != "autre":
        for r in inventory:
            if r["Statut"] == "pris" and r.get("Secteur") == sector:
                conflict = {"sponsor": r.get("Sponsor actuel") or "un sponsor", "sector": sector, "slot": r["Emplacement"]}
                break

    benefits = {i: clean_text(data["benefits"].get(i, "")) for i in {j for v in offers.values() for j in v}}
    needs_human = bool(data.get("needs_human"))
    human_reason = clean_text(data.get("human_reason") or "")
    if conflict:
        needs_human = True
        human_reason = (
            f"Le secteur « {sector} » a déjà un partenaire ({conflict['sponsor']}, {conflict['slot']}). "
            "Vérifier la clause d'exclusivité avant d'envoyer. " + human_reason
        ).strip()
    return {
        "sector": sector,
        "fit_reason": clean_text(data.get("fit_reason", "")),
        "need_link": clean_text(data.get("need_link", "")),
        "offers": offers,
        "benefits": benefits,
        "email_subject": clean_text(data["email_subject"]),
        "email_body": "\n".join(clean_text(l) if l.strip() else "" for l in str(data["email_body"]).splitlines()).strip(),
        "needs_human": needs_human,
        "human_reason": human_reason,
        "conflict": conflict,
        "notes": notes,
        "price": price,
    }


def _call(client, model: str, user: str) -> tuple[dict, dict]:
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.4,
        max_tokens=1600,
        extra_body={"reasoning": {"enabled": False}},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    )
    seconds = time.perf_counter() - start
    data = _extract_json(resp.choices[0].message.content or "")
    u = resp.usage
    meta = {
        "model": model,
        "tokens_in": u.prompt_tokens,
        "tokens_out": u.completion_tokens,
        "cost_usd": cost_usd(model, u.prompt_tokens, u.completion_tokens),
        "seconds": seconds,
    }
    return data, meta


def plan_offer(business: str, city: str, sector_hint: str, inventory: list[dict], needs: str, goal: int, client=None):
    """Retourne (plan vérifié, mesures). Petit modèle par défaut, grand modèle si la réponse est inutilisable."""
    if client is None:
        client = OpenAI(base_url=BASE_URL, api_key=get_api_key(), timeout=60)
    user = (
        f"{club_facts(inventory, needs, goal)}\n\nCommerce à démarcher : {business}\n"
        f"Ville : {city or 'non précisée'}\nActivité indiquée : {sector_hint or 'non précisée'}\n\n"
        f"Format JSON attendu :\n{SCHEMA_HINT}"
    )
    last_error = None
    for model in (SMALL_MODEL, LARGE_MODEL):
        try:
            data, meta = _call(client, model, user)
            return sanitize(data, inventory), meta
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise LLMError(f"Réponse inutilisable après deux modèles : {last_error}")
