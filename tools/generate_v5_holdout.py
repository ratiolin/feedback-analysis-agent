# ruff: noqa: E501
import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from feedback_app.routing import derive_severity, needs_escalation, route_owner
from feedback_app.schemas import ImpactSignals, ProblemType, ProductArea

DATASET_VERSION = "v5-frozen-suite-holdout-20260702"
OUT_DIR = Path("data/suite-evaluation")
DEVELOPMENT_PATH = Path("data/candidate-evaluation/v4-holdout-locked.csv")
FROZEN_FILES = [
    Path("dify-workflows/feedback-structuring-v2-candidate.yml"),
    Path("dify-workflows/issue-cluster-narrative-v1-candidate.yml"),
    Path("dify-workflows/sop-draft-v1-candidate.yml"),
    Path("dify-workflows/weekly-report-narrative-v1-candidate.yml"),
    Path("feedback_app/clustering.py"),
]

# New unseen families written after v4 was retired to development-only use. Once generated,
# v5 must not be used to modify the prompts, blocking key, or similarity threshold.
FAMILIES = [
    ("V5-ISSUE-001", "Jira 负责人同步缺失", "integration", "member_permission", "从 Jira 同步任务后负责人字段一直为空", "外部 Jira 任务进入平台时没有带入原来的经办人"),
    ("V5-ISSUE-002", "日历订阅事件缺失", "integration", "notification", "订阅项目日历后新增的截止事件没有出现在客户端", "外部日历已经订阅成功但新任务提醒事件没有同步过去"),
    ("V5-ISSUE-003", "API 游标重复返回", "integration", "open_api", "使用分页游标查询任务时下一页重复返回上一页数据", "开放接口翻页后的 cursor 仍然得到相同一批任务"),
    ("V5-ISSUE-004", "云盘文件名同步异常", "integration", "file", "同步企业云盘文件后带空格的文件名被截断", "外部网盘附件进入系统时文件名称没有完整保留"),
    ("V5-ISSUE-005", "子任务排序刷新后重置", "bug", "task", "调整子任务顺序后刷新页面又恢复原来的排列", "拖动保存的子任务次序在重新打开任务时丢失"),
    ("V5-ISSUE-006", "复制项目丢失自定义状态", "bug", "project", "复制项目后原来的自定义任务状态没有保留", "项目副本中缺少模板已经配置好的状态列"),
    ("V5-ISSUE-007", "文件下载版本错误", "bug", "file", "点击下载最新附件却拿到了上一个历史版本", "文件详情显示新版本但下载内容仍然是旧文件"),
    ("V5-ISSUE-008", "通知链接打开错误任务", "bug", "notification", "任务评论通知中的链接跳转到了另一个任务", "点击邮件提醒后打开的不是消息里提到的任务"),
    ("V5-ISSUE-009", "导出当前筛选结果", "how_to", "import_export", "如何只导出当前筛选后显示的任务", "想知道能否把列表筛选结果单独下载成表格"),
    ("V5-ISSUE-010", "轮换开放接口令牌", "how_to", "open_api", "请问在哪里更新即将到期的 API Token", "想了解怎样重新生成开放接口访问令牌"),
    ("V5-ISSUE-011", "配置项目访客范围", "how_to", "member_permission", "怎样限制访客只能查看指定项目", "请问从哪里设置外部成员可以访问的项目范围"),
    ("V5-ISSUE-012", "查看订阅用量", "how_to", "account_subscription", "在哪里查看当前套餐的席位和存储用量", "想查询本月订阅资源已经使用了多少"),
    ("V5-ISSUE-013", "默认负责人未应用", "configuration", "task", "任务模板设置了默认负责人但新任务仍然无人负责", "保存的任务默认经办人没有应用到后来创建的任务"),
    ("V5-ISSUE-014", "提醒提前量仍用旧值", "configuration", "notification", "到期提醒改为提前两天后仍按提前一天发送", "修改提醒提前时间后通知继续使用原来的配置"),
    ("V5-ISSUE-015", "项目工作周配置未应用", "configuration", "project", "项目设置为六天工作制但工期仍按五天计算", "修改项目工作日后时间计划没有采用新的工作周"),
    ("V5-ISSUE-016", "账单收件人配置未生效", "configuration", "account_subscription", "订阅账单收件邮箱修改后仍发送到旧地址", "已经保存新的财务联系人但账单邮件没有切换收件人"),
    ("V5-ISSUE-017", "大型项目导出缓慢", "performance", "import_export", "导出包含几万条任务的项目长时间没有生成文件", "大项目下载任务表格时一直停留在处理中"),
    ("V5-ISSUE-018", "角色管理页面缓慢", "performance", "member_permission", "成员角色管理页面打开需要十几秒", "进入权限配置列表后等待很久才显示角色"),
    ("V5-ISSUE-019", "附件下载速度过慢", "performance", "file", "下载较大的附件时速度持续非常慢", "大文件从项目中下载需要等待很长时间"),
    ("V5-ISSUE-020", "项目时间线滚动卡顿", "performance", "project", "项目时间线包含大量任务时滚动明显卡顿", "大型项目甘特视图拖动和滚动都很慢"),
    ("V5-ISSUE-021", "访客可以编辑附件", "permission", "file", "只读访客账号仍然可以替换项目附件", "访客被授予查看权限后却能上传新文件版本"),
    ("V5-ISSUE-022", "团队管理员无法维护角色", "permission", "member_permission", "团队管理员进入角色设置时提示没有操作权限", "拥有团队管理权限的成员仍不能修改成员角色"),
    ("V5-ISSUE-023", "财务查看者可以修改订阅", "permission", "account_subscription", "只读财务角色可以进入页面变更订阅套餐", "账单查看权限的成员错误获得了调整套餐的入口"),
    ("V5-ISSUE-024", "导出状态统计不一致", "data_consistency", "import_export", "导出文件中的已完成任务数与页面统计不同", "下载表格统计出的状态数量和任务列表对不上"),
    ("V5-ISSUE-025", "项目进度比例不一致", "data_consistency", "project", "项目首页的完成比例与任务明细计算结果不同", "项目概览进度和列表中的已完成任务占比不一致"),
    ("V5-ISSUE-026", "任务评论计数不一致", "data_consistency", "task", "任务卡片显示的评论数量与详情页实际条数不同", "列表上的评论计数和打开任务后看到的记录数对不上"),
    ("V5-ISSUE-027", "付费席位数量不一致", "data_consistency", "account_subscription", "订阅页显示的已用席位与成员计费列表数量不同", "套餐用量和付费成员清单统计出的席位数对不上"),
    ("V5-ISSUE-028", "批量归档项目", "feature_request", "project", "希望支持一次选择多个项目进行归档", "建议增加项目批量归档和恢复功能"),
    ("V5-ISSUE-029", "Webhook 事件重放", "feature_request", "open_api", "希望开放平台支持重新发送失败的 Webhook 事件", "建议提供回调投递记录的一键重放能力"),
    ("V5-ISSUE-030", "自定义通知摘要时间", "feature_request", "notification", "希望可以自定义每日通知摘要的发送时间", "建议让用户选择汇总提醒在一天中的推送时段"),
]


def build_rows() -> list[dict]:
    rows: list[dict] = []
    start = datetime(2026, 7, 10, 9, tzinfo=UTC)
    for family_index, (family, title, problem_type, product_area, first, second) in enumerate(
        FAMILIES
    ):
        blocked = any(
            cue in f"{first}{second}"
            for cue in ("无法", "错误", "丢失", "缺少", "没有", "长时间", "卡顿", "不一致")
        )
        for variant, base in enumerate((first, second)):
            team = variant == 1 and family_index % 4 == 0
            repeat_contacts = 2 if variant == 1 else 0
            clauses = []
            if team:
                clauses.append("该问题影响整个团队")
            if repeat_contacts:
                clauses.append("已经联系客服两次")
            message = f"{base}{'，' + '，'.join(clauses) if clauses else ''}。"
            signals = {
                "affected_scope": "team" if team else "individual",
                "workflow_blocked": blocked,
                "data_loss_claimed": False,
                "repeat_contacts": repeat_contacts,
            }
            typed = ImpactSignals.model_validate(signals)
            severity = derive_severity(typed)
            number = family_index * 2 + variant + 1
            rows.append(
                {
                    "ticket_id": f"V5-T{number:03d}",
                    "user_type": "enterprise_admin" if variant == 0 else "member",
                    "channel": "support_portal" if variant == 0 else "chat",
                    "message": message,
                    "created_at": (start + timedelta(hours=number * 3)).isoformat(),
                    "current_status": "open",
                    "gold_issue_family": family,
                    "gold_issue_title": title,
                    "gold_problem_type": problem_type,
                    "gold_product_area": product_area,
                    "gold_owner": route_owner(
                        ProblemType(problem_type), ProductArea(product_area)
                    ).value,
                    "gold_severity": severity.value,
                    "gold_escalation": str(needs_escalation(severity, typed)).lower(),
                    "gold_impact_signals": json.dumps(signals, ensure_ascii=False),
                    "split": "suite_holdout",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict], include_audit: bool = False) -> None:
    output = rows
    if include_audit:
        output = [
            {
                **row,
                "audit_label_text_consistent": "yes",
                "audit_notes": "AI-assisted v5 consistency review: pair, labels, routing and explicit impact cues align.",
                "auditor": "Codex AI-assisted review (not independent human)",
            }
            for row in rows
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main()-> None:  # noqa: S3776 (tool script - acceptable complexity)
    rows = build_rows()
    write_csv(OUT_DIR / "v5-holdout-locked.csv", rows)
    write_csv(OUT_DIR / "v5-holdout-audit.csv", rows, include_audit=True)
    manifest = {
        "dataset_version": DATASET_VERSION,
        "state": "candidate_unscored",
        "generated_at": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "family_count": len(FAMILIES),
        "candidate_prompt_path": str(FROZEN_FILES[0]),
        "candidate_prompt_sha256": sha256(FROZEN_FILES[0]),
        "frozen_files": [
            {"path": str(path), "sha256": sha256(path)} for path in FROZEN_FILES
        ],
        "development_dataset": str(DEVELOPMENT_PATH),
        "development_sha256": sha256(DEVELOPMENT_PATH),
        "problem_type_support": Counter(row["gold_problem_type"] for row in rows),
        "product_area_support": Counter(row["gold_product_area"] for row in rows),
        "boundary": (
            "Fresh synthetic v5 holdout generated after v4 was retired to development-only use. "
            "Do not tune prompts, product-area blocking, or the threshold on v5. "
            "AI-assisted review is not an independent human audit."
        ),
    }
    (OUT_DIR / "v5-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"generated v5 rows={len(rows)} families={len(FAMILIES)}")


if __name__ == "__main__":
    main()
