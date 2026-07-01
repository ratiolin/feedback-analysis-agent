# v2 候选锁定集

状态：`candidate_unscored`。

- `v4-holdout-locked.csv`：候选工作流真实回放输入与 gold 标签。
- `v4-holdout-audit.csv`：60/60 条 AI 辅助一致性复核结果；不是独立人工审计。
- `v4-manifest.json`：数据版本、类别支持、候选提示词路径与冻结 SHA-256。

该锁定集在 `feedback-structuring-v2-candidate.yml` 冻结后生成。不得读取 v4 错误案例来修改 v2 提示词；任何候选 DSL 变化都必须生成新的锁定集版本。
