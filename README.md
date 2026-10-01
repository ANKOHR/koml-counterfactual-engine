# KOML Counterfactual Engine

KCE computes "what if we chose X instead?" from explicit local decision inputs.
It does not discover, predict, estimate, call models, access the network, or use a GPU.
Python 3.10+; standard library runtime; pytest for development.

## Quickstart

```powershell
python -m pip install --no-deps --no-build-isolation -e .
kce fixtures --out demo
kce run --input demo
kce report --format md
python -m pytest -q
```

If pip reports that its Scripts directory is absent from PATH, add that reported
directory to the current PowerShell session using `$env:PATH = "<Scripts>;" +
$env:PATH`, or invoke `python -m koml_counterfactual_engine.cli` in place of `kce`.

The fixture command also writes `demo/tiny/decisions.json`, a five-record
hand-designed example. Run `kce run --input demo/tiny` for the smallest version.
No randomness is used, so no seed is required. The same inputs and selection
produce byte-identical result files and reports. No runtime timestamps are added.

## Input format reference

Input directories contain JSON dataset files, read in filename order. All JSON
files except `expectations.json` are inputs. Other data formats (CSV, YAML,
JSONL) are rejected explicitly. Nested directories are not read. A leading
single `//` header comment is supported as an extension to standard JSON;
it occupies its original line for parse diagnostics. Ordinary JSON needs no comment.
Use a separate directory for unrelated data or generated reports.

Example of Henry's manually entered real input (illustrative format example,
not shipped trial evidence; alternative figures are hypothetical):

```json
{
  "schema_version": 1,
  "synthetic": false,
  "entered_by": "Henry",
  "source": "Henry manual decision log",
  "as_of": "2026-09-30",
  "currency": "GBP",
  "records": [{
    "id": "decision-1",
    "date": "2026-09-01",
    "baseline": {"choice": "current", "cost_minor": 1000,
      "duration_minutes": 60, "basis": "observed"},
    "alternatives": [{"choice": "alternative", "cost_minor": 800,
      "duration_minutes": 40, "basis": "hypothetical"}]
  }]
}
```

Every field above is required. Unknown fields fail validation. Currency is a
three-letter uppercase ASCII code, carried through without conversion. Money
is integer minor units (GBP pence), and durations are integer minutes. Both
must be between 0 and 1000000000000 inclusive; floats, booleans and negatives
are rejected. Differences may be negative and mean the alternative costs more
or takes longer. Dates must be exact ISO dates and cannot exceed explicit
`as_of`; no wall-clock date enters the calculation. Dates after `as_of` are
rejected even if a scenario is hypothetical.

IDs are unique across the whole input directory. Each decision has a baseline
and at least one alternative with distinct choice names. Nonblank strings may
contain Unicode and Windows paths, up to 10000 characters. Em dash characters
are rejected. Real datasets require `entered_by: Henry`; this is self-declared
provenance, not authentication. Multiple files must agree on provenance,
currency and `as_of`, preventing mixed real/synthetic reports.

The default selection minimizes alternative cost, then duration, then choice
name using deterministic Unicode ordering. It can select an alternative that
is more expensive than the baseline; it does not implicitly retain the baseline.
A named comparison requires that choice on every record. Baseline minus
alternative gives hypothetical cost/time differences. Strictly lower cost
marks a hypothetical cheaper case. Each report contains all decision traces
and totals, so counts and money reconcile directly to the inputs.

## Subcommand catalogue

- `kce fixtures --out demo`: write 200 labelled synthetic records, independent
  expectations, and a tiny five-record example.
- `kce run --input demo --state .kce/result.json`: compute the default selection.
- `kce compare --input demo --choice premium`: compute the named hypothetical
  choice against each observed baseline, writing the same report state format.
- `kce validate --input demo`: check schema, duplicate IDs and adversarial values.
- `kce report --format md`: render latest state with provenance and honesty labels.
- `kce report --format json --state .kce/result.json --out report.json`: write a report.

Each subcommand offers `--help` and an example. The default state is relative to
the current directory; report renders that snapshot, so rerun after editing inputs.
Run and compare write UTF-8 JSON state atomically. Report output also uses atomic
replacement; failed writes remove temporary files and preserve existing files.
The fixture set consists of individually atomic files, not a directory transaction.
Empty directories yield explicitly synthetic empty results with all zero totals.
Missing directories produce `MissingInput` with a usage hint and exit 2.
Malformed JSON produces `ParseError` with filename and exact line. Schema
failures name the offending field, file and line 1 (structural validation, not
an exact field location). Read and write failures produce `ReadError` and
`WriteError`. CLI errors exit 2 without tracebacks. Fix and rerun; failed runs do
not replace the previous state. Inputs and reports are local files only.

## Architecture

```text
fixtures.py -> labelled datasets and independent expectations
local JSON -> cli.py (parse, validate, atomic I/O)
           -> core.py (pure validation and hypothetical arithmetic)
           -> local result snapshot -> report.py -> Markdown or JSON
```

## Honesty boundary

Alternative costs, durations, differences and cheaper cases are hypothetical
input scenarios, never measured savings or predictions. Baselines are supplied
observations and are not independently verified. Synthetic baseline observations
are synthetic too. There is no measured savings output. Selection is an explicit
cost-first rule, not a recommendation based on utility, risk or causal inference.
No tool output supplies unentered outcomes or missing data. Time saved and money
saved cannot be claimed from these hypothetical differences. Runtime evidence
measures the CLI itself, not operator time saved. All reports carry a provenance
banner identifying synthetic inputs or Henry's self-declared real manual inputs.

## Fixture labelling and evidence

Every generated fixture file has a `// SYNTHETIC` header and `synthetic: true`.
The four planted cases have baseline (1000 pence, 60 minutes) and alternatives
(800,40), (1000,60), (1200,80), (500,90), repeated 50 times. Premium is
(1500,30) throughout. No production code computes the expectations file.
Hand arithmetic: alternative cost 50*(800+1000+1200+500)=175000;
alternative duration 50*(40+60+80+90)=13500. Baselines total 200000
and 12000. Hypothetical differences are 25000 and -1500. Exactly 100
strictly cheaper records are in cycle positions 0 and 3, with zero false positives.
Tests also corrupt one cost and verify the resulting 100-unit change.
See `EVIDENCE.md` for local acceptance results. Real trial data is not shipped.

## Evidence-based improvement hook and verdict

Start the two-week window on the first real use, not the build date. Henry should
record each run privately, with date, use count and a hand-checked sample of
selected choices and arithmetic. Primary metric: erroneous checked decisions /
all checked decisions; also record number of actual uses. After 14 days, if the
error rate exceeds 10 percent or usage is zero, record the top failure cause
and fix it, or kill with a written reason. This hook has not been measured yet.

Verdict is pending that real evidence window. Record date, sample size, error
rate, use count and reason in `VERDICT.md`. Expand if it earns daily use or
revenue; integrate if overlap with a sibling project dominates; commercialise
if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if
unused or unable to meet acceptance criteria. Synthetic acceptance results
alone do not justify expansion or commercialisation.
