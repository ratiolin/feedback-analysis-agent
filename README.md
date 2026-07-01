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
Python 自动测试：17
```

公开评测当前明确标记为 `demo_rules` 故障兜底：Schema 和 quote 定位机制可复跑，但分类、升级和聚类质量尚未过门，不得写成模型质量成果。DeepSeek/Dify 工作流导入并完成 N=60 复跑后，才可更新公开质量结论。

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

模型评测：

```bash
uv run python tools/evaluate.py --analyzer demo --embedding tfidf

# Dify 工作流配置完成后
DIFY_FEEDBACK_WORKFLOW_API_KEY='app-...' \
uv run python tools/evaluate.py --analyzer dify --embedding bge
```

## 目录

```text
feedback_app/       FastAPI、Worker、规则、聚类和周报
web/                Next.js 产品看板与匿名会话 BFF
dify-workflows/     可导入 Dify 1.13.3 的结构化工作流 DSL
tools/              数据生成、种子和离线评测
tests/              规则、证据、数据、聚类和报告测试
portfolio/          静态作品页
docs/               架构、部署、评测边界与人工审核说明
```

## 数据与安全

- 数据全部为虚构合成样本。
- 在线输入最长 2,000 字；CSV 最大 1 MB、10 行。
- 邮箱、手机号和疑似密钥在持久化及模型调用前脱敏。
- 公网实时分析限制为每会话每天 5 条、全站每天 100 条。
- API、Postgres 和 Worker 不暴露公网，仅 Next.js 通过 BFF 访问。
- 密钥只允许放 `.env`，仓库只提供 `.env.example`。

详见 `docs/architecture.md`、`docs/evaluation-boundary.md` 和 `docs/deployment.md`。

