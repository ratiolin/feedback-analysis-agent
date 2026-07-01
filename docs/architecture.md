# 架构与数据流

## 模块地图

```text
公网浏览器
  │ /feedback
  ▼
云端 Nginx ── Tailscale Serve :8100 ── Next.js :18100
                                           │ BFF（会话 cookie）
                                           ▼
                                      FastAPI :8101
                                      ├─ PostgreSQL
                                      ├─ Worker
                                      ├─ Dify Workflow → DeepSeek
                                      └─ BGE-small-zh-v1.5
```

云服务器只承担 TLS、公网入口和静态作品页；业务服务与数据库运行在 WSL2。

## 权威边界

| 能力 | 提议者 | 最终裁决 |
|---|---|---|
| 摘要、问题类型、产品区域 | LLM | Schema + 人工复核 |
| evidence quote | LLM | 服务端 exact/NFKC 定位 |
| start/end | 无 | 服务端写入 |
| 责任方 | LLM 仅留 trace | 规则映射 |
| 严重度、升级 | LLM 提取影响信号 | 规则映射 |
| 根因 | 待确认假设 | 不进入事实结论 |
| 聚类成员 | 向量相似度 | 冻结阈值 + 错误案例评测 |
| SOP 发布 | LLM 可起草 | 仅人工会话审核；不发布正式库 |

## 状态与失败

分析任务状态：`queued → processing → completed | needs_review | failed`。

- Dify/DeepSeek 未配置时，公开演示使用透明 `demo_rules`，结果字段明确标记来源。
- Dify 超时或无效结构最多重试两次，退避为 2 秒、8 秒；仍失败不得伪造结果。

## 工作流版本状态

- `客户反馈结构化-v1`：当前已发布官方基线；v3 锁定集真实回放存在未通过质量门。
- `客户反馈结构化-v2-candidate`：候选规则，仅存在于独立 DSL 和候选状态目录；导入、真实回放和晋级前不得替代 v1。
- 候选提示词与锁定集通过 SHA-256 绑定。提示词变化会使评测前置校验失败，防止用锁定集调参后继续沿用旧分数。
- evidence 无法唯一、可映射地定位时进入 `needs_review`。
- Worker 任务持久化在 PostgreSQL，重启后继续领取。
- Worker 每分钟回收超过 120 秒仍处于 `processing` 的陈旧任务，重新排队而不是永久卡住。
- 重复分析缓存只接受完全相同的脱敏原文与工作流版本，不复用规范化后“近似相同”文本的 offset。
- 工单详情、任务轮询和审核写入均校验会话归属；公共种子可读，其他会话的实时数据返回 404。
- 会话有效期为 24 小时，Worker 周期性删除过期会话及其工单、任务、分析和审核记录。
