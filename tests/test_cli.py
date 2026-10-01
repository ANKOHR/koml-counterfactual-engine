import json
import time
from pathlib import Path
import pytest
from koml_counterfactual_engine.cli import main, load, write_atomic
from koml_counterfactual_engine.core import InputError


def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "Data provenance: SYNTHETIC" in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    capsys.readouterr()
    assert main(["report", "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert all(v == 0 for v in result["totals"].values())


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n "bad": }')
    assert main(["run", "--input", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "ParseError" in err and "bad.json" in err and "line 2" in err
    assert "Traceback" not in err


def test_determinism_byte_identical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["fixtures", "--out", "demo"])
    for _ in range(2):
        assert main(["run", "--input", "demo"]) == 0
        assert main(["report", "--out", f"report{_}.md"]) == 0
    assert Path("report0.md").read_bytes() == Path("report1.md").read_bytes()


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for command in ("fixtures", "run", "report", "compare", "validate"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
    main(["fixtures", "--out", "demo"])
    assert main(["validate", "--input", "demo"]) == 0
    assert main(["compare", "--input", "demo", "--choice", "premium"]) == 0
    assert main(["report", "--format", "json"]) == 0


def test_missing_input_and_write_failure(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err
    target = tmp_path / "directory"
    target.mkdir()
    with pytest.raises(InputError, match="WriteError"):
        write_atomic(target, "anything")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["directory"]


def test_duplicate_across_files(tmp_path):
    main(["fixtures", "--out", str(tmp_path)])
    (tmp_path / "duplicate.json").write_bytes((tmp_path / "decisions.json").read_bytes())
    with pytest.raises(InputError, match="duplicate id"):
        load(tmp_path)


@pytest.mark.parametrize("suffix", ["csv", "yaml", "jsonl"])
def test_unsupported_formats_named_error(tmp_path, capsys, suffix):
    (tmp_path / ("bad." + suffix)).write_text("malformed")
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "SchemaError" in capsys.readouterr().err


def test_em_dash_input_rejected_and_error_sanitized(tmp_path, capsys):
    from koml_counterfactual_engine.fixtures import fixture
    data = fixture(1)
    data["source"] = "bad" + chr(8212) + "source"
    (tmp_path / "bad.json").write_text(json.dumps(data))
    assert main(["run", "--input", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "SchemaError" in err and chr(8212) not in err
