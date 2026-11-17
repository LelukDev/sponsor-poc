"""Démo : l'outil propose à un commerce local les emplacements réellement libres d'un club, avec photos réalistes."""

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
OFFER_TITLES = {"recommandee": "Offre recommandée", "entree": "Offre d'entrée", "premium": "Offre premium"}

st.set_page_config(page_title="Proposition de sponsoring", layout="wide")


@st.cache_resource
def _global_counter() -> dict:
    return {"n": 0}


@st.cache_data(show_spinner=False, max_entries=96)
def render_slot_jpeg(slot_id: str, logo_bytes: bytes | None, name: str, existing: tuple) -> bytes:
    """Photo de l'emplacement proposé, avec les sponsors déjà en place sur la même scène."""
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
        blocks.append(f"<h2>{OFFER_TITLES[key]} : {format_price(total)} par saison</h2><div class='g'>{cards}</div>")
    body = html.escape(plan["email_body"]).replace("\n", "<br>")
    return (
        "<!doctype html><meta charset='utf-8'><title>Proposition de sponsoring</title>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;max-width:1000px;margin:2rem auto;color:#1B2430}"
        ".g{display:flex;gap:16px;flex-wrap:wrap}.c{flex:1;min-width:260px}.c img{width:100%;height:auto;border-radius:6px}</style>"
        f"<h1>{html.escape(C.CLUB['name'])} × {html.escape(business)}</h1>{''.join(blocks)}"
        f"<h2>{html.escape(plan['email_subject'])}</h2><p>{body}</p>"
        "<p><em>Texte généré avec l'aide d'une IA, à relire avant envoi.</em></p>"
    )


# ---------- Titre ----------
st.title("Proposition de sponsoring")
st.caption(
    "Saisissez un commerce local : l'outil ne propose que les emplacements libres, évite les concurrents d'un sponsor "
    "existant et tient compte des besoins du club. Essayez « Garage Martin », « Pharmacie des Tilleuls » ou "
    "« Agence immobilière Century »."
)

# ---------- Profil du club (modifiable) ----------
if "inv" not in st.session_state:
    st.session_state["inv"] = pd.DataFrame(C.default_inventory())

with st.expander(f"Profil du club (fictif) : emplacements, sponsors et besoins"):
    st.caption(f"{C.CLUB['name']}, {C.CLUB['sport']}, {C.CLUB['licensees']} licenciés. Changez un statut, un prix ou un besoin : l'offre s'adapte à la prochaine génération.")
    base = st.session_state["inv"]
    edited = st.data_editor(
        base[["Emplacement", "Prix (€)", "Statut", "Sponsor actuel", "Secteur"]],
        hide_index=True,
        disabled=["Emplacement"],
        num_rows="fixed",
        width="stretch",
        column_config={
            "Statut": st.column_config.SelectboxColumn(options=["libre", "pris"], required=True),
            "Secteur": st.column_config.SelectboxColumn(options=[""] + C.SECTORS),
            "Prix (€)": st.column_config.NumberColumn(min_value=0, step=50, format="%d"),
        },
        key="inv_editor",
    )
    n1, n2 = st.columns([3, 1])
    needs = n1.text_area("Besoins du club", value=C.DEFAULT_NEEDS, height=100)
    goal = n2.number_input("Objectif de collecte (€)", min_value=0, value=C.DEFAULT_GOAL, step=500)

inventory = []
for slot, (_, row) in zip(C.SLOTS, edited.iterrows()):
    inventory.append(
        {
            "id": slot.id,
            "Emplacement": slot.label,
            "Prix (€)": int(row["Prix (€)"] or 0),
            "Statut": row["Statut"] or "libre",
            "Sponsor actuel": str(row["Sponsor actuel"] or ""),
            "Secteur": str(row["Secteur"] or ""),
        }
    )
summary = C.summarize(inventory, int(goal))
k1, k2, k3, k4 = st.columns(4)
k1.metric("Emplacements libres", f"{len(summary['free'])} / {len(inventory)}")
k2.metric("Déjà signé", format_price(summary["signed"]))
k3.metric("Reste à lever", format_price(summary["remaining"]))
k4.metric("Valeur des emplacements libres", format_price(summary["free_value"]))
if summary["gap"] > 0:
    st.warning(
        f"Les emplacements libres ne couvrent pas le reste à lever : il manque {format_price(summary['gap'])}. "
        "Piste : créer de nouveaux supports (tournoi, site du club, lettre d'information)."
    )

# ---------- Saisie ----------
with st.form("input"):
    c1, c2 = st.columns(2)
    business = c1.text_input("Nom du commerce", placeholder="Boulangerie Dupont")
    city = c2.text_input("Ville", placeholder="Villeurbanne")
    c3, c4 = st.columns(2)
    sector_hint = c3.text_input("Activité (facultatif)", placeholder="boulangerie-pâtisserie")
    logo_file = c4.file_uploader("Logo (facultatif)", type=["png", "jpg", "jpeg", "webp"])
    submitted = st.form_submit_button("Générer la proposition", type="primary")

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
        st.info("Tous les emplacements sont pris. Libérez-en un dans le profil du club, ou créez un nouveau support.")
    elif used >= MAX_PER_SESSION or counter["n"] >= MAX_TOTAL:
        st.error("Limite d'utilisation de la démonstration atteinte.")
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
            with st.spinner("Analyse du club et rédaction de l'offre…"):
                plan, meta = plan_offer(name, city.strip(), sector_hint.strip(), inventory, needs, int(goal))
            with st.spinner("Préparation des visuels…"):
                ids = {i for v in plan["offers"].values() for i in v}
                existing = tuple(
                    (r["id"], r["Sponsor actuel"] or "Partenaire") for r in inventory if r["Statut"] == "pris"
                )
                images = {i: render_slot_jpeg(i, logo_bytes, name, existing) for i in ids}
        except LLMError as exc:
            st.error(f"La génération a échoué : {exc}")
            st.stop()
        except Exception:
            st.error("Le service d'IA ne répond pas. Réessayez dans un instant.")
            st.stop()
        st.session_state["used"] = used + 1
        counter["n"] += 1
        st.session_state["result"] = {"business": name, "plan": plan, "meta": meta, "images": images, "has_logo": bool(logo_bytes)}

# ---------- Résultat ----------
state = st.session_state.get("result")
if state:
    plan, meta, images = state["plan"], state["meta"], state["images"]
    st.subheader(f"{C.CLUB['name']} × {state['business']}")
    st.caption(f"Secteur détecté : {plan['sector']}")
    if plan["needs_human"]:
        st.warning(f"À valider par un humain avant envoi : {plan['human_reason'] or 'information insuffisante.'}")
    for note in plan["notes"]:
        st.caption(note)
    st.write(plan["fit_reason"])
    if plan["need_link"]:
        st.info(f"Besoin du club : {plan['need_link']}")

    tabs = st.tabs([OFFER_TITLES[k] for k in ("recommandee", "entree", "premium")])
    for tab, key in zip(tabs, ("recommandee", "entree", "premium")):
        with tab:
            ids = plan["offers"][key]
            if not ids:
                st.info("Aucun emplacement libre pour cette offre.")
                continue
            total = sum(plan["price"][i] for i in ids)
            st.markdown(f"**Total : {format_price(total)} par saison**")
            cols = st.columns(min(len(ids), 3))
            for col, i in zip(cols, ids):
                with col:
                    st.image(images[i], width="stretch")
                    st.markdown(f"**{C.SLOT_BY_ID[i].label}**, {format_price(plan['price'][i])}")
                    st.caption(plan["benefits"].get(i, ""))
    if not state["has_logo"]:
        st.caption("Sans logo importé, le nom du commerce est utilisé à la place.")

    st.subheader("Mail d'accroche")
    st.text_input("Objet", value=plan["email_subject"])
    st.text_area("Message", value=plan["email_body"], height=240)
    st.caption("Texte généré avec l'aide d'une IA, à relire avant envoi. Les prix viennent de l'inventaire du club, pas de l'IA.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temps de rédaction", f"{meta['seconds']:.1f} s")
    m2.metric("Coût de la génération", f"{meta['cost_usd']:.5f} $")
    m3.metric("Tokens (entrée / sortie)", f"{meta['tokens_in']} / {meta['tokens_out']}")
    m4.metric("Modèle", meta["model"].split("/")[-1])
    st.caption("Les photos sont préparées une fois pour toutes : la pose du logo ne coûte rien.")

    st.download_button(
        "Télécharger la proposition (HTML)",
        data=build_download(state["business"], plan, images),
        file_name="proposition-sponsoring.html",
        mime="text/html",
    )

with st.expander("Hypothèses de cette démonstration"):
    st.markdown(
        "- Le club, ses effectifs, ses sponsors et ses besoins sont fictifs et modifiables dans le profil.\n"
        "- Les prix sont une grille d'exemple, fixée par le club et jamais produite par l'IA.\n"
        "- Les photos de base sont générées une fois ; le logo est posé automatiquement (perspective et lumière).\n"
        "- Les commerces d'alcool, de tabac et de jeux d'argent sont écartés avant tout appel à l'IA.\n"
        "- Aucun envoi réel d'e-mail, aucune connexion, aucun paiement."
    )
