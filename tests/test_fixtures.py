from koml_counterfactual_engine.cli import main, read_json
from koml_counterfactual_engine.fixtures import fixture


def test_fixtures_labelled_synthetic(tmp_path):
    assert main(["fixtures", "--out", str(tmp_path)]) == 0
    for path in tmp_path.rglob("*.json"):
        assert path.read_text().startswith("// SYNTHETIC")
        assert read_json(path)["synthetic"] is True
    assert len(read_json(tmp_path / "decisions.json")["records"]) == 200
    assert len(read_json(tmp_path / "tiny/decisions.json")["records"]) == 5


def test_fixture_deterministic():
    assert fixture() == fixture()
