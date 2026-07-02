# v2 候选工作流激活清单（历史记录）

本文件记录 V2 当时的激活与失败，不是当前运行配置。V2 已发布并完成锁定评测，但聚类门禁失败，状态为 `candidate_scored_unpromoted`。当前作品集演示已依据独立 promotion record 使用通过 V7 门禁的 `客户反馈结构化-v3-candidate`；生产级“官方基线”仍未被本项目证明。

## 项目所有者步骤（已完成）

1. 打开 Dify 控制台，进入“工作室”。
2. 选择“导入 DSL 文件”，导入：

   ```text
   D:\download\ratio\客户反馈项目\dify-workflows\feedback-structuring-v2-candidate.yml
   ```

3. 确认应用名为 `客户反馈结构化-v2-candidate`，LLM 节点使用 `deepseek-v4-pro`。
4. 发布工作流，在“访问 API”创建该候选应用的 API Key。
5. 在 WSL 的 `/srv/stack/feedback-analysis-agent/.env` 中，把 `DIFY_FEEDBACK_WORKFLOW_API_KEY` 替换为新候选应用的 Key。不要把真实 Key 写入聊天、GitHub 或作品材料。
6. 只回复“v2 已导入并配置 Key”。后续真实回放、质量门判断、展示页更新和候选晋级由自动化继续执行。

## 自动化结果

- v2 候选 DSL 已冻结，SHA-256：`47bcd77f2aa5b0b472a6b2df51266875ce1329f31ca72a947555de8dddb77178`。
- 新锁定集 `v4-frozen-candidate-holdout-20260702` 已生成，共 60 条、30 个问题族。
- v4 已完成 60/60 条 AI 辅助一致性复核；它不是独立人工审计。
- v4 已完成真实 Dify + BGE 回放；结构化 6 项门禁全部通过。
- 聚类门禁失败：30/30 个问题族被拆分，重复匹配精确率/召回率 0，B³ F1 0.667。
- v2 未晋升，v1 仍是公开基线。v4 不得再用于调参后的正式评测。

## 可复跑命令

```bash
cd /srv/stack/feedback-analysis-agent
./tools/run_candidate_evaluation.sh
```

脚本会重建使用候选 Key 的 API/Worker 容器，在 v4 锁定集上运行真实 Dify + BGE 评测，并输出到 `artifacts/evaluation-v2-candidate/`。当前结果只用于可复现性检查；不得根据 v4 调参后再次将其作为未见锁定评测。只有全新锁定集的所有已测质量门通过并完成结果复核后，候选才可晋级。
