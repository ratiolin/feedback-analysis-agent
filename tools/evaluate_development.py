import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from tools.evaluate import (
    cached_summaries,
    clustering_evaluation,
    load_rows,
    structure_evaluation,
)


def main() -> None:
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
    summaries = cached_summaries(rows, cache)
    clustering = clustering_evaluation(
        rows,
        rows,
        "bge",
        holdout_groups=structure["predicted_product_areas"],
        linkage="complete",
        development_summaries=summaries,
        holdout_summaries=summaries,
        raw_text_weight=0.8,
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
