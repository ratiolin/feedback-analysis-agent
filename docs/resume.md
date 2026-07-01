# 简历描述候选

**客户反馈结构化分析 Agent｜个人项目**

设计并实现面向项目协作 SaaS 的客户反馈工作流，支持工单导入、结构化分类、确定性责任路由、重复问题聚类、候选 SOP 和可追溯周报。采用“LLM 建议 + Schema/证据硬门 + 人工确认”边界，模型只输出逐字 quote，由服务端定位 offset；根因假设不进入周报事实结论，候选 SOP 不自动进入正式知识库。基于 240 条合成工单构建开发集与锁定评测集，公开混淆矩阵、错误合并/拆分案例和证据边界；使用 FastAPI、Next.js、Dify、DeepSeek、BGE、PostgreSQL、Docker Compose、Prometheus 与 Grafana 完成公网演示。

在 DeepSeek/Dify 锁定集评测达标前，不在简历中填写 Macro-F1、准确率或效率提升数字。

当前 v1 真实回放的问题类型 Macro-F1 未达门槛；v2 仍是未评测候选。简历只能描述机制、边界和可复跑评测，不得把 v2 写成已提升。
