# 部署与运维

## WSL2

```bash
cd /srv/stack/feedback-analysis-agent
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:18100/feedback
```

服务：

- `feedback-web`：`127.0.0.1:18100`。
- `feedback-api`：Docker 内部 `8101`，加入 `shared-net`。
- `feedback-worker`：持久化任务消费者。
- `feedback-postgres`：无宿主机端口。

Tailscale：

```bash
sudo tailscale serve --bg --yes --tcp=8100 tcp://127.0.0.1:18100
```

## 云端

云端 Nginx 的 `/feedback` 与 `/feedback/` 转发至 `metratio.tail1f4641.ts.net:8100`。`^~ /feedback/` 用于防止 Next.js 的 JS/CSS 被静态资源正则截获。

静态作品页位于：

```text
/srv/stack/nginx/metratio-static/index/feedback/index.html
```

云端 Nginx 已为 `/index/feedback` 和 `/index/feedback/` 配置独立静态路由；必须放在通用 `/index` location 之前，否则请求会回落到站点总首页。

## 监控

- Prometheus job：`feedback-analysis`。
- Blackbox：`https://metratio.com/feedback`。
- Grafana UID：`feedback-analysis`。
- 指标：工单、问题簇、候选 SOP、待复核、请求率和 p95 延迟。

## 更新流程

```bash
uv run pytest
uv run ruff check feedback_app tools tests migrations
docker compose build
docker compose up -d
docker compose ps
```

Nginx 修改必须先备份、运行 `nginx -t`，成功后再 reload。

运行时迁移与回归检查：

```bash
docker compose exec feedback-api alembic current
docker compose exec feedback-api alembic check
curl -fsS http://127.0.0.1:18100/feedback/api/health
```

## v2 候选激活

候选 DSL 导入与 API Key 创建必须由项目所有者在 Dify 控制台完成，具体见 `docs/activation-checklist.md`。配置候选 Key 后执行：

```bash
cd /srv/stack/feedback-analysis-agent
./tools/run_candidate_evaluation.sh
```

候选结果写入独立目录 `artifacts/evaluation-v2-candidate/`，不会自动覆盖 `artifacts/evaluation/` 的 v1 官方基线。候选提示词哈希不匹配、审计行与锁定集不一致或存在未复核行时，评测会直接失败。

公网 BFF 会把 HttpOnly 会话 cookie 转成内部 `X-Demo-Session`，并将可信代理链末端地址传给 API 生成单向哈希。API 同时执行会话、来源和全站三级日限额；原始地址不持久化。
