# 客户反馈结构化分析 Agent

面向虚构项目协作 SaaS 的工单结构化、重复问题聚类、候选 SOP 与周报演示系统。

- 交互演示：<https://metratio.com/feedback>
- 作品说明：<https://metratio.com/index/feedback>
- 评测页面：<https://metratio.com/feedback/evaluation>

## 定位

系统把客服工单转化为可审核、可追溯的问题池：

```text
CSV / 在线工单
→ Dify + DeepSeek 结构化建议
→ Schema / quote 定位 / 责任路由 / 严重度硬门
→ BGE 中文向量聚类
→ 候选 SOP
→ 可下钻到 ticket_id 的周报
```

边界：

- LLM 只输出摘要、分类建议、逐字 `quote` 和待确认原因。
- 服务端负责原文 offset、责任方、严重度、升级与人工复核。
- 根因假设只能进入“待确认原因”，不能进入周报事实结论。
- 候选 SOP 不会自动进入正式知识库。
- 公开审核只写入 24 小时匿名会话沙箱。
- 合成数据不能证明真实业务收益、真实分布或生产 SLO。

## 当前证据

```text
合成工单：240（开发/演示 180，锁定抽检 60）
问题类型：8
产品区域：8
初始 BGE 问题簇：63
候选 SOP：2
Python 自动测试：37
```

当前公开基线来自已发布 `客户反馈结构化-v1` 的真实 Dify + BGE 回放（数据版本 `v3-natural-singletons`）。Schema、quote 定位、产品区域、升级召回与聚类指标通过门槛；问题类型 Macro-F1 为 0.647、责任路由策略一致率为 83.3%，未通过 0.80/0.85 门槛。因此只能声明机制已实现，不能声明整体分类质量达标。

`客户反馈结构化-v2-candidate` 已冻结为候选 DSL，并配套全新 `v4-frozen-candidate-holdout-20260702` 锁定集。v4 已完成 60/60 条 AI 辅助一致性复核，但尚未运行模型评测；不得把候选状态写成质量提升。导入步骤见 `docs/activation-checklist.md`。

## 快速开始

```bash
cp .env.example .env
# 设置 FEEDBACK_DB_PASSWORD；Dify 工作流导入后再设置 API Key
docker compose up -d --build

docker compose --profile seed run --rm feedback-seed
curl http://127.0.0.1:18100/feedback
```

本地开发：

```bash
uv sync --extra dev
uv run python tools/generate_dataset.py
uv run pytest
uv run ruff check feedback_app tools tests migrations

docker run --rm -v "$PWD/web:/app" -w /app node:22-alpine \
  sh -lc 'npm ci && npm audit --audit-level=moderate && npm run lint && npm run build'
```

模型评测与候选激活：

```bash
uv run python tools/evaluate.py --analyzer demo --embedding tfidf

# 导入并配置 v2 候选 Key 后，在 WSL 执行
./tools/run_candidate_evaluation.sh
```

## 目录

```text
feedback_app/       FastAPI、Worker、规则、聚类和周报
web/                Next.js 产品看板与匿名会话 BFF
dify-workflows/     已发布 v1 基线与可导入的 v2 候选 DSL
tools/              数据生成、种子和离线评测
tests/              规则、证据、数据、聚类和报告测试
portfolio/          静态作品页
docs/               架构、部署、评测边界与人工审核说明
```

## 数据与安全

- 数据全部为虚构合成样本。
- 在线输入最长 2,000 字；CSV 最大 1 MB、10 行。
- 邮箱、手机号和疑似密钥在持久化及模型调用前脱敏。
- 公网实时分析限制为每会话每天 5 条、每来源每天 10 条、全站每天 100 条；刷新或清除 cookie 不能绕过来源限额。
- API、Postgres 和 Worker 不暴露公网，仅 Next.js 通过 BFF 访问。
- 密钥只允许放 `.env`，仓库只提供 `.env.example`。
- `Idempotency-Key` 在数据库中按会话唯一，并处理并发插入竞争；重复请求返回原任务。
- 仅对“工作流版本 + 脱敏后原文完全一致”的输入复用分析，避免 evidence offset 因空格或标点差异错位。
- 实时工单、任务与审核结果按匿名会话隔离；过期会话由 Worker 清理。

详见 `docs/architecture.md`、`docs/evaluation-boundary.md` 和 `docs/deployment.md`。

激活 v2 候选时按 `docs/activation-checklist.md` 执行；真实密钥不得进入仓库。AI 辅助复核不等于独立人工审计。
