import copy
import pytest
from koml_counterfactual_engine.core import InputError, simulate
from koml_counterfactual_engine.fixtures import fixture, expectations


def test_fixture_ground_truth_matches_hand_computed():
    assert simulate(fixture())["totals"] == expectations()["totals"]


@pytest.mark.parametrize("mutation", ["negative", "future", "extreme", "duplicate", "float", "bool", "drift", "basis"])
def test_rejects_adversarial_values(mutation):
    data = fixture(2)
    r = data["records"][0]
    if mutation == "negative": r["baseline"]["cost_minor"] = -1
    if mutation == "future": r["date"] = "2026-10-01"
    if mutation == "extreme": r["id"] = "a" * 10001
    if mutation == "duplicate": data["records"][1]["id"] = r["id"]
    if mutation == "float": r["baseline"]["cost_minor"] = 1.5
    if mutation == "bool": r["baseline"]["cost_minor"] = True
    if mutation == "drift": r["surprise"] = 1
    if mutation == "basis": r["alternatives"][0]["basis"] = "observed"
    with pytest.raises(InputError, match="SchemaError"):
        simulate(data)


def test_corrupted_fixture_changes_computed_results():
    data = fixture()
    data["records"][0]["alternatives"][0]["cost_minor"] = 900
    assert simulate(data)["totals"]["hypothetical_cost_difference_minor"] == 24900


def test_named_choice_and_tie_break():
    data = fixture(1)
    assert simulate(data, "premium")["totals"]["hypothetical_cost_minor"] == 1500
    with pytest.raises(InputError, match="unavailable"):
        simulate(data, "missing")
    data["records"][0]["alternatives"].append(dict(choice="aaa", cost_minor=800, duration_minutes=40, basis="hypothetical"))
    before = copy.deepcopy(data)
    assert simulate(data)["decisions"][0]["alternative_choice"] == "aaa"
    assert data == before
