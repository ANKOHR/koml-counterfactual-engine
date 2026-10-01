"""Deterministic report rendering with explicit provenance and honesty labels."""

import json


HONESTY = "Alternative costs, durations, differences and cheaper cases are hypothetical input scenarios, not measured savings or predictions. Baselines are input observations, not independently verified."


def banner(result):
    p = result["provenance"]
    kind = "SYNTHETIC fixtures; no real data" if p["synthetic"] else "REAL: Henry's own data, manually entered by Henry (self-declared)"
    return f"Data provenance: {kind}. Source: {p['source']}. As of: {p['as_of']}. Currency: {p['currency']}."


def render(result, format="md"):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), "honesty_boundary": HONESTY, **result}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lines = ["# KOML Counterfactual Engine", "", banner(result), "", HONESTY, "", f"Selection: {result['selection']}", "", "## Computed input totals", ""]
    lines.extend(f"- {key}: {value}" for key, value in result["totals"].items())
    lines.extend(["", "## Per-decision trace (JSON)", "", "```json", json.dumps(result["decisions"], ensure_ascii=False, sort_keys=True, indent=2), "```", ""])
    return "\n".join(lines)
