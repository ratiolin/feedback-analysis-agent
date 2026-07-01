# 最后激活清单

以下两项需要项目所有者本人完成；自动化代理不能代替账户授权，也不能把模型生成的判断伪装成独立人工抽检。

## 1. 激活 Dify 工作流

1. 打开 Dify 控制台，进入“工作室”。
2. 选择“导入 DSL”，导入：

   ```text
   D:\download\ratio\客户反馈项目\dify-workflows\feedback-structuring-v1.yml
   ```

3. 确认 LLM 节点可使用 `deepseek-v4-pro`，然后发布工作流。
4. 在该工作流的“访问 API”页面创建 API Key。
5. 在 WSL 内编辑 `/srv/stack/feedback-analysis-agent/.env`，只在本机填写：

   ```dotenv
   DIFY_FEEDBACK_WORKFLOW_API_KEY=app-你的真实密钥
   ```

不要把真实密钥发到聊天、GitHub 或作品材料目录。完成后只需回复“Dify 已配置”。后续容器重启、真实工作流冒烟测试、N=60 回放评测和结果发布由自动化继续执行。

## 2. 完成人工抽检

打开：

```text
D:\download\ratio\客户反馈项目\data\manual-audit\holdout-audit.csv
```

逐行检查 `message` 与 gold 标签是否语义一致，填写：

- `audit_label_text_consistent`：`yes` 或 `no`；
- `audit_notes`：不一致时说明问题；
- `auditor`：审核者标识，可使用姓名缩写。

必须审核全部 60 行。该步骤只检查合成样本与人工标签的一致性，不代表真实业务分布，也不能证明生产收益。完成后保存原文件并回复“人工抽检已完成”。

## 自动化恢复后将执行

- 校验 60 行均有人工结论，汇总不一致样本；
- 对 Dify 工作流运行锁定 holdout，生成分类报告、混淆矩阵和聚类错误案例；
- 检查 evidence 原文定位率、owner 规则一致率、升级召回率与聚类质量门；
- 若质量门不通过，保留失败证据并迭代工作流，不发布虚假漂亮指标；
- 重新生成评测页、部署、运行公网 E2E、提交 GitHub 并等待 CI。
