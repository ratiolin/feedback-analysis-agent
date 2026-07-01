import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix

from feedback_app.analysis import finalize_analysis
from feedback_app.analyzers import DemoAnalyzer, DifyAnalyzer
from feedback_app.clustering import select_threshold, threshold_clusters
from feedback_app.config import get_settings
from feedback_app.embeddings import SentenceTransformerEmbedder, TfidfEmbedder
from feedback_app.schemas import ProblemType, ProductArea, TicketInput


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_ticket(row: dict) -> TicketInput:
    return TicketInput(
        ticket_id=row["ticket_id"],
        user_type=row["user_type"],
        channel=row["channel"],
        message=row["message"],
        created_at=row["created_at"],
        current_status=row["current_status"],
    )


def confusion_payload(gold: list[str], predicted: list[str], labels: list[str]) -> dict:
    return {
        "labels": labels,
        "matrix": confusion_matrix(gold, predicted, labels=labels).tolist(),
        "report": classification_report(
            gold,
            predicted,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
    }


def structure_evaluation(rows: list[dict], analyzer_name: str) -> dict:
    settings = get_settings()
    analyzer = DifyAnalyzer(settings) if analyzer_name == "dify" else DemoAnalyzer()
    predicted_types: list[str] = []
    predicted_areas: list[str] = []
    predicted_owners: list[str] = []
    predicted_escalations: list[bool] = []
    evidence_located = 0
    first_pass_valid = 0
    errors: list[dict] = []
    for row in rows:
        try:
            raw = analyzer.analyze(as_ticket(row))
            first_pass_valid += 1
            final = finalize_analysis(row["message"], raw, settings.workflow_version, analyzer_name)
            predicted_types.append(final.problem_type.value)
            predicted_areas.append(final.product_area.value)
            predicted_owners.append(final.suggested_owner.value)
            predicted_escalations.append(final.needs_escalation)
            evidence_located += int(bool(final.evidence_spans) and not final.review_reasons)
        except Exception as exc:
            errors.append({"ticket_id": row["ticket_id"], "error": f"{type(exc).__name__}: {exc}"})
            predicted_types.append("error")
            predicted_areas.append("error")
            predicted_owners.append("error")
            predicted_escalations.append(True)

    gold_types = [row["gold_problem_type"] for row in rows]
    gold_areas = [row["gold_product_area"] for row in rows]
    gold_owners = [row["gold_owner"] for row in rows]
    gold_escalations = [row["gold_escalation"] == "true" for row in rows]
    high_indexes = [index for index, expected in enumerate(gold_escalations) if expected]
    escalation_recall = (
        sum(predicted_escalations[index] for index in high_indexes) / len(high_indexes)
        if high_indexes
        else 1.0
    )
    return {
        "analyzer": analyzer_name,
        "sample_count": len(rows),
        "first_pass_schema_rate": first_pass_valid / len(rows),
        "evidence_auto_location_rate": evidence_located / len(rows),
        "problem_type": confusion_payload(
            gold_types, predicted_types, [item.value for item in ProblemType]
        ),
        "product_area": confusion_payload(
            gold_areas, predicted_areas, [item.value for item in ProductArea]
        ),
        "owner_policy_consistency": sum(
            actual == expected
            for actual, expected in zip(predicted_owners, gold_owners, strict=True)
        )
        / len(rows),
        "escalation_recall": escalation_recall,
        "errors": errors,
    }


def clustering_evaluation(
    development: list[dict],
    holdout: list[dict],
    embedding_backend: str,
) -> dict:
    all_rows = development + holdout
    texts = [row["message"] for row in all_rows]
    if embedding_backend == "bge":
        embedder = SentenceTransformerEmbedder(get_settings().embedding_model)
    else:
        embedder = TfidfEmbedder()
    vectors = embedder.encode(texts)
    development_vectors = vectors[: len(development)]
    holdout_vectors = vectors[len(development) :]
    development_gold = [row["gold_issue_family"] for row in development]
    holdout_gold = [row["gold_issue_family"] for row in holdout]
    tuned = select_threshold(development_vectors, development_gold)
    holdout_labels = threshold_clusters(holdout_vectors, tuned.threshold)

    false_merges: list[dict] = []
    for left in range(len(holdout)):
        for right in range(left + 1, len(holdout)):
            same_predicted = holdout_labels[left] == holdout_labels[right]
            different_gold = holdout_gold[left] != holdout_gold[right]
            if same_predicted and different_gold:
                false_merges.append(
                    {
                        "left": holdout[left]["ticket_id"],
                        "right": holdout[right]["ticket_id"],
                        "left_family": holdout_gold[left],
                        "right_family": holdout_gold[right],
                    }
                )
    family_clusters: dict[str, set[int]] = defaultdict(set)
    for family, label in zip(holdout_gold, holdout_labels, strict=True):
        family_clusters[family].add(label)
    false_splits = [
        {"family": family, "predicted_cluster_count": len(labels)}
        for family, labels in family_clusters.items()
        if len(labels) > 1 and not family.startswith("SINGLETON")
    ]
    holdout_metrics = select_threshold(
        holdout_vectors,
        holdout_gold,
        thresholds=[tuned.threshold],
        minimum_pairwise_precision=0,
    )
    return {
        "embedding_backend": embedding_backend,
        "development_count": len(development),
        "holdout_count": len(holdout),
        "frozen_threshold": tuned.threshold,
        "development_metrics": {
            "pairwise": tuned.pairwise,
            "b_cubed": tuned.b_cubed,
            "purity": tuned.purity,
        },
        "holdout_metrics": {
            "pairwise": holdout_metrics.pairwise,
            "b_cubed": holdout_metrics.b_cubed,
            "purity": holdout_metrics.purity,
        },
        "false_merge_examples": false_merges[:10],
        "false_split_examples": false_splits[:10],
    }


def markdown_report(payload: dict) -> str:
    structure = payload["structure"]
    clustering = payload["clustering"]
    problem_macro = structure["problem_type"]["report"]["macro avg"]["f1-score"]
    area_macro = structure["product_area"]["report"]["macro avg"]["f1-score"]
    holdout = clustering["holdout_metrics"]
    return "\n".join(
        [
            "# 合成机制评测报告",
            "",
            "> 锁定人工校验集 N=60，仅用于合成场景下的机制质量评估，不代表真实业务分布。",
            "",
            f"- 分析器：`{structure['analyzer']}`",
            f"- 首次 Schema 通过率：{structure['first_pass_schema_rate']:.1%}",
            f"- 证据自动定位成功率：{structure['evidence_auto_location_rate']:.1%}",
            f"- 问题类型 Macro-F1：{problem_macro:.3f}",
            f"- 产品区域 Macro-F1：{area_macro:.3f}",
            f"- 责任路由策略一致率：{structure['owner_policy_consistency']:.1%}",
            f"- 升级召回率：{structure['escalation_recall']:.1%}",
            f"- 重复问题匹配精确率：{holdout['pairwise']['precision']:.1%}",
            f"- 重复问题匹配召回率：{holdout['pairwise']['recall']:.1%}",
            f"- 聚类纯度：{holdout['purity']:.1%}",
            f"- B³ F1（技术指标）：{holdout['b_cubed']['f1']:.3f}",
            "",
            "混淆矩阵、错误合并和错误拆分案例见同目录 JSON。",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/generated"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/evaluation"))
    parser.add_argument("--analyzer", choices=["demo", "dify"], default="demo")
    parser.add_argument("--embedding", choices=["tfidf", "bge"], default="tfidf")
    args = parser.parse_args()
    development = load_rows(args.data / "tickets_development_with_gold.csv")
    holdout = load_rows(args.data / "tickets_holdout_locked.csv")
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "boundary": "Synthetic mechanism benchmark; not a real-business distribution.",
        "structure": structure_evaluation(holdout, args.analyzer),
        "clustering": clustering_evaluation(development, holdout, args.embedding),
        "holdout_support": {
            "problem_type": Counter(row["gold_problem_type"] for row in holdout),
            "product_area": Counter(row["gold_product_area"] for row in holdout),
        },
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "evaluation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.out / "evaluation.md").write_text(markdown_report(payload), encoding="utf-8")
    print(markdown_report(payload))


if __name__ == "__main__":
    main()
