# v2 候选工作流激活清单

当前官方基线仍是已发布的 `客户反馈结构化-v1`。`v2` 处于候选状态，尚未运行模型评测，不得写成已提升或已达标。

## 需要项目所有者完成

1. 打开 Dify 控制台，进入“工作室”。
2. 选择“导入 DSL 文件”，导入：

   ```text
   D:\download\ratio\客户反馈项目\dify-workflows\feedback-structuring-v2-candidate.yml
   ```

3. 确认应用名为 `客户反馈结构化-v2-candidate`，LLM 节点使用 `deepseek-v4-pro`。
4. 发布工作流，在“访问 API”创建该候选应用的 API Key。
5. 在 WSL 的 `/srv/stack/feedback-analysis-agent/.env` 中，把 `DIFY_FEEDBACK_WORKFLOW_API_KEY` 替换为新候选应用的 Key。不要把真实 Key 写入聊天、GitHub 或作品材料。
6. 只回复“v2 已导入并配置 Key”。后续真实回放、质量门判断、展示页更新和候选晋级由自动化继续执行。

## 已由自动化完成

- v2 候选 DSL 已冻结，SHA-256：`47bcd77f2aa5b0b472a6b2df51266875ce1329f31ca72a947555de8dddb77178`。
- 新锁定集 `v4-frozen-candidate-holdout-20260702` 已生成，共 60 条、30 个问题族。
- v4 已完成 60/60 条 AI 辅助一致性复核；它不是独立人工审计。
- v4 尚未运行模型评测，且不得用于修改 v2 提示词。任何提示词变更都会导致哈希校验失败，必须生成新版本锁定集。

## 导入后的自动化命令

```bash
cd /srv/stack/feedback-analysis-agent
./tools/run_candidate_evaluation.sh
```

脚本会重建使用新 Key 的 API/Worker 容器，在 v4 锁定集上运行真实 Dify + BGE 评测，并输出到 `artifacts/evaluation-v2-candidate/`。只有所有已测质量门通过并完成结果复核后，候选结果才可晋级为公开基线。
