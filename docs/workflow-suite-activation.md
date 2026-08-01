# 四工作流套件状态记录

当前状态为 `published_pending_revalidation`。四个 Dify 应用已导入、发布并配置独立 API Key；2026-07-19 控制台与仓库 DSL 已同步为 `deepseek-v4-flash`；2026-08-01 完成 flash 真实回放与冻结评测：结构化工作流九项质量门全部通过，内容套件因周报叙事未达门槛保持未晋升。模型切换前的晋级结论不转移给当前 flash 配置。

## 应用与 Key

| DSL 文件 | 应用 | API Key 环境变量 | 当前 flash 状态 |
|---|---|---|---|
| `feedback-structuring-v3-candidate.yml` | `客户反馈结构化-v3-candidate` | `DIFY_FEEDBACK_WORKFLOW_API_KEY` | 已发布；flash 冻结回放九门全过 |
| `issue-cluster-narrative-v1-candidate.yml` | `问题簇命名与解释-v1-candidate` | `DIFY_CLUSTER_WORKFLOW_API_KEY` | 已发布；flash 回放 30/30 通过 |
| `sop-draft-v1-candidate.yml` | `候选SOP草案-v1-candidate` | `DIFY_SOP_WORKFLOW_API_KEY` | 已发布；flash 回放 5/5 通过 |
| `weekly-report-narrative-v1-candidate.yml` | `运营周报叙事-v1-candidate` | `DIFY_REPORT_WORKFLOW_API_KEY` | 已发布；flash 回放 5/6，未达门槛 |

## flash 回放结果（2026-08-01）

锁定集沿用 V7 冻结集（`v7-frozen-signature-clustering-holdout-20260702`，N=60），按当前 flash DSL 与代码重新冻结为 `v7-flash-frozen-signature-clustering-holdout-20260719`，全部 60 行真实 Dify 调用一次成功。

### 结构化工作流 `feedback-structuring-v3-candidate`（九项质量门全部通过）

| 指标 | flash 实测 | 门槛 | V7 历史 |
|---|---:|---:|---:|
| Schema 契约有效率 | 100% | 95% | 100% |
| 问题类型 Macro-F1 | 0.828 | 0.80 | 0.846 |
| 产品区域 Macro-F1 | 0.984 | 0.80 | 0.963 |
| 责任路由一致率 | 85.0% | 85% | 85.0% |
| 高风险升级召回率 | 100% | 100% | 100% |
| quote 自动定位 | 100% | 95% | 100% |
| 重复识别精确率 | 100% | 80% | 84.2% |
| 重复识别召回率 | 50.0% | 50% | 53.3% |
| B³ F1 | 0.857 | 0.75 | 0.853 |

首次依赖成功率为 100%（V7 为 88.3%），聚类纯度为 100%（V7 为 96.7%）。评测状态 `candidate_scored_unpromoted`，`eligible_for_manual_promotion`。

### 内容工作流套件（未达晋升门槛）

| 工作流 | flash 实测 | 历史 |
|---|---:|---:|
| 问题簇叙事 | 30/30 | 30/30 |
| 候选 SOP | 5/5 | 5/5 |
| 周报叙事 | 5/6 | 6/6 |

周报叙事 batch-5 失败原因为工作流内安全门禁拦截（`ValueError: forbidden_irreversible_action`，Dify sandbox 拒绝），即模型输出触发“不可逆动作”校验被拒绝，不是网络或基础设施故障。按门槛 100%，内容套件不得晋升，套件整体保持 `published_pending_revalidation`；修复或重新冻结周报工作流后需再次回放与复核。

权威文件（flash）：

- `data/v7-evaluation/v7-flash-frozen-20260719-manifest.json`
- `artifacts/evaluation-v7-flash-candidate/evaluation.json`
- `artifacts/evaluation-v7-flash-candidate/status.json`
- `artifacts/evaluation-v7-flash-candidate/analysis-cache.json`
- `artifacts/workflow-suite-v1-flash-candidate/evaluation.json`

真实 Key 只在 `.env`，不进入仓库、聊天、截图或作品材料。

## 已激活的服务端约束

- 模型只输出 `quote`；服务端 exact match、规范化匹配并计算 offset。
- 最终责任方、严重度和升级由规则裁决，不盲信模型值。
- 问题簇、SOP 和周报中的 ticket ID 必须是确定性输入的子集，后端再次校验。
- 候选 SOP 始终为 `pending_review`，不会自动更改正式知识库或执行不可逆动作。
- 周报数字由确定性服务计算；模型只生成文案，根因只能标为“待确认原因”。
- Dify 调用失败时可降级为确定性文案，并持久化 `generation_source` / `workflow_version`。

## V7 历史结果（模型切换前）

以下结果只属于模型切换前冻结的 DSL 与哈希，不适用于当前 flash 配置。锁定集：`v7-frozen-signature-clustering-holdout-20260702`，N=60。

| 指标 | 结果 | 门槛 |
|---|---:|---:|
| Schema 契约有效率 | 100% | 95% |
| 问题类型 Macro-F1 | 0.846 | 0.80 |
| 产品区域 Macro-F1 | 0.963 | 0.80 |
| 责任路由一致率 | 85.0% | 85% |
| 高风险升级召回率 | 100% | 100% |
| quote 自动定位 | 100% | 95% |
| 重复识别精确率 | 84.2% | 80% |
| 重复识别召回率 | 53.3% | 50% |
| B³ F1 | 0.853 | 0.75 |

首次依赖成功率为 88.3%，作为可靠性信息项单独展示，不降低 Schema 契约有效率。聚类纯度为 96.7%。

权威文件：

- `data/v7-evaluation/v7-manifest.json`
- `artifacts/evaluation-v7-candidate/evaluation.json`
- `artifacts/evaluation-v7-candidate/status.json`
- `artifacts/evaluation-v7-candidate/promotion-record.json`

## 失败历史与边界

V5 因问题类型、责任路由、重复识别精确率与召回率未达门槛而未晋级。V6 的问题类型 F1 达 0.901，但聚类精确率 57.1%、召回率 40.0%，仍未晋级。V7 使用全新冻结集，不把已读的 V5/V6 继续包装成未见评测。

V7 标签是 AI 辅助一致性复核，不是独立人工审计；结果不外推当前 flash、真实业务分布、效率收益或生产 SLA。当前 flash 已回放但内容套件未达门槛，不恢复 `promoted_for_portfolio_demo` 状态。
