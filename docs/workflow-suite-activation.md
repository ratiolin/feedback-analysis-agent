# 四工作流套件激活记录

当前状态为 `promoted_for_portfolio_demo`。四个 Dify 应用已导入、发布、配置独立 API Key，并完成真实 API 契约验证。V7 的九项已测质量门全部通过，晋级范围仅限合成作品集演示。

## 应用与 Key

| DSL 文件 | 应用 | API Key 环境变量 | 回放状态 |
|---|---|---|---|
| `feedback-structuring-v3-candidate.yml` | `客户反馈结构化-v3-candidate` | `DIFY_FEEDBACK_WORKFLOW_API_KEY` | V7 锁定集 60/60 已捕获；7 次首次依赖失败经重试恢复 |
| `issue-cluster-narrative-v1-candidate.yml` | `问题簇命名与解释-v1-candidate` | `DIFY_CLUSTER_WORKFLOW_API_KEY` | 30/30 成功 |
| `sop-draft-v1-candidate.yml` | `候选SOP草案-v1-candidate` | `DIFY_SOP_WORKFLOW_API_KEY` | 5/5 成功 |
| `weekly-report-narrative-v1-candidate.yml` | `运营周报叙事-v1-candidate` | `DIFY_REPORT_WORKFLOW_API_KEY` | 6/6 成功 |

真实 Key 只在 `.env`，不进入仓库、聊天、截图或作品材料。

## 已激活的服务端约束

- 模型只输出 `quote`；服务端 exact match、规范化匹配并计算 offset。
- 最终责任方、严重度和升级由规则裁决，不盲信模型值。
- 问题簇、SOP 和周报中的 ticket ID 必须是确定性输入的子集，后端再次校验。
- 候选 SOP 始终为 `pending_review`，不会自动更改正式知识库或执行不可逆动作。
- 周报数字由确定性服务计算；模型只生成文案，根因只能标为“待确认原因”。
- Dify 调用失败时可降级为确定性文案，并持久化 `generation_source` / `workflow_version`。

## V7 结果

锁定集：`v7-frozen-signature-clustering-holdout-20260702`，N=60。

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

V7 标签是 AI 辅助一致性复核，不是独立人工审计；结果不外推真实业务分布、效率收益或生产 SLA。
