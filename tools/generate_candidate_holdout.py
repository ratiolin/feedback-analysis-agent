# ruff: noqa: E501
import csv
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from feedback_app.routing import derive_severity, needs_escalation, route_owner
from feedback_app.schemas import ImpactSignals, ProblemType, ProductArea
from tools.holdout_io import support_counts, write_manifest

DATASET_VERSION = "v4-frozen-candidate-holdout-20260702"
PROMPT_PATH = Path("dify-workflows/feedback-structuring-v2-candidate.yml")
OUT_DIR = Path("data/candidate-evaluation")

# This fixture is generated only after the v2 candidate prompt is frozen. Do not use it to
# modify that prompt. Any prompt change invalidates this holdout and requires a new version.
FAMILIES = [
    ("V4-ISSUE-001", "Webhook 签名回调被拒", "integration", "open_api", "合作方收到的 Webhook 一直提示签名校验失败", "第三方回调端持续拒绝平台发送的 Webhook 签名"),
    ("V4-ISSUE-002", "SCIM 用户组同步缺失", "integration", "member_permission", "SCIM 同步后新建用户组没有出现在成员目录", "身份平台中的用户组同步完成后成员目录仍然缺少该组"),
    ("V4-ISSUE-003", "企业网盘附件链接失效", "integration", "file", "从企业网盘挂载的附件第二天就无法打开", "外部云盘同步进来的文件链接很快变成不可访问"),
    ("V4-ISSUE-004", "OAuth Token 刷新失败", "integration", "open_api", "开放接口的 OAuth Token 到期后没有自动刷新", "API 授权令牌过期后刷新流程没有返回新的 Token"),
    ("V4-ISSUE-005", "复制模板缺少自定义视图", "bug", "project", "用项目模板创建副本后自定义视图全部消失", "复制模板生成的新项目没有保留原来的自定义视图"),
    ("V4-ISSUE-006", "重复任务日期偏移", "bug", "task", "每月重复任务生成后截止日期提前了一天", "周期任务的新实例日期比规则设定的时间早一天"),
    ("V4-ISSUE-007", "文件批注保存后消失", "bug", "file", "预览文档时添加的批注保存后不见了", "文件预览中的批注提交成功但重新打开后消失"),
    ("V4-ISSUE-008", "同一事件重复通知", "bug", "notification", "一次负责人变更触发了两封内容相同的邮件", "任务负责人只修改一次却收到重复的通知邮件"),
    ("V4-ISSUE-009", "设置通知免打扰时段", "how_to", "notification", "如何设置晚上十点以后不再发送移动端通知", "想知道在哪里配置夜间免打扰时间"),
    ("V4-ISSUE-010", "批量调整截止日期", "how_to", "task", "怎样一次修改一批任务的截止日期", "请问能否批量把选中任务的到期时间顺延一周"),
    ("V4-ISSUE-011", "下载增值税发票", "how_to", "account_subscription", "在哪里下载本月订阅的增值税发票", "想查询并导出指定账期的电子发票"),
    ("V4-ISSUE-012", "恢复已归档里程碑", "how_to", "project", "误归档的里程碑应该从哪里恢复", "请问如何把已归档里程碑重新放回项目时间线"),
    ("V4-ISSUE-013", "默认项目隐私设置未应用", "configuration", "project", "组织默认设置为私有项目但新项目仍然公开", "默认项目可见范围已经设为私有，新建项目却没有继承"),
    ("V4-ISSUE-014", "周报发送时间未生效", "configuration", "notification", "每周汇总邮件设为周五发送但仍在周一到达", "修改周报发送时间后邮件还是按照旧时间推送"),
    ("V4-ISSUE-015", "新增席位未计入可用数", "configuration", "account_subscription", "刚购买的十个席位没有增加到可用席位中", "订阅扩容已经完成但后台可分配席位数量没变化"),
    ("V4-ISSUE-016", "任务字段默认值未生效", "configuration", "task", "自定义字段设置了默认值，新任务中仍然为空", "任务字段的默认选项保存后没有应用到新建任务"),
    ("V4-ISSUE-017", "大型看板加载缓慢", "performance", "project", "包含上千条任务的项目看板打开需要二十秒", "大型项目的看板首次加载非常慢"),
    ("V4-ISSUE-018", "任务搜索输入卡顿", "performance", "task", "在任务搜索框输入文字时页面会连续卡顿", "搜索任务时每输入一个字都要等待很久"),
    ("V4-ISSUE-019", "大文件预览缓慢", "performance", "file", "两百兆的设计文件预览一直停留在加载中", "较大的附件打开预览需要等待很长时间"),
    ("V4-ISSUE-020", "API 查询响应过慢", "performance", "open_api", "批量查询任务的 API 平均要十几秒才返回", "开放接口查询项目列表时响应时间明显过长"),
    ("V4-ISSUE-021", "访客可见私密项目", "permission", "member_permission", "访客账号可以看到标记为私密的项目", "只授予访客权限的成员看到了不应展示的私密项目"),
    ("V4-ISSUE-022", "账单管理员无法改抬头", "permission", "account_subscription", "账单管理员没有权限修改发票抬头", "已分配财务角色的成员仍然不能维护开票信息"),
    ("V4-ISSUE-023", "项目管理员无法邀请成员", "permission", "project", "项目管理员点击邀请成员时提示没有权限", "拥有项目管理角色的用户仍无法添加项目成员"),
    ("V4-ISSUE-024", "导入日期整体偏移", "data_consistency", "import_export", "Excel 导入后所有任务日期都向后偏移一天", "导入表格中的截止日期进入系统后统一多了一天"),
    ("V4-ISSUE-025", "成员数量统计不一致", "data_consistency", "member_permission", "团队首页显示的成员数与成员列表数量不同", "组织概览和成员管理页统计出的成员总数对不上"),
    ("V4-ISSUE-026", "批量更新生成重复标签", "data_consistency", "task", "批量修改任务后同一个标签出现了两次", "任务批处理完成后生成了名称相同的重复标签"),
    ("V4-ISSUE-027", "项目统计与列表不一致", "data_consistency", "project", "仪表盘显示的逾期任务数与任务列表不一致", "项目概览中的完成数量和筛选列表统计结果对不上"),
    ("V4-ISSUE-028", "导出包含评论内容", "feature_request", "import_export", "希望导出任务时可以同时包含评论记录", "建议在任务导出文件中增加评论内容列"),
    ("V4-ISSUE-029", "在线比较文件版本", "feature_request", "file", "希望文件模块支持在线比较两个版本的差异", "建议增加附件历史版本的并排对比功能"),
    ("V4-ISSUE-030", "跨项目风险视图", "feature_request", "project", "希望增加汇总多个项目风险状态的视图", "建议提供跨项目查看风险和阻塞项的管理页面"),
]


def build_rows() -> list[dict]:
    rows: list[dict] = []
    start = datetime(2026, 7, 2, 9, tzinfo=UTC)
    for family_index, (family, title, problem_type, product_area, first, second) in enumerate(
        FAMILIES
    ):
        blocked = any(
            cue in f"{first}{second}"
            for cue in ("无法", "失败", "消失", "拒绝", "不可访问", "停留在加载中")
        )
        for variant, base in enumerate((first, second)):
            team = variant == 1 and family_index % 3 == 0
            repeat_contacts = 2 if variant == 1 else 0
            suffixes = []
            if team:
                suffixes.append("该问题影响整个团队")
            if repeat_contacts:
                suffixes.append("已经联系客服两次")
            message = f"{base}{'，' + '，'.join(suffixes) if suffixes else ''}。"
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
                    "ticket_id": f"V4-T{number:03d}",
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
                    "split": "candidate_holdout",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict], include_audit: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if include_audit and path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))
        same_dataset = len(existing) == len(rows) and all(
            old.get("ticket_id") == new["ticket_id"] and old.get("message") == new["message"]
            for old, new in zip(existing, rows, strict=True)
        )
        reviewed = any(
            row.get("audit_label_text_consistent") or row.get("audit_notes") or row.get("auditor")
            for row in existing
        )
        if same_dataset and reviewed:
            return
    output = rows
    if include_audit:
        output = [
            {
                **row,
                "audit_label_text_consistent": "",
                "audit_notes": "",
                "auditor": "",
            }
            for row in rows
        ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)


def main()-> None:  # noqa: S3776 (tool script - acceptable complexity)
    prompt_bytes = PROMPT_PATH.read_bytes()
    prompt_sha256 = hashlib.sha256(prompt_bytes).hexdigest()
    rows = build_rows()
    write_csv(OUT_DIR / "v4-holdout-locked.csv", rows)
    write_csv(OUT_DIR / "v4-holdout-audit.csv", rows, include_audit=True)
    manifest = {
        "dataset_version": DATASET_VERSION,
        "state": "candidate_unscored",
        "generated_at": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "family_count": len(FAMILIES),
        "candidate_prompt_path": str(PROMPT_PATH),
        "candidate_prompt_sha256": prompt_sha256,
        **support_counts(rows),
        "boundary": (
            "Frozen synthetic candidate holdout. It must not be used to modify the v2 prompt. "
            "No model quality claim exists until the candidate workflow is imported and replayed."
        ),
    }
    write_manifest(OUT_DIR / "v4-manifest.json", manifest)
    print(f"generated candidate holdout rows={len(rows)} prompt_sha256={prompt_sha256}")


if __name__ == "__main__":
    main()
