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


# ---------- Guardrail and prices ----------
def test_guardrail_blocks_alcohol_tobacco_gambling():
    for name in ("Wine cellar of the Rhône", "Cave à vins du Rhône", "The Sports Bar", "Tabac Presse Centrale", "Casino de Lyon", "Vape Shop"):
        assert check_business(name).status == "blocked", name


def test_guardrail_allows_normal_and_avoids_false_positives():
    for name in ("Boulangerie Dupont", "Garage Vincent", "Boulangerie de Paris", "Pharmacie du Centre", "Barbershop Lyon"):
        assert check_business(name).status == "ok", name


def test_guardrail_unclear():
    assert check_business("ab").status == "unclear"
    assert check_business("shop").status == "unclear"


def test_format_price():
    assert format_price(1500) == "€1,500"


# ---------- Club inventory ----------
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


# ---------- Plan checks (the code controls the AI) ----------
BASE = {
    "sector": "automotive",
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
    assert any("already taken" in n for n in plan["notes"])
    assert plan["offers"]["entree"]  # replaced by a rule


def test_sanitize_detects_sector_conflict():
    data = dict(BASE, sector="real estate and construction")
    plan = llm.sanitize(data, C.default_inventory())
    assert plan["conflict"]["sponsor"] == "Lacroix Real Estate"
    assert plan["needs_human"] is True


def test_sanitize_unknown_sector_and_unknown_ids():
    data = dict(BASE, sector="astrology", offers={"entree": ["whatever"], "recommandee": [], "premium": []})
    plan = llm.sanitize(data, C.default_inventory())
    assert plan["sector"] == "other" and plan["conflict"] is None
    free = {r["id"] for r in C.default_inventory() if r["Status"] == "free"}
    for ids in plan["offers"].values():
        assert ids and set(ids) <= free


def test_sanitize_with_everything_taken():
    inv = C.default_inventory()
    for r in inv:
        r["Status"] = "taken"
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
    _, meta2 = llm.plan_offer("Garage Martin", "Lyon", "", inv, C.DEFAULT_NEEDS, 12000, client=_client(["not json", json.dumps(BASE)]))
    assert meta2["model"] == llm.LARGE_MODEL
    with pytest.raises(llm.LLMError):
        llm.plan_offer("Garage Martin", "Lyon", "", inv, C.DEFAULT_NEEDS, 12000, client=_client(["nothing", "nothing"]))


def test_prompt_is_in_english():
    assert "sponsorship assistant" in llm.SYSTEM and "FREE slots" in C.club_facts(C.default_inventory(), "x", 1000)


# ---------- Natural punctuation ----------
def test_clean_text_removes_ai_dashes_and_arrows():
    assert llm.clean_text("Your logo — seen everywhere — on the minibus") == "Your logo, seen everywhere, on the minibus"
    assert llm.clean_text("The minibus – our big need") == "The minibus, our big need"
    assert llm.clean_text("garage → automotive") == "garage: automotive"
    assert llm.clean_text("A sentence - cut by a dash") == "A sentence, cut by a dash"
    assert llm.clean_text("Pharmacie du Centre, in Lyon") == "Pharmacie du Centre, in Lyon"
    assert llm.clean_text("sport-leisure and well-being") == "sport-leisure and well-being"


def test_sanitize_cleans_every_text_field():
    dirty = dict(BASE, fit_reason="a — b", email_subject="s — t", email_body="Hello,\n\nYour garage — our minibus.\nBest regards")
    dirty["benefits"] = {"banderole": "x — y", "minibus": "y", "dos": "z"}
    plan = llm.sanitize(dirty, C.default_inventory())
    blob = " ".join([plan["fit_reason"], plan["email_subject"], plan["email_body"], *plan["benefits"].values()])
    assert "—" not in blob and "–" not in blob
    assert plan["email_body"].count("\n") == 3  # line breaks are kept


# ---------- Logo placement ----------
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
        scenes.load_logo(b"not an image")
    with pytest.raises(ValueError):
        scenes.load_logo(b"x" * (3 * 1024 * 1024))


def test_logo_error_messages_are_in_english():
    with pytest.raises(ValueError, match="too heavy|unreadable"):
        scenes.load_logo(b"x" * (3 * 1024 * 1024))
    with pytest.raises(ValueError, match="unreadable"):
        scenes.load_logo(b"not an image")


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
    assert diff.sum() > 150  # the logo is really placed
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
    assert out[cy - 10 : cy + 10, cx - 10 : cx + 10].mean() < 120  # a dark background is put behind the light logo


# ---------- Editing the club table ----------
def test_inventory_from_frame_handles_empty_and_bad_cells():
    import pandas as pd

    df = pd.DataFrame(C.default_inventory())
    df.loc[0, "Price (€)"] = float("nan")          # price cell cleared
    df.loc[1, "Status"] = "maybe"                  # invalid status
    df.loc[2, "Current sponsor"] = None            # sponsor cell cleared
    df.loc[3, "Sector"] = "astrology"              # unknown sector
    df.loc[4, "Price (€)"] = -50                   # negative price
    inv = C.inventory_from_frame(df)
    assert inv[0]["Price (€)"] == 0
    assert inv[1]["Status"] == "free"
    assert inv[2]["Current sponsor"] == ""
    assert inv[3]["Sector"] == ""
    assert inv[4]["Price (€)"] == 0
    assert len(inv) == 10 and all(r["id"] == s.id for r, s in zip(inv, C.SLOTS))


def test_taking_a_slot_changes_what_can_be_offered():
    import pandas as pd

    df = pd.DataFrame(C.default_inventory())
    df.loc[df["id"] == "minibus", "Status"] = "taken"
    df.loc[df["id"] == "minibus", "Current sponsor"] = "Garage Roux"
    inv = C.inventory_from_frame(df)
    plan = llm.sanitize(dict(BASE, offers={"entree": ["banderole"], "recommandee": ["minibus"], "premium": ["minibus", "dos"]}), inv)
    for ids in plan["offers"].values():
        assert "minibus" not in ids
    assert C.summarize(inv, 12000)["signed"] == 3200
