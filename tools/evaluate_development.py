import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from tools.evaluate import (
    cached_cluster_texts,
    clustering_evaluation,
    load_rows,
    structure_evaluation,
)


def main()-> None:  # noqa: S3776 (tool script - acceptable complexity)
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--analysis-cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = load_rows(args.data)
    cache = json.loads(args.analysis_cache.read_text(encoding="utf-8"))
    structure = structure_evaluation(
        rows,
        "dify",
        "feedback-routing-v3-candidate",
        analysis_cache=cache,
    )
    cluster_texts = cached_cluster_texts(rows, cache)
    groups = [
        f"{area}|{problem_type}"
        for area, problem_type in zip(
            structure["predicted_product_areas"],
            structure["predicted_problem_types"],
            strict=True,
        )
    ]
    clustering = clustering_evaluation(
        rows,
        rows,
        "bge",
        development_groups=groups,
        holdout_groups=groups,
        linkage="complete",
        development_cluster_texts=cluster_texts,
        holdout_cluster_texts=cluster_texts,
        raw_text_weight=0.2,
        block_by_problem_type=True,
    )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "state": "development_only_not_promotion_eligible",
        "boundary": (
            "v5 is a seen development set. Metrics are resubstitution evidence for "
            "candidate selection and must not be presented as holdout performance."
        ),
        "data": str(args.data),
        "analysis_cache": str(args.analysis_cache),
        "structure": structure,
        "clustering": clustering,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "development.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(args.out / "development.json")


if __name__ == "__main__":
    main()
