"""Pure validation and arithmetic. Alternative differences are hypothetical."""

from datetime import date


class InputError(ValueError):
    """Named input error suitable for presentation without a traceback."""


def fail(field, message):
    raise InputError(f"SchemaError: {field}: {message}")


def fields(value, required, path):
    if not isinstance(value, dict):
        fail(path, "expected object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required)
    if missing or extra:
        fail(path, f"missing fields {sorted(missing)}; unknown fields {sorted(extra)}")


def string(value, path):
    if not isinstance(value, str) or not value.strip() or len(value) > 10000:
        fail(path, "expected nonblank string of at most 10000 characters")
    if "\u2014" in value:
        fail(path, "em dash is forbidden; use a hyphen")
    return value


def amount(value, path):
    if type(value) is not int or not 0 <= value <= 10**12:
        fail(path, "expected integer from 0 to 1000000000000")


def iso_date(value, path):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
        return parsed
    except (ValueError, TypeError):
        fail(path, "expected ISO date YYYY-MM-DD")


def validate(dataset):
    fields(dataset, ["schema_version", "synthetic", "entered_by", "source", "as_of", "currency", "records"], "dataset")
    if type(dataset["schema_version"]) is not int or dataset["schema_version"] != 1:
        fail("schema_version", "expected 1")
    if type(dataset["synthetic"]) is not bool:
        fail("synthetic", "expected boolean")
    for key in ("entered_by", "source", "currency"):
        string(dataset[key], key)
    if len(dataset["currency"]) != 3 or not dataset["currency"].isascii() or not dataset["currency"].isupper() or not dataset["currency"].isalpha():
        fail("currency", "expected three uppercase ASCII letters")
    if not dataset["synthetic"] and dataset["entered_by"] != "Henry":
        fail("entered_by", "real input must be Henry's own manually entered data")
    as_of = iso_date(dataset["as_of"], "as_of")
    if not isinstance(dataset["records"], list):
        fail("records", "expected array")
    ids = set()
    for i, record in enumerate(dataset["records"]):
        path = f"records[{i}]"
        fields(record, ["id", "date", "baseline", "alternatives"], path)
        rid = string(record["id"], path + ".id")
        if rid in ids:
            fail(path + ".id", "duplicate id")
        ids.add(rid)
        if iso_date(record["date"], path + ".date") > as_of:
            fail(path + ".date", "future date relative to explicit as_of")
        if not isinstance(record["alternatives"], list) or not record["alternatives"]:
            fail(path + ".alternatives", "expected nonempty array")
        names = set()
        for j, option in enumerate([record["baseline"]] + record["alternatives"]):
            op = path + (".baseline" if j == 0 else f".alternatives[{j-1}]")
            fields(option, ["choice", "cost_minor", "duration_minutes", "basis"], op)
            name = string(option["choice"], op + ".choice")
            if name in names:
                fail(op + ".choice", "duplicate choice within decision")
            names.add(name)
            for key in ("cost_minor", "duration_minutes"):
                amount(option[key], op + "." + key)
            if option["basis"] != ("observed" if j == 0 else "hypothetical"):
                fail(op + ".basis", "baseline requires observed; alternatives require hypothetical")
    return dataset


def simulate(dataset, choice=None):
    """Select minimum cost, then duration, then choice; differences hypothetical."""
    validate(dataset)
    rows = []
    for record in sorted(dataset["records"], key=lambda r: r["id"]):
        options = record["alternatives"]
        if choice is not None:
            options = [o for o in options if o["choice"] == choice]
            if not options:
                fail(record["id"] + ".alternatives", f"choice {choice!r} unavailable")
        alternative = min(options, key=lambda o: (o["cost_minor"], o["duration_minutes"], o["choice"]))
        baseline = record["baseline"]
        rows.append({"id": record["id"], "baseline_choice": baseline["choice"], "alternative_choice": alternative["choice"],
                     "baseline_cost_minor": baseline["cost_minor"], "hypothetical_cost_minor": alternative["cost_minor"],
                     "baseline_duration_minutes": baseline["duration_minutes"], "hypothetical_duration_minutes": alternative["duration_minutes"],
                     "hypothetical_cost_difference_minor": baseline["cost_minor"] - alternative["cost_minor"],
                     "hypothetical_time_difference_minutes": baseline["duration_minutes"] - alternative["duration_minutes"],
                     "hypothetical_cheaper": alternative["cost_minor"] < baseline["cost_minor"]})
    numeric = ("baseline_cost_minor", "hypothetical_cost_minor", "baseline_duration_minutes", "hypothetical_duration_minutes", "hypothetical_cost_difference_minor", "hypothetical_time_difference_minutes")
    totals = {key: sum(r[key] for r in rows) for key in numeric}
    totals.update(record_count=len(rows), hypothetical_cheaper_count=sum(r["hypothetical_cheaper"] for r in rows))
    return {"schema_version": 1, "provenance": {key: dataset[key] for key in ("synthetic", "entered_by", "source", "as_of", "currency")},
            "selection": choice if choice is not None else "minimum input cost, then duration, then choice", "totals": totals, "decisions": rows}
