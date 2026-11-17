"""Démo : un commerce local devient une proposition de sponsoring avec maquettes."""

import html

import streamlit as st

from sponsor.club import CLUB
from sponsor.guardrail import check_business
from sponsor.llm import LLMError, generate_proposal, load_dotenv
from sponsor.mockups import MOCKUPS, logo_data_uri
from sponsor.pricing import PACKAGES, format_price

load_dotenv()

MAX_PER_SESSION = 20
MAX_TOTAL = 1500

st.set_page_config(page_title="Proposition de sponsoring", layout="wide")


@st.cache_resource
def _global_counter() -> dict:
    return {"n": 0}


def build_download(business: str, mockups: dict, result: dict) -> str:
    blocks = "".join(
        f"<div class='b'><div>{svg}</div><p><strong>{html.escape(p.tier)}</strong> · "
        f"{html.escape(p.support)} · {format_price(p.price_eur)}</p>"
        f"<p>{html.escape(result['benefits'][p.key])}</p></div>"
        for p, svg in ((p, mockups[p.key]) for p in PACKAGES)
    )
    body = html.escape(result["email_body"]).replace("\n", "<br>")
    return (
        "<!doctype html><meta charset='utf-8'><title>Proposition de sponsoring</title>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;max-width:900px;margin:2rem auto;color:#1B2430}"
        ".g{display:flex;gap:16px;flex-wrap:wrap}.b{flex:1;min-width:240px}.b svg{width:100%;height:auto}</style>"
        f"<h1>{html.escape(CLUB['name'])} × {html.escape(business)}</h1>"
        f"<div class='g'>{blocks}</div>"
        f"<h2>{html.escape(result['email_subject'])}</h2><p>{body}</p>"
        "<p><em>Texte généré avec l'aide d'une IA, à relire avant envoi.</em></p>"
    )


st.title("Proposition de sponsoring")
st.caption(
    f"Démonstration avec un club fictif : {CLUB['name']} ({CLUB['sport']}, {CLUB['licensees']} licenciés). "
    "Saisissez un commerce local, l'outil prépare l'offre."
)

with st.form("input"):
    c1, c2 = st.columns(2)
    business = c1.text_input("Nom du commerce", placeholder="Boulangerie Dupont")
    city = c2.text_input("Ville", placeholder="Villeurbanne")
    c3, c4 = st.columns(2)
    sector_hint = c3.text_input("Activité (facultatif)", placeholder="boulangerie-pâtisserie")
    logo_file = c4.file_uploader("Logo (facultatif)", type=["png", "jpg", "jpeg", "webp", "svg"])
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
    elif used >= MAX_PER_SESSION or counter["n"] >= MAX_TOTAL:
        st.error("Limite d'utilisation de la démonstration atteinte.")
    else:
        logo_uri = None
        if logo_file is not None:
            try:
                logo_uri = logo_data_uri(logo_file.getvalue(), logo_file.type)
            except ValueError as exc:
                st.error(str(exc))
                st.stop()
        try:
            with st.spinner("Rédaction en cours…"):
                result, meta = generate_proposal(business.strip(), city.strip(), sector_hint.strip())
        except LLMError as exc:
            st.error(f"La génération a échoué : {exc}")
            st.stop()
        except Exception:
            st.error("Le service d'IA ne répond pas. Réessayez dans un instant.")
            st.stop()
        st.session_state["used"] = used + 1
        counter["n"] += 1
        st.session_state["result"] = {
            "business": business.strip(),
            "data": result,
            "meta": meta,
            "mockups": {p.key: MOCKUPS[p.key](business.strip(), logo_uri) for p in PACKAGES},
        }

state = st.session_state.get("result")
if state:
    data, meta, mockups = state["data"], state["meta"], state["mockups"]
    st.subheader(f"{CLUB['name']} × {state['business']}")
    if data.get("needs_human"):
        st.warning(f"À valider par un humain avant envoi : {data.get('human_reason') or 'information insuffisante.'}")
    st.write(data["fit_reason"])

    cols = st.columns(3)
    for col, p in zip(cols, reversed(PACKAGES)):
        with col:
            st.image(mockups[p.key], use_container_width=True)
            st.markdown(f"**{p.tier}** · {p.support} · **{format_price(p.price_eur)}**")
            st.caption(data["benefits"][p.key])

    st.subheader("Mail d'accroche")
    st.text_input("Objet", value=data["email_subject"])
    st.text_area("Message", value=data["email_body"], height=220)
    st.caption("Texte généré avec l'aide d'une IA, à relire avant envoi. Les prix viennent de la grille du club, pas de l'IA.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temps", f"{meta['seconds']:.1f} s")
    m2.metric("Coût de la génération", f"{meta['cost_usd']:.5f} $")
    m3.metric("Tokens (entrée / sortie)", f"{meta['tokens_in']} / {meta['tokens_out']}")
    m4.metric("Modèle", meta["model"].split("/")[-1])

    st.download_button(
        "Télécharger la proposition (HTML)",
        data=build_download(state["business"], mockups, data),
        file_name="proposition-sponsoring.html",
        mime="text/html",
    )

with st.expander("Hypothèses de cette démonstration"):
    st.markdown(
        "- Le club, ses effectifs et ses supports sont fictifs.\n"
        "- Les prix (500 €, 800 €, 1 500 € par saison) sont une grille d'exemple, calculée hors IA.\n"
        "- Sans logo, le nom du commerce est utilisé à la place.\n"
        "- Les commerces d'alcool, de tabac et de jeux d'argent sont écartés avant tout appel à l'IA.\n"
        "- Aucun envoi réel d'e-mail, aucune connexion, aucun paiement."
    )
