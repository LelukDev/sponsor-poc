"""Demo: the tool offers a local business the free slots of a club, with realistic photos."""

import base64
import html
import io

import pandas as pd
import streamlit as st

from sponsor import club as C
from sponsor import scenes
from sponsor.guardrail import check_business
from sponsor.llm import LLMError, load_dotenv, plan_offer
from sponsor.pricing import format_price

load_dotenv()

MAX_PER_SESSION = 20
MAX_TOTAL = 1500
OFFER_TITLES = {"recommandee": "Recommended offer", "entree": "Entry offer", "premium": "Premium offer"}

st.set_page_config(page_title="Sponsorship offer", layout="wide")


@st.cache_resource
def _global_counter() -> dict:
    return {"n": 0}


@st.cache_data(show_spinner=False, max_entries=96)
def render_slot_jpeg(slot_id: str, logo_bytes: bytes | None, name: str, existing: tuple) -> bytes:
    """Photo of the proposed slot, with the sponsors already in place on the same scene."""
    slot = C.SLOT_BY_ID[slot_id]
    logo = scenes.load_logo(logo_bytes) if logo_bytes else scenes.wordmark(name)
    base = None
    for other_id, sponsor in existing:
        other = C.SLOT_BY_ID[other_id]
        if other.scene == slot.scene and not set(other.zones) & set(slot.zones):
            base = scenes.render_scene(other.scene, other.zones, scenes.wordmark(sponsor), base=base)
    img = scenes.render_scene(slot.scene, slot.zones, logo, base=base)
    if slot.crop:
        img = scenes.closeup(img, slot.scene, slot.zones)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def build_download(business: str, plan: dict, images: dict) -> str:
    blocks = []
    for key in ("recommandee", "entree", "premium"):
        ids = plan["offers"][key]
        if not ids:
            continue
        total = sum(plan["price"][i] for i in ids)
        cards = "".join(
            f"<div class='c'><img src='data:image/jpeg;base64,{base64.b64encode(images[i]).decode()}'>"
            f"<p><strong>{html.escape(C.SLOT_BY_ID[i].label)}</strong>, {format_price(plan['price'][i])}</p>"
            f"<p>{html.escape(plan['benefits'].get(i, ''))}</p></div>"
            for i in ids
        )
        blocks.append(f"<h2>{OFFER_TITLES[key]}: {format_price(total)} per season</h2><div class='g'>{cards}</div>")
    body = html.escape(plan["email_body"]).replace("\n", "<br>")
    return (
        "<!doctype html><meta charset='utf-8'><title>Sponsorship offer</title>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;max-width:1000px;margin:2rem auto;color:#1B2430}"
        ".g{display:flex;gap:16px;flex-wrap:wrap}.c{flex:1;min-width:260px}.c img{width:100%;height:auto;border-radius:6px}</style>"
        f"<h1>{html.escape(C.CLUB['name'])} and {html.escape(business)}</h1>{''.join(blocks)}"
        f"<h2>{html.escape(plan['email_subject'])}</h2><p>{body}</p>"
        "<p><em>Text written with the help of AI. Please read it before you send it.</em></p>"
    )


# ---------- Title ----------
st.title("Sponsorship offer")
st.caption(
    "Type a local business. The tool offers only the free slots, avoids competitors of a current sponsor "
    "and follows the needs of the club. Try \"Garage Martin\", \"Pharmacie des Tilleuls\" or \"Agence immobilière Century\"."
)

# ---------- Club profile (editable) ----------
if "inv" not in st.session_state:
    st.session_state["inv"] = pd.DataFrame(C.default_inventory())

with st.expander("Club profile (example club): slots, sponsors and needs"):
    st.caption(
        f"{C.CLUB['name']}, {C.CLUB['sport']}, {C.CLUB['licensees']} members. "
        "Change a status, a price or a need: the offer changes the next time you generate it."
    )
    base = st.session_state["inv"]
    edited = st.data_editor(
        base[list(C.COLUMNS)],
        hide_index=True,
        disabled=["Slot"],
        num_rows="fixed",
        width="stretch",
        column_config={
            "Status": st.column_config.SelectboxColumn(options=[C.STATUS_FREE, C.STATUS_TAKEN], required=True),
            "Sector": st.column_config.SelectboxColumn(options=[""] + C.SECTORS),
            "Price (€)": st.column_config.NumberColumn(min_value=0, step=50, format="%d"),
        },
        key="inv_editor",
    )
    n1, n2 = st.columns([3, 1])
    needs = n1.text_area("Needs of the club", value=C.DEFAULT_NEEDS, height=100)
    goal = n2.number_input("Fundraising goal (€)", min_value=0, value=C.DEFAULT_GOAL, step=500)

inventory = C.inventory_from_frame(edited)
summary = C.summarize(inventory, int(goal))
k1, k2, k3, k4 = st.columns(4)
k1.metric("Free slots", f"{len(summary['free'])} / {len(inventory)}")
k2.metric("Already signed", format_price(summary["signed"]))
k3.metric("Left to raise", format_price(summary["remaining"]))
k4.metric("Value of free slots", format_price(summary["free_value"]))
if summary["gap"] > 0:
    st.warning(
        f"The free slots do not cover what is left to raise: {format_price(summary['gap'])} is missing. "
        "Idea: create new things to sell, such as a tournament, the club website or a newsletter."
    )

# ---------- Input ----------
with st.form("input"):
    c1, c2 = st.columns(2)
    business = c1.text_input("Business name", placeholder="Boulangerie Dupont")
    city = c2.text_input("City", placeholder="Villeurbanne")
    c3, c4 = st.columns(2)
    sector_hint = c3.text_input("What the business does (optional)", placeholder="bakery and pastry")
    logo_file = c4.file_uploader("Logo (optional)", type=["png", "jpg", "jpeg", "webp"])
    submitted = st.form_submit_button("Generate the offer", type="primary")

if submitted:
    st.session_state.pop("result", None)
    verdict = check_business(business, sector_hint)
    counter = _global_counter()
    used = st.session_state.get("used", 0)
    if verdict.status == "unclear":
        st.info(verdict.message)
    elif verdict.status == "blocked":
        st.warning(verdict.message)
    elif not summary["free"]:
        st.info("All slots are taken. Free a slot in the club profile, or create a new thing to sell.")
    elif used >= MAX_PER_SESSION or counter["n"] >= MAX_TOTAL:
        st.error("The usage limit of this demo has been reached.")
    else:
        logo_bytes = logo_file.getvalue() if logo_file is not None else None
        if logo_bytes:
            try:
                scenes.load_logo(logo_bytes)
            except ValueError as exc:
                st.error(str(exc))
                st.stop()
        name = business.strip()
        try:
            with st.spinner("Reading the club profile and writing the offer..."):
                plan, meta = plan_offer(name, city.strip(), sector_hint.strip(), inventory, needs, int(goal))
            with st.spinner("Preparing the photos..."):
                ids = {i for v in plan["offers"].values() for i in v}
                existing = tuple(
                    (r["id"], r["Current sponsor"] or "Partner") for r in inventory if r["Status"] == C.STATUS_TAKEN
                )
                images = {i: render_slot_jpeg(i, logo_bytes, name, existing) for i in ids}
        except LLMError as exc:
            st.error(f"The offer could not be generated: {exc}")
            st.stop()
        except Exception:
            st.error("The AI service does not answer. Please try again in a moment.")
            st.stop()
        st.session_state["used"] = used + 1
        counter["n"] += 1
        st.session_state["result"] = {"business": name, "plan": plan, "meta": meta, "images": images, "has_logo": bool(logo_bytes)}

# ---------- Result ----------
state = st.session_state.get("result")
if state:
    plan, meta, images = state["plan"], state["meta"], state["images"]
    st.subheader(f"{C.CLUB['name']} and {state['business']}")
    st.caption(f"Sector found: {plan['sector']}")
    if plan["needs_human"]:
        st.warning(f"A person should check this before sending: {plan['human_reason'] or 'not enough information.'}")
    for note in plan["notes"]:
        st.caption(note)
    st.write(plan["fit_reason"])
    if plan["need_link"]:
        st.info(f"Club need: {plan['need_link']}")

    tabs = st.tabs([OFFER_TITLES[k] for k in ("recommandee", "entree", "premium")])
    for tab, key in zip(tabs, ("recommandee", "entree", "premium")):
        with tab:
            ids = plan["offers"][key]
            if not ids:
                st.info("No free slot for this offer.")
                continue
            total = sum(plan["price"][i] for i in ids)
            st.markdown(f"**Total: {format_price(total)} per season**")
            cols = st.columns(min(len(ids), 3))
            for col, i in zip(cols, ids):
                with col:
                    st.image(images[i], width="stretch")
                    st.markdown(f"**{C.SLOT_BY_ID[i].label}**, {format_price(plan['price'][i])}")
                    st.caption(plan["benefits"].get(i, ""))
    if not state["has_logo"]:
        st.caption("No logo was uploaded, so the business name is used instead.")

    st.subheader("Email to send")
    st.text_input("Subject", value=plan["email_subject"])
    st.text_area("Message", value=plan["email_body"], height=240)
    st.caption("Text written with the help of AI. Please read it before you send it. Prices come from the club's slots, not from the AI.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Writing time", f"{meta['seconds']:.1f} s")
    m2.metric("Cost of this offer", f"${meta['cost_usd']:.5f}")
    m3.metric("Tokens (in / out)", f"{meta['tokens_in']} / {meta['tokens_out']}")
    m4.metric("Model", meta["model"].split("/")[-1])
    st.caption("The photos are prepared once. Placing the logo on them costs nothing.")

    st.download_button(
        "Download the offer (HTML)",
        data=build_download(state["business"], plan, images),
        file_name="sponsorship-offer.html",
        mime="text/html",
    )

with st.expander("Assumptions of this demo"):
    st.markdown(
        "- The club, its members, its sponsors and its needs are made up. You can change them in the club profile.\n"
        "- The prices are an example grid set by the club. The AI never sets a price.\n"
        "- The base photos were generated once. The logo is placed on them by code, in perspective and with the light of the scene.\n"
        "- Alcohol, tobacco and gambling businesses are stopped before any call to the AI.\n"
        "- No email is sent, there is no login and no payment."
    )
