# 四工作流套件导入清单

当前套件状态为 `candidate_awaiting_import`。结构化 v2 已有真实冻结回放记录；另外三个工作流只是已完成静态验证的候选，导入和真实调用前不得写成已上线或已达标。

## 文件与应用

| 顺序 | DSL 文件 | 导入后的应用名 | API Key 环境变量 |
|---:|---|---|---|
| 1 | `feedback-structuring-v2-candidate.yml` | `客户反馈结构化-v2-candidate` | `DIFY_FEEDBACK_WORKFLOW_API_KEY` |
| 2 | `issue-cluster-narrative-v1-candidate.yml` | `问题簇命名与解释-v1-candidate` | `DIFY_CLUSTER_WORKFLOW_API_KEY` |
| 3 | `sop-draft-v1-candidate.yml` | `候选SOP草案-v1-candidate` | `DIFY_SOP_WORKFLOW_API_KEY` |
| 4 | `weekly-report-narrative-v1-candidate.yml` | `运营周报叙事-v1-candidate` | `DIFY_REPORT_WORKFLOW_API_KEY` |

结构化 v2 如果仍存在且 Key 可用，不要重复导入；只需连续导入后面三个文件。四个应用均确认使用 `deepseek-v4-pro`、发布并分别创建 API Key。

## 一次性配置

在 WSL 的 `/srv/stack/feedback-analysis-agent/.env` 中配置：

```dotenv
DIFY_FEEDBACK_WORKFLOW_API_KEY=app-existing-structure-key
DIFY_CLUSTER_WORKFLOW_API_KEY=app-new-cluster-key
DIFY_SOP_WORKFLOW_API_KEY=app-new-sop-key
DIFY_REPORT_WORKFLOW_API_KEY=app-new-report-key
```

不要把真实 Key 写入聊天、GitHub、截图或作品材料。新变量在导入后的后端接入步骤中启用；当前生产代码尚不会调用后三个 Key。

## 已在 DSL 内处理的已知边界

- 结构化只输出原文 `quote`，不输出 start/end；责任方、严重度和升级由后端裁决。
- 问题簇文案的证据 ID 必须来自输入代表工单。
- SOP 不输出审批状态，不执行或建议不可逆动作，证据 ID 必须来自输入。
- 周报不重新计算数字，且每条证据必须属于对应问题簇。
- 四个工作流都把业务文本视为不可信数据，并要求根因只进入“待确认原因”。

## 不属于 YML 的已知问题

BGE 聚类的旧开发集包含同族重复文本，导致阈值 0.85 无法识别真实改写。该问题必须在导入后通过“重建改写开发集 → 仅在开发集选阈值 → 生成全新 v5 锁定集”修复，不能通过增加 Dify 节点解决，也不能复用 v4 调参后宣称未见评测。

完成导入与 `.env` 配置后，只回复：`四工作流已发布并配置 Key`。随后再执行后端适配、真实 canary、聚类修复、v5 评测、展示页和文档更新。
