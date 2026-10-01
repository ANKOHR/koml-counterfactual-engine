"""Labelled synthetic fixtures. No randomness; seed is not applicable."""


def option(choice, cost, minutes, basis):
    return dict(choice=choice, cost_minor=cost, duration_minutes=minutes, basis=basis)


def fixture(count=200):
    records = []
    for i in range(count):
        group = i % 4
        # Four hand-designed cases: cheaper, equal, dearer, cheaper and slower.
        cost, minutes = [(800, 40), (1000, 60), (1200, 80), (500, 90)][group]
        records.append(dict(id=f"decision-{i+1:03}", date="2026-09-01", baseline=option("current", 1000, 60, "observed"), alternatives=[option("alternative", cost, minutes, "hypothetical"), option("premium", 1500, 30, "hypothetical")]))
    return dict(schema_version=1, synthetic=True, entered_by="fixture generator", source="SYNTHETIC: planted four-case cycle", as_of="2026-09-30", currency="GBP", records=records)


def expectations():
    # Independently hand-computed: 50 of each case, never call the engine here.
    return {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth", "totals": {
        "record_count": 200, "baseline_cost_minor": 200000, "hypothetical_cost_minor": 175000,
        "baseline_duration_minutes": 12000, "hypothetical_duration_minutes": 13500,
        "hypothetical_cost_difference_minor": 25000, "hypothetical_time_difference_minutes": -1500,
        "hypothetical_cheaper_count": 100},
        "hypothetical_cheaper_ids": [f"decision-{i+1:03}" for i in range(200) if i % 4 in (0, 3)]}
