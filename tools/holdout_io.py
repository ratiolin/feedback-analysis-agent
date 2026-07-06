import json
from collections import Counter
from pathlib import Path


def support_counts(rows: list[dict]) -> dict:
    return {
        "problem_type_support": Counter(row["gold_problem_type"] for row in rows),
        "product_area_support": Counter(row["gold_product_area"] for row in rows),
    }


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
