# 四工作流套件激活记录

套件状态为 `candidate_scored_unpromoted`。四个 Dify 应用已导入、发布、配置独立 API Key，并完成真实 API 契约验证。内容生成工作流通过自身门禁，但四工作流整体套件因结构化/聚类门禁失败而未晋级。

## 应用与 Key

| DSL 文件 | 应用 | API Key 环境变量 | 回放状态 |
|---|---|---|---|
| `feedback-structuring-v2-candidate.yml` | `客户反馈结构化-v2-candidate` | `DIFY_FEEDBACK_WORKFLOW_API_KEY` | 60 条 v5 真实调用，2 条超时/缺失 |
| `issue-cluster-narrative-v1-candidate.yml` | `问题簇命名与解释-v1-candidate` | `DIFY_CLUSTER_WORKFLOW_API_KEY` | 30/30 成功 |
| `sop-draft-v1-candidate.yml` | `候选SOP草案-v1-candidate` | `DIFY_SOP_WORKFLOW_API_KEY` | 5/5 成功 |
| `weekly-report-narrative-v1-candidate.yml` | `运营周报叙事-v1-candidate` | `DIFY_REPORT_WORKFLOW_API_KEY` | 6/6 成功 |

真实 Key 只在 `.env`，不进入仓库、聊天、截图或作品材料。

## 已激活的服务端约束

- 结构化模型只输出 `quote`；服务端 exact match、规范化匹配并计算 offset。
- 最终责任方、严重度和升级由规则裁决，不盲信模型值。
- 问题簇、SOP 和周报中的 ticket ID 必须是确定性输入的子集，后端再次校验。
- 候选 SOP 始终是 `pending_review`，不会自动更改正式知识库或执行不可逆动作。
- 周报数字由确定性服务计算；模型只生成文案，根因只能标为“待确认原因”。
- 任一 Dify 调用失败时可降级为确定性文案，并持久化 `generation_source`/`workflow_version` 以便审计。

## v5 结果

内容生成：问题簇、SOP、周报成功率 100%，证据 ID 有效率和安全动作契约 100%。

整体未晋级：问题类型 Macro-F1 0.776、责任路由一致率 78.3%、重复识别精确率 71.4%、召回率 33.3% 未达门槛。v5 结果见 `artifacts/evaluation-v5-suite-candidate/` 与 `artifacts/workflow-suite-v1-candidate/`；后续调整必须使用全新 v6 锁定集。
