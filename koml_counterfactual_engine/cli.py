"""Local-only CLI. All alternative results are hypothetical."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .core import InputError, simulate, validate
from .fixtures import fixture, expectations
from .report import render


def read_json(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
        # Optional labelled header comment, preserving line numbers.
        if text.startswith("//"):
            text = "\n" + text.split("\n", 1)[1]
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
    except (OSError, UnicodeError, IndexError) as exc:
        raise InputError(f"ReadError: {path}: line 1: {exc}") from exc


def write_atomic(path, text):
    temporary = None
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def load(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use kce fixtures --out <dir> or create an input directory")
    unsupported = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in (".csv", ".yaml", ".yml", ".jsonl"))
    if unsupported:
        raise InputError(f"SchemaError: {unsupported[0]}: line 1: unsupported format; use the documented JSON dataset schema")
    files = sorted(directory.glob("*.json"))
    files = [p for p in files if p.name != "expectations.json"]
    if not files:
        return {"schema_version": 1, "synthetic": True, "entered_by": "empty input", "source": "SYNTHETIC empty input; no observations", "as_of": "1970-01-01", "currency": "GBP", "records": []}
    datasets = []
    for path in files:
        data = read_json(path)
        try:
            validate(data)
        except InputError as exc:
            raise InputError(f"{exc}; file {path}; line 1 (schema validation)") from exc
        datasets.append(data)
    merged = dict(datasets[0], records=[])
    for data, path in zip(datasets, files):
        for key in ("synthetic", "entered_by", "source", "as_of", "currency"):
            if data[key] != merged[key]:
                raise InputError(f"SchemaError: {path}: line 1: conflicting field {key}; use separate runs for different provenance")
        merged["records"].extend(data["records"])
    try:
        return validate(merged)
    except InputError as exc:
        raise InputError(f"{exc}; files {', '.join(str(p) for p in files)}; line 1") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(prog="kce", description="Compute explicitly hypothetical alternatives from local inputs.")
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="Generate labelled synthetic ground truth", epilog="Example: kce fixtures --out demo")
    f.add_argument("--out", required=True)
    for name, help_text in (("run", "Compute hypothetical lowest-cost alternatives"), ("compare", "Compare a named hypothetical choice against observed baselines"), ("validate", "Check decision schema and adversarial values")):
        s = sub.add_parser(name, help=help_text, description=help_text, epilog=f"Example: kce {name} --input demo" + (" --choice alternative" if name == "compare" else ""))
        s.add_argument("--input", required=True)
        if name != "validate":
            s.add_argument("--state", default=".kce/result.json")
        if name == "compare":
            s.add_argument("--choice", required=True)
    r = sub.add_parser("report", help="Render results with provenance and hypothetical labels", epilog="Example: kce report --format md")
    r.add_argument("--format", choices=("md", "json"), default="md")
    r.add_argument("--state", default=".kce/result.json")
    r.add_argument("--out")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        if args.command == "fixtures":
            out = Path(args.out)
            for name, data in (("decisions.json", fixture()), ("expectations.json", expectations()), ("tiny/decisions.json", fixture(5))):
                write_atomic(out / name, "// SYNTHETIC fixture; hypothetical alternatives\n" + json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            print("SYNTHETIC fixtures written: 200 records plus tiny 5-record example; alternatives hypothetical.")
        elif args.command in ("run", "compare", "validate"):
            dataset = load(args.input)
            if args.command == "validate":
                print(f"Valid input: {len(dataset['records'])} records. Alternatives are hypothetical; provenance is self-declared.")
            else:
                result = simulate(dataset, getattr(args, "choice", None))
                write_atomic(args.state, render(result, "json"))
                print(f"Computed {result['totals']['record_count']} records; alternatives and differences are hypothetical. State: {args.state}")
        else:
            result = read_json(Path(args.state))
            try:
                output = render(result, args.format)
            except (KeyError, TypeError, ValueError) as exc:
                raise InputError(f"SchemaError: {args.state}: line 1: invalid result field {exc}") from exc
            if args.out:
                write_atomic(args.out, output)
            else:
                sys.stdout.write(output)
        return 0
    except InputError as exc:
        print(str(exc).replace("\u2014", "-"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
