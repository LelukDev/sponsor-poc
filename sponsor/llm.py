"""The "intelligence" step: pick the right slots and write the offer, through OpenRouter.

The AI proposes; the code checks. Only slots that are really free are kept, prices come from the
inventory, and a sector conflict with a current sponsor is flagged.
"""

import json
import os
import re
import time

from openai import OpenAI

from .club import CLUB, SECTORS, SLOT_BY_ID, STATUS_TAKEN, club_facts

BASE_URL = "https://openrouter.ai/api/v1"
SMALL_MODEL = "anthropic/claude-haiku-5.5"
LARGE_MODEL = "anthropic/claude-sonnet-5.5"
# Prices in USD per million tokens (input, output), read on OpenRouter.
PRICES = {SMALL_MODEL: (0.10, 0.50), LARGE_MODEL: (2.00, 10.00)}

SYSTEM = (
    "You are the sponsorship assistant of an amateur sports club in France. You choose the best slots for a local "
    "business, then you write the offer. Reply with one valid JSON object only.\n"
    "Rules:\n"
    "- Propose ONLY ids of FREE slots. Never propose a taken slot.\n"
    "- Priority 1: match the audience of the slot with the customers of the business (neighbourhood families for food "
    "or health shops, drivers for a garage, parents for a sports shop). Priority 2: the club's declared needs. Link the "
    "offer to a need only if the link is natural (a garage and the minibus, a sports shop and the training bibs); "
    "otherwise leave need_link empty. Do not mention the minibus for a business that has nothing to do with travel.\n"
    "- Vary the entry slot and the recommended slots from one business to another. Do not always propose the same ones.\n"
    "- Three offers. entree = 1 affordable slot. recommandee = 1 or 2 best-fitting slots. premium = 2 or 3 slots, "
    "including the best one. If few slots are free, reuse them.\n"
    "- Use only the facts you are given. Invent no figure and no information about the business. Quote no price, "
    "the app adds them.\n"
    "- Write in simple, warm and direct English. No stiff or formal phrases.\n"
    "- Business names are often French: Boulangerie = bakery, Boucherie = butcher, Pharmacie = pharmacy, "
    "Fleuriste = florist, Garage = car garage, Agence immobilière = estate agency, Coiffeur = hairdresser. "
    "If the name contains such a word, the activity is known: needs_human is false, even if the activity field is empty. "
    "Set needs_human to true only if the name does not show the activity (a person's name, a fancy name). In that case "
    "write a careful, generic version and explain in human_reason. Always fill every field, including the email.\n"
    f"- sector must be exactly one of: {', '.join(SECTORS)}.\n"
    "- Sector hints: a sports shop or club is sport and leisure; bakery, butcher, greengrocer are food; garage and car "
    "dealer are automotive; pharmacy, physiotherapist and optician are health and wellness.\n"
    "- Each offer slot is a single slot, never combined: use the ids from the list only.\n"
    "- Natural punctuation: never use long dashes, en dashes, arrows, or a dash to cut a sentence. Use commas and full stops."
)

SCHEMA_HINT = (
    '{"sector": "one value from the list", '
    '"fit_reason": "2 short sentences: why this business and these slots fit", '
    '"need_link": "1 sentence that links the offer to a club need, or an empty string", '
    '"offers": {"entree": ["id"], "recommandee": ["id"], "premium": ["id", "id"]}, '
    '"benefits": {"<id used in an offer>": "1 concrete sentence: where it is seen and by whom"}, '
    '"email_subject": "email subject", '
    f'"email_body": "6 to 9 short lines, signed \\"The board of {CLUB["name"]}\\"", '
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
        raise LLMError("The OPENROUTER_API_KEY secret is missing.")
    return key


def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_DASH_CODES = "".join(chr(c) for c in (0x2014, 0x2013, 0x2015))
_ARROW_CODES = "".join(chr(c) for c in (0x2192, 0x2190, 0x21D2))
_DASHES = re.compile(r"\s*[" + _DASH_CODES + r"]\s*|\s+-\s+")
_ARROWS = re.compile(r"\s*[" + _ARROW_CODES + r"]\s*")


def clean_text(text: str) -> str:
    """Remove long dashes, en dashes, arrows and cutting dashes that generated text often contains."""
    text = _DASHES.sub(", ", str(text))
    text = _ARROWS.sub(": ", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES[model]
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("no JSON in the answer")
    data = json.loads(match.group(0))
    for field in ("sector", "fit_reason", "email_subject", "email_body", "offers", "benefits"):
        if field not in data:
            raise ValueError(f"missing field: {field}")
    if not isinstance(data["offers"], dict) or not isinstance(data["benefits"], dict):
        raise ValueError("offers and benefits must be objects")
    return data


def sanitize(data: dict, inventory: list[dict]) -> dict:
    """Checks done by the code: availability, duplicates, sector conflict, fallback offers."""
    free = [r for r in inventory if r["Status"] != STATUS_TAKEN]
    free_ids = [r["id"] for r in free]
    price = {r["id"]: int(r["Price (€)"]) for r in inventory}
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
                notes.append(f'"{SLOT_BY_ID[i].label}" was removed: it is already taken.')
        offers[key] = clean[:3]

    by_price = sorted(free_ids, key=lambda i: price[i])
    if free_ids:
        if not offers["recommandee"]:
            offers["recommandee"] = by_price[len(by_price) // 2 : len(by_price) // 2 + 1]
            notes.append("The recommended offer was completed by a rule (the model's choice could not be used).")
        if not offers["entree"]:
            offers["entree"] = by_price[:1]
        if not offers["premium"]:
            offers["premium"] = sorted(by_price[-3:], key=lambda i: price[i])
    sector = data.get("sector") if data.get("sector") in SECTORS else "other"

    conflict = None
    if sector != "other":
        for r in inventory:
            if r["Status"] == STATUS_TAKEN and r.get("Sector") == sector:
                conflict = {"sponsor": r.get("Current sponsor") or "a sponsor", "sector": sector, "slot": r["Slot"]}
                break

    benefits = {i: clean_text(data["benefits"].get(i, "")) for i in {j for v in offers.values() for j in v}}
    needs_human = bool(data.get("needs_human"))
    human_reason = clean_text(data.get("human_reason") or "")
    if conflict:
        needs_human = True
        human_reason = (
            f'The sector "{sector}" already has a partner ({conflict["sponsor"]}, {conflict["slot"]}). '
            "Check the exclusivity clause before you send this. " + human_reason
        ).strip()
    return {
        "sector": sector,
        "fit_reason": clean_text(data.get("fit_reason", "")),
        "need_link": clean_text(data.get("need_link", "")),
        "offers": offers,
        "benefits": benefits,
        "email_subject": clean_text(data["email_subject"]),
        "email_body": "\n".join(clean_text(line) if line.strip() else "" for line in str(data["email_body"]).splitlines()).strip(),
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
    """Return (checked plan, measures). Small model first, large model if the answer cannot be used."""
    if client is None:
        client = OpenAI(base_url=BASE_URL, api_key=get_api_key(), timeout=60)
    user = (
        f"{club_facts(inventory, needs, goal)}\n\nBusiness to approach: {business}\n"
        f"City: {city or 'not given'}\nActivity given: {sector_hint or 'not given'}\n\n"
        f"Expected JSON format:\n{SCHEMA_HINT}"
    )
    last_error = None
    for model in (SMALL_MODEL, LARGE_MODEL):
        try:
            data, meta = _call(client, model, user)
            return sanitize(data, inventory), meta
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise LLMError(f"Unusable answer after two models: {last_error}")
