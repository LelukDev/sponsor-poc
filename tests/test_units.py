import json
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

from sponsor import llm
from sponsor.guardrail import check_business
from sponsor.mockups import MOCKUPS, logo_data_uri
from sponsor.pricing import PACKAGES, format_price, total_if_all


def test_guardrail_blocks_alcohol_tobacco_gambling():
    assert check_business("Cave à vins du Rhône").status == "blocked"
    assert check_business("Le Bar des Sports").status == "blocked"
    assert check_business("Tabac Presse Centrale").status == "blocked"
    assert check_business("Casino de Lyon").status == "blocked"


def test_guardrail_allows_normal_and_avoids_false_positives():
    assert check_business("Boulangerie Dupont").status == "ok"
    assert check_business("Garage Vincent").status == "ok"
    assert check_business("Boulangerie de Paris").status == "ok"
    assert check_business("Pharmacie du Centre").status == "ok"


def test_guardrail_unclear():
    assert check_business("ab").status == "unclear"
    assert check_business("commerce").status == "unclear"


def test_prices_fixed_and_formatted():
    assert [p.price_eur for p in PACKAGES] == [300, 800, 1500]
    assert format_price(1500) == "1 500 €"
    assert total_if_all() == 2600


def test_mockups_are_valid_svg_with_and_without_logo():
    uri = logo_data_uri(b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml")
    for fn in MOCKUPS.values():
        for logo in (None, uri):
            root = ET.fromstring(fn("Boulangerie & Fils <Dupont>", logo))
            assert root.tag.endswith("svg")
    assert "Boulangerie" in MOCKUPS["or"]("Boulangerie Dupont")
    assert "data:image/svg+xml;base64" in MOCKUPS["or"]("X Y Z", uri)


def test_logo_validation():
    with pytest.raises(ValueError):
        logo_data_uri(b"x", "application/pdf")
    with pytest.raises(ValueError):
        logo_data_uri(b"x" * (3 * 1024 * 1024), "image/png")


GOOD = {
    "sector": "boulangerie",
    "fit_reason": "a",
    "email_subject": "s",
    "email_body": "b",
    "benefits": {"bronze": "1", "argent": "2", "or": "3"},
}


def _client(replies):
    it = iter(replies)

    def create(**kwargs):
        content = next(it)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
            usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=400),
        )

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_generate_parses_json_and_costs():
    data, meta = llm.generate_proposal("Boulangerie Dupont", client=_client(["texte " + json.dumps(GOOD)]))
    assert data["sector"] == "boulangerie" and data["needs_human"] is False
    assert meta["model"] == llm.SMALL_MODEL
    assert meta["cost_usd"] == pytest.approx((1000 * 0.10 + 400 * 0.50) / 1e6)


def test_generate_falls_back_to_large_model():
    data, meta = llm.generate_proposal("Boulangerie Dupont", client=_client(["pas de json", json.dumps(GOOD)]))
    assert meta["model"] == llm.LARGE_MODEL


def test_generate_fails_cleanly():
    with pytest.raises(llm.LLMError):
        llm.generate_proposal("Boulangerie Dupont", client=_client(["rien", "toujours rien"]))
