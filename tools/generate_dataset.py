# ruff: noqa: E501
import argparse
import csv
import json
import random
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from feedback_app.routing import derive_severity, needs_escalation, route_owner
from feedback_app.schemas import ImpactSignals, ProblemType, ProductArea

FAMILIES = [
    ("ISSUE-001", "到期通知未送达", "configuration", "notification", "任务到期后整个团队都无法收到提醒"),
    ("ISSUE-002", "邮件通知延迟", "performance", "notification", "邮件提醒延迟很久才出现"),
    ("ISSUE-003", "成员权限未生效", "permission", "member_permission", "团队成员权限修改后仍然无法访问项目"),
    ("ISSUE-004", "访客权限异常", "permission", "member_permission", "访客看到了不应公开的任务列表"),
    ("ISSUE-005", "CSV 字段映射异常", "data_consistency", "import_export", "CSV 导入后字段映射到了错误的列"),
    ("ISSUE-006", "重复导入任务", "data_consistency", "import_export", "同一份文件导入后生成了重复任务"),
    ("ISSUE-007", "Webhook 超时", "integration", "open_api", "Webhook 调用经常超时且没有回执"),
    ("ISSUE-008", "API Token 权限", "integration", "open_api", "API Token 无法读取已授权的项目"),
    ("ISSUE-009", "项目看板卡顿", "performance", "project", "项目看板打开和拖动任务都很卡"),
    ("ISSUE-010", "文件上传缓慢", "performance", "file", "文件上传到一半会长时间没有进度"),
    ("ISSUE-011", "任务依赖保存失败", "bug", "task", "设置任务依赖后保存提示失败"),
    ("ISSUE-012", "归档项目缺失", "bug", "project", "项目归档后在归档列表中找不到"),
    ("ISSUE-013", "文件预览空白", "bug", "file", "上传的文档点击预览只显示空白页"),
    ("ISSUE-014", "导出中文乱码", "bug", "import_export", "导出的 CSV 中文字段全部乱码"),
    ("ISSUE-015", "通知规则配置咨询", "how_to", "notification", "不知道怎样只接收我负责的任务提醒"),
    ("ISSUE-016", "批量修改任务咨询", "how_to", "task", "想知道如何批量修改任务负责人"),
    ("ISSUE-017", "自定义字段建议", "feature_request", "task", "希望任务支持更多自定义字段类型"),
    ("ISSUE-018", "管理驾驶舱建议", "feature_request", "project", "希望增加跨项目管理驾驶舱"),
    ("ISSUE-019", "席位数量配置", "configuration", "account_subscription", "订阅席位增加后可用数量没有变化"),
    ("ISSUE-020", "SSO 成员同步", "integration", "member_permission", "SSO 登录后成员没有同步到对应团队"),
]

PREFIXES = [
    "你好，",
    "麻烦帮忙看一下，",
    "我们这边遇到一个问题：",
    "今天使用时发现，",
    "企业管理员反馈，",
]
SUFFIXES = [
    "，请问应该怎么处理？",
    "，已经影响正常协作。",
    "，麻烦尽快确认。",
    "，刷新和重新登录都没有改善。",
    "，客服之前的说明没有解决。",
]


def make_signals(index: int, base_text: str) -> dict:
    blocked = any(word in base_text for word in ("无法", "失败", "找不到", "空白", "超时"))
    scope = "team" if index % 4 == 0 else "individual"
    repeat_contacts = 2 if index % 9 == 0 else 0
    return {
        "affected_scope": scope,
        "workflow_blocked": blocked,
        "data_loss_claimed": False,
        "repeat_contacts": repeat_contacts,
    }


def gold_fields(problem_type: str, product_area: str, signals: dict) -> dict:
    typed_signals = ImpactSignals.model_validate(signals)
    severity = derive_severity(typed_signals)
    return {
        "gold_problem_type": problem_type,
        "gold_product_area": product_area,
        "gold_owner": route_owner(ProblemType(problem_type), ProductArea(product_area)).value,
        "gold_severity": severity.value,
        "gold_escalation": str(needs_escalation(severity, typed_signals)).lower(),
    }


def build_rows(seed: int = 20260701) -> list[dict]:
    random.seed(seed)
    start = datetime(2026, 6, 1, 9, tzinfo=UTC)
    rows: list[dict] = []
    ticket_number = 1
    for family_index, (family_id, title, problem_type, product_area, base_text) in enumerate(FAMILIES):
        for variant in range(10):
            prefix = PREFIXES[variant % len(PREFIXES)]
            suffix = SUFFIXES[(variant // len(PREFIXES) + variant) % len(SUFFIXES)]
            message = f"{prefix}{base_text}{suffix}"
            signals = make_signals(variant, base_text)
            if family_index < 5:
                created_at = start + timedelta(days=21 + variant % 7, hours=variant)
            else:
                created_at = start + timedelta(days=(ticket_number * 7) % 28, hours=variant)
            row = {
                "ticket_id": f"T{ticket_number:04d}",
                "user_type": "enterprise_admin" if variant % 4 == 0 else "member",
                "channel": ("chat", "email", "support_portal")[variant % 3],
                "message": message,
                "created_at": created_at.isoformat(),
                "current_status": "open",
                "gold_issue_family": family_id,
                "gold_issue_title": title,
                **gold_fields(problem_type, product_area, signals),
                "gold_impact_signals": json.dumps(signals, ensure_ascii=False),
                "split": "holdout" if variant >= 8 else "development",
            }
            rows.append(row)
            ticket_number += 1

    problem_types = [item.value for item in ProblemType]
    product_areas = [item.value for item in ProductArea]
    for singleton in range(40):
        problem_type = problem_types[singleton % len(problem_types)]
        product_area = product_areas[(singleton * 3) % len(product_areas)]
        base = f"一次性问题 {singleton + 1}：{product_area} 模块出现{problem_type}相关疑问"
        signals = make_signals(singleton + 3, base)
        rows.append(
            {
                "ticket_id": f"T{ticket_number:04d}",
                "user_type": "member",
                "channel": "support_portal",
                "message": f"{base}，目前没有发现其他用户反馈。",
                "created_at": (start + timedelta(days=(ticket_number * 5) % 28)).isoformat(),
                "current_status": "open",
                "gold_issue_family": f"SINGLETON-{singleton + 1:03d}",
                "gold_issue_title": base,
                **gold_fields(problem_type, product_area, signals),
                "gold_impact_signals": json.dumps(signals, ensure_ascii=False),
                "split": "holdout" if singleton >= 20 else "development",
            }
        )
        ticket_number += 1
    return rows


def write_csv(path: Path, rows: list[dict], runtime_only: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if runtime_only:
        fieldnames = [
            "ticket_id",
            "user_type",
            "channel",
            "message",
            "created_at",
            "current_status",
        ]
    else:
        fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path: Path, rows: list[dict]) -> None:
    holdout = [row for row in rows if row["split"] == "holdout"]
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total": len(rows),
        "development": len(rows) - len(holdout),
        "holdout": len(holdout),
        "problem_type_support": Counter(row["gold_problem_type"] for row in holdout),
        "product_area_support": Counter(row["gold_product_area"] for row in holdout),
        "evidence_boundary": (
            "Synthetic mechanism fixture. The locked N=60 holdout requires manual audit and "
            "does not represent a real business distribution."
        ),
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_audit_sheet(path: Path, rows: list[dict]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    audit_rows = [
        {
            **row,
            "audit_label_text_consistent": "",
            "audit_notes": "",
            "auditor": "",
        }
        for row in rows
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/generated"))
    args = parser.parse_args()
    rows = build_rows()
    development = [row for row in rows if row["split"] == "development"]
    holdout = [row for row in rows if row["split"] == "holdout"]
    write_csv(args.out / "tickets_all_with_gold.csv", rows)
    write_csv(args.out / "tickets_development_with_gold.csv", development)
    write_csv(args.out / "tickets_holdout_locked.csv", holdout)
    write_csv(args.out / "tickets_demo_runtime.csv", development, runtime_only=True)
    write_manifest(args.out / "dataset_manifest.json", rows)
    write_audit_sheet(Path("data/manual-audit/holdout-audit.csv"), holdout)
    print(f"generated total={len(rows)} development={len(development)} holdout={len(holdout)}")


if __name__ == "__main__":
    main()
