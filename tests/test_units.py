import io
import json
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image, ImageDraw

from sponsor import club as C
from sponsor import llm, scenes
from sponsor.guardrail import check_business
from sponsor.pricing import format_price


# ---------- Garde-fou et prix ----------
def test_guardrail_blocks_alcohol_tobacco_gambling():
    for name in ("Cave à vins du Rhône", "Le Bar des Sports", "Tabac Presse Centrale", "Casino de Lyon"):
        assert check_business(name).status == "blocked", name


def test_guardrail_allows_normal_and_avoids_false_positives():
    for name in ("Boulangerie Dupont", "Garage Vincent", "Boulangerie de Paris", "Pharmacie du Centre"):
        assert check_business(name).status == "ok", name


def test_guardrail_unclear():
    assert check_business("ab").status == "unclear"
    assert check_business("commerce").status == "unclear"


def test_format_price():
    assert format_price(1500) == "1 500 €"


# ---------- Inventaire du club ----------
def test_default_inventory_numbers():
    inv = C.default_inventory()
    assert len(inv) == len(C.SLOTS) == 10
    s = C.summarize(inv, C.DEFAULT_GOAL)
    assert s["signed"] == 2400
    assert s["remaining"] == 9600
    assert s["free_value"] == 4250
    assert s["gap"] == 5350


def test_every_slot_points_to_a_real_zone():
    zones = json.loads((scenes.ASSETS / "zones.json").read_text())
    for slot in C.SLOTS:
        assert slot.scene in zones, slot.id
        assert all(z < len(zones[slot.scene]["zones"]) for z in slot.zones), slot.id


# ---------- Vérifications du plan (le code contrôle l'IA) ----------
BASE = {
    "sector": "automobile",
    "fit_reason": "a",
    "need_link": "",
    "offers": {"entree": ["banderole"], "recommandee": ["minibus"], "premium": ["minibus", "dos"]},
    "benefits": {"banderole": "x", "minibus": "y", "dos": "z"},
    "email_subject": "s",
    "email_body": "b",
    "needs_human": False,
    "human_reason": "",
}


def test_sanitize_drops_taken_slots_and_notes_it():
    data = dict(BASE, offers={"entree": ["poitrine"], "recommandee": ["minibus", "poitrine"], "premium": ["minibus"]})
    plan = llm.sanitize(data, C.default_inventory())
    for ids in plan["offers"].values():
        assert "poitrine" not in ids
    assert any("déjà pris" in n for n in plan["notes"])
    assert plan["offers"]["entree"]  # remplacé par une règle


def test_sanitize_detects_sector_conflict():
    data = dict(BASE, sector="immobilier-bâtiment")
    plan = llm.sanitize(data, C.default_inventory())
    assert plan["conflict"]["sponsor"] == "Groupe Lacroix Immobilier"
    assert plan["needs_human"] is True


def test_sanitize_unknown_sector_and_unknown_ids():
    data = dict(BASE, sector="astrologie", offers={"entree": ["nimportequoi"], "recommandee": [], "premium": []})
    plan = llm.sanitize(data, C.default_inventory())
    assert plan["sector"] == "autre" and plan["conflict"] is None
    free = {r["id"] for r in C.default_inventory() if r["Statut"] == "libre"}
    for ids in plan["offers"].values():
        assert ids and set(ids) <= free


def test_sanitize_with_everything_taken():
    inv = C.default_inventory()
    for r in inv:
        r["Statut"] = "pris"
    plan = llm.sanitize(BASE, inv)
    assert all(v == [] for v in plan["offers"].values())


def _client(replies):
    it = iter(replies)

    def create(**kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=next(it)))],
            usage=SimpleNamespace(prompt_tokens=1500, completion_tokens=800),
        )

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_plan_offer_parses_costs_and_falls_back():
    inv = C.default_inventory()
    plan, meta = llm.plan_offer("Garage Martin", "Lyon", "", inv, C.DEFAULT_NEEDS, 12000, client=_client(["ok " + json.dumps(BASE)]))
    assert plan["offers"]["recommandee"] == ["minibus"]
    assert meta["model"] == llm.SMALL_MODEL
    assert meta["cost_usd"] == pytest.approx((1500 * 0.10 + 800 * 0.50) / 1e6)
    _, meta2 = llm.plan_offer("Garage Martin", "Lyon", "", inv, C.DEFAULT_NEEDS, 12000, client=_client(["pas de json", json.dumps(BASE)]))
    assert meta2["model"] == llm.LARGE_MODEL
    with pytest.raises(llm.LLMError):
        llm.plan_offer("Garage Martin", "Lyon", "", inv, C.DEFAULT_NEEDS, 12000, client=_client(["rien", "rien"]))


# ---------- Pose du logo ----------
def _png(draw_fn, size=(400, 160), mode="RGBA", bg=(0, 0, 0, 0), fmt="PNG"):
    im = Image.new(mode, size, bg)
    draw_fn(ImageDraw.Draw(im))
    b = io.BytesIO()
    im.save(b, fmt)
    return b.getvalue()


def test_white_background_is_removed_from_logo():
    data = _png(lambda d: d.ellipse((60, 20, 340, 140), fill=(200, 40, 20)), mode="RGB", bg=(255, 255, 255), fmt="JPEG")
    logo = scenes.load_logo(data)
    a = np.asarray(logo)[..., 3]
    assert a[0, 0] < 30 and a[a.shape[0] // 2, a.shape[1] // 2] > 200


def test_load_logo_rejects_garbage_and_huge():
    with pytest.raises(ValueError):
        scenes.load_logo(b"pas une image")
    with pytest.raises(ValueError):
        scenes.load_logo(b"x" * (3 * 1024 * 1024))


def test_perspective_coefficients_map_corners():
    quad = [(100, 50), (300, 80), (290, 200), (90, 170)]
    c = scenes._coeffs(quad, 200, 100)
    for (x, y), (u, v) in zip(quad, [(0, 0), (200, 0), (200, 100), (0, 100)]):
        d = c[6] * x + c[7] * y + 1
        assert (c[0] * x + c[1] * y + c[2]) / d == pytest.approx(u, abs=1e-6)
        assert (c[3] * x + c[4] * y + c[5]) / d == pytest.approx(v, abs=1e-6)


@pytest.mark.parametrize("slot", C.SLOTS, ids=lambda s: s.id)
def test_every_slot_renders_and_changes_only_its_zone(slot):
    logo = scenes.wordmark("Garage Martin")
    out = scenes.render_scene(slot.scene, slot.zones, logo)
    plate = scenes._plate(slot.scene)
    assert out.size == plate.size
    diff = np.abs(np.asarray(out).astype(int) - np.asarray(plate).astype(int)).sum(axis=2) > 12
    assert diff.sum() > 150  # le logo est bien posé
    ys, xs = np.nonzero(diff)
    quads = [scenes._zones()[slot.scene]["zones"][z]["quad"] for z in slot.zones]
    pts = np.array([p for q in quads for p in q])
    assert xs.min() >= pts[:, 0].min() - 6 and xs.max() <= pts[:, 0].max() + 6
    assert ys.min() >= pts[:, 1].min() - 6 and ys.max() <= pts[:, 1].max() + 6


def test_light_logo_stays_visible_on_white_support():
    data = _png(lambda d: d.rounded_rectangle((10, 10, 390, 150), radius=30, outline=(255, 255, 255, 255), width=12))
    out = np.asarray(scenes.render_scene("pitch_boards", (0,), scenes.load_logo(data))).astype(int)
    q = np.array(scenes._zones()["pitch_boards"]["zones"][0]["quad"])
    cx, cy = int(q[:, 0].mean()), int(q[:, 1].mean())
    assert out[cy - 10 : cy + 10, cx - 10 : cx + 10].mean() < 120  # fond sombre posé derrière le logo clair


# ---------- Ponctuation naturelle ----------
def test_clean_text_removes_ai_dashes_and_arrows():
    assert llm.clean_text("Votre logo \u2014 visible partout \u2014 sur le minibus") == "Votre logo, visible partout, sur le minibus"
    assert llm.clean_text("Le minibus \u2013 notre besoin") == "Le minibus, notre besoin"
    assert llm.clean_text("garage \u2192 automobile") == "garage : automobile"
    assert llm.clean_text("Une phrase - avec un tiret de coupure") == "Une phrase, avec un tiret de coupure"
    assert llm.clean_text("Pharmacie du Centre, à Lyon") == "Pharmacie du Centre, à Lyon"
    assert llm.clean_text("sport-loisirs et santé-bien-être") == "sport-loisirs et santé-bien-être"


def test_sanitize_cleans_every_text_field():
    dirty = dict(BASE, fit_reason="a \u2014 b", email_subject="s \u2014 t", email_body="Bonjour,\n\nVotre garage \u2014 notre minibus.\nCordialement")
    dirty["benefits"] = {"banderole": "x \u2014 y", "minibus": "y", "dos": "z"}
    plan = llm.sanitize(dirty, C.default_inventory())
    blob = " ".join([plan["fit_reason"], plan["email_subject"], plan["email_body"], *plan["benefits"].values()])
    assert "\u2014" not in blob and "\u2013" not in blob
    assert plan["email_body"].count("\n") == 3  # les sauts de ligne sont conservés
