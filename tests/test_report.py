import json
from koml_counterfactual_engine.core import simulate
from koml_counterfactual_engine.fixtures import fixture, expectations
from koml_counterfactual_engine.report import render


def test_report_matches_ground_truth_exact():
    report = json.loads(render(simulate(fixture()), "json"))
    assert report["totals"] == expectations()["totals"]
    for row in report["decisions"]:
        assert row["baseline_cost_minor"] - row["hypothetical_cost_minor"] == row["hypothetical_cost_difference_minor"]


def test_report_zero_false_positives():
    rows = simulate(fixture())["decisions"]
    assert [r["id"] for r in rows if r["hypothetical_cheaper"]] == expectations()["hypothetical_cheaper_ids"]


def test_report_carries_provenance_banner():
    data = fixture(1)
    for fmt in ("json", "md"):
        assert "Data provenance: SYNTHETIC" in render(simulate(data), fmt)
    data.update(synthetic=False, entered_by="Henry", source="Henry manual input")
    assert "REAL: Henry's own data" in render(simulate(data))


def test_hypothetical_figures_labelled():
    for fmt in ("json", "md"):
        text = render(simulate(fixture()), fmt)
        assert "hypothetical_cost_difference_minor" in text
        assert "not measured savings or predictions" in text


def test_handles_unicode_and_long_inputs():
    data = fixture(1)
    data["records"][0]["id"] = "東京 café C:\\work\\" + "x" * 9000
    text = render(simulate(data), "json")
    assert json.loads(text)["decisions"][0]["id"] == data["records"][0]["id"]


def test_no_em_dashes_in_outputs():
    for fmt in ("json", "md"):
        assert chr(8212) not in render(simulate(fixture()), fmt)
