from collections import Counter

from tools.generate_dataset import build_rows


def test_dataset_has_planned_split_and_class_support() -> None:
    rows = build_rows()
    development = [row for row in rows if row["split"] == "development"]
    holdout = [row for row in rows if row["split"] == "holdout"]
    assert len(rows) == 240
    assert len(development) == 180
    assert len(holdout) == 60
    problem_support = Counter(row["gold_problem_type"] for row in holdout)
    area_support = Counter(row["gold_product_area"] for row in holdout)
    assert min(problem_support.values()) >= 5
    assert min(area_support.values()) >= 5


def test_runtime_fields_do_not_require_gold_labels() -> None:
    row = build_rows()[0]
    runtime_fields = {
        "ticket_id",
        "user_type",
        "channel",
        "message",
        "created_at",
        "current_status",
    }
    assert runtime_fields.issubset(row)

