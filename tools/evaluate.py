import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix

from feedback_app.analysis import finalize_analysis
from feedback_app.analyzers import DemoAnalyzer, DifyAnalyzer
from feedback_app.clustering import normalize_ticket_text, select_threshold, threshold_clusters
from feedback_app.config import get_settings
from feedback_app.embeddings import SentenceTransformerEmbedder, TfidfEmbedder
from feedback_app.schemas import ProblemType, ProductArea, TicketInput


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_audit_status(path: Path, expected_rows: list[dict]) -> dict:
    rows = load_rows(path)
    expected = {(row["ticket_id"], row["message"]) for row in expected_rows}
    audited = {(row["ticket_id"], row["message"]) for row in rows}
    if audited != expected:
        raise ValueError("audit rows do not match the selected holdout")
    labels = Counter(row.get("audit_label_text_consistent", "").strip().lower() for row in rows)
    auditors = sorted(
        {
            row.get("auditor", "").strip()
            for row in rows
            if row.get("auditor", "").strip()
        }
    )
    status = {
        "review_type": "AI-assisted candidate consistency review",
        "independent_human_audit": False,
        "row_count": len(rows),
        "consistent": labels["yes"],
        "inconsistent": labels["no"],
        "unreviewed": len(rows) - labels["yes"] - labels["no"],
        "auditors": auditors,
        "boundary": (
            "Checks synthetic text/label consistency and deterministic policy derivation; "
            "does not establish real-business validity or replace independent human review."
        ),
    }
    if status["unreviewed"]:
        raise ValueError(f"audit has {status['unreviewed']} unreviewed rows")
    return status


def load_and_verify_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected_hash = manifest.get("candidate_prompt_sha256")
    prompt_path = manifest.get("candidate_prompt_path")
    if expected_hash and prompt_path:
        actual_hash = hashlib.sha256(Path(prompt_path).read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(
                "candidate prompt changed after holdout freeze; create a new holdout version"
            )
    return manifest


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
    texts = [normalize_ticket_text(row["message"]) for row in all_rows]
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
        "embedding_input": "normalized_ticket_text_proxy_for_production_summary",
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
    audit = payload["audit"]
    gates = payload["quality_gates"]
    return "\n".join(
        [
            "# 合成机制评测报告",
            "",
            (
                "> 锁定合成校验集 N=60，仅用于机制质量评估，不代表真实业务分布。"
                "当前已完成 AI 辅助一致性复核，不构成独立人工审计。"
            ),
            "",
            f"- 数据版本：`{payload['dataset_version']}`",
            f"- 评测状态：`{payload['evaluation_state']}`",
            *(
                [f"- 候选提示词 SHA-256：`{payload['candidate_prompt_sha256']}`"]
                if payload.get("candidate_prompt_sha256")
                else []
            ),
            (
                f"- AI 辅助复核：{audit['consistent']}/{audit['row_count']} 一致，"
                f"{audit['unreviewed']} 条未复核"
            ),
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
            "## 质量门",
            "",
            *[
                f"- {'通过' if gate['passed'] else '未通过'}：{gate['label']} "
                f"（实际 {gate['actual']:.3f}，门槛 {gate['threshold']:.3f}）"
                for gate in gates["items"]
            ],
            "",
            (
                "结论：已测关键门全部通过。"
                if gates["all_measured_passed"]
                else "结论：存在未通过的关键质量门，只能声明机制已实现，不能声明整体质量达标。"
            ),
            "",
            "混淆矩阵、错误合并和错误拆分案例见同目录 JSON。",
        ]
    )


def quality_gate_results(payload: dict) -> dict:
    structure = payload["structure"]
    holdout = payload["clustering"]["holdout_metrics"]
    values = [
        ("首次 Schema 通过率", structure["first_pass_schema_rate"], 0.95),
        (
            "问题类型 Macro-F1",
            structure["problem_type"]["report"]["macro avg"]["f1-score"],
            0.80,
        ),
        (
            "产品区域 Macro-F1",
            structure["product_area"]["report"]["macro avg"]["f1-score"],
            0.80,
        ),
        ("责任路由策略一致率", structure["owner_policy_consistency"], 0.85),
        ("高风险升级召回率", structure["escalation_recall"], 1.0),
        ("quote 自动定位成功率", structure["evidence_auto_location_rate"], 0.95),
        ("重复问题匹配精确率", holdout["pairwise"]["precision"], 0.80),
        ("B³ F1", holdout["b_cubed"]["f1"], 0.75),
    ]
    items = [
        {"label": label, "actual": actual, "threshold": threshold, "passed": actual >= threshold}
        for label, actual, threshold in values
    ]
    return {
        "items": items,
        "all_measured_passed": all(item["passed"] for item in items),
        "unmeasured": ["已接受记录 offset 有效率", "周报与 SOP 引用率"],
    }


def candidate_status_payload(payload: dict) -> dict:
    failed = [
        item["label"] for item in payload["quality_gates"]["items"] if not item["passed"]
    ]
    return {
        "workflow_state": "candidate_scored_unpromoted",
        "workflow_name": "客户反馈结构化-v2-candidate",
        "dsl_path": "dify-workflows/feedback-structuring-v2-candidate.yml",
        "candidate_prompt_sha256": payload.get("candidate_prompt_sha256"),
        "dataset_version": payload["dataset_version"],
        "holdout_rows": payload["structure"]["sample_count"],
        "audit_consistent": payload["audit"]["consistent"],
        "audit_type": "AI-assisted consistency review; not an independent human audit",
        "model_evaluation": "completed",
        "promotion_state": (
            "eligible_for_manual_promotion"
            if not failed
            else "blocked_quality_gates"
        ),
        "quality_gates_all_passed": not failed,
        "failed_quality_gates": failed,
        "boundary": (
            "A scored candidate remains separate from the official baseline. "
            "Promotion requires every measured gate to pass and an explicit promotion record."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/generated"))
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--out", type=Path, default=Path("artifacts/evaluation"))
    parser.add_argument(
        "--audit",
        type=Path,
        default=Path("data/manual-audit/holdout-audit.csv"),
    )
    parser.add_argument("--analyzer", choices=["demo", "dify"], default="demo")
    parser.add_argument("--embedding", choices=["tfidf", "bge"], default="tfidf")
    args = parser.parse_args()
    development = load_rows(args.data / "tickets_development_with_gold.csv")
    holdout_path = args.holdout or args.data / "tickets_holdout_locked.csv"
    manifest_path = args.manifest or args.data / "dataset_manifest.json"
    holdout = load_rows(holdout_path)
    manifest = load_and_verify_manifest(manifest_path)
    is_candidate = str(manifest.get("state", "")).startswith("candidate_")
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "boundary": "Synthetic mechanism benchmark; not a real-business distribution.",
        "dataset_version": manifest["dataset_version"],
        "evaluation_state": "candidate_scored_unpromoted" if is_candidate else "official_baseline",
        "candidate_prompt_sha256": manifest.get("candidate_prompt_sha256"),
        "audit": load_audit_status(args.audit, holdout),
        "structure": structure_evaluation(holdout, args.analyzer),
        "clustering": clustering_evaluation(development, holdout, args.embedding),
        "holdout_support": {
            "problem_type": Counter(row["gold_problem_type"] for row in holdout),
            "product_area": Counter(row["gold_product_area"] for row in holdout),
        },
    }
    payload["quality_gates"] = quality_gate_results(payload)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "evaluation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.out / "evaluation.md").write_text(markdown_report(payload), encoding="utf-8")
    if is_candidate:
        (args.out / "status.json").write_text(
            json.dumps(candidate_status_payload(payload), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(markdown_report(payload))


if __name__ == "__main__":
    main()
