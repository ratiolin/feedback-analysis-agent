# N=60 人工抽检说明

待审核文件：`data/manual-audit/holdout-audit.csv`。

逐行确认：

1. 工单正文是否自然表达该问题。
2. `gold_problem_type` 是否与正文一致。
3. `gold_product_area` 是否与正文一致。
4. `gold_issue_family` 是否确实表示同一重复问题。
5. `gold_escalation` 是否与影响信号一致。

填写：

- `audit_label_text_consistent`：`yes` 或 `no`。
- `audit_notes`：不一致原因与修正建议。
- `auditor`：审核者名字或稳定代号。

全部 60 条完成前，评测报告必须保留“锁定集待人工校验”的状态，不能称为人工校验集。

