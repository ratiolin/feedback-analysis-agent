import { api } from "@/lib/api";
import { Metric, PageHead } from "@/components/UI";

export default async function EvaluationPage() {
  const [baseline, suite] = await Promise.all([
    api.evaluation(),
    api.suiteEvaluation(),
  ]) as any[];
  const latest = suite.structure_clustering ?? {};
  const structure = latest.structure ?? {};
  const clustering = latest.clustering?.holdout_metrics ?? {};
  const workflows = suite.content_workflows ?? {};
  const problemF1 = structure.problem_type?.report?.["macro avg"]?.["f1-score"] ?? 0;
  const areaF1 = structure.product_area?.report?.["macro avg"]?.["f1-score"] ?? 0;
  const failed = (latest.quality_gates?.items ?? []).filter((gate: any) => !gate.passed);
  const contentMetrics = workflows.metrics ?? {};
  const baselineFailed = (baseline.quality_gates?.items ?? []).filter((gate: any) => !gate.passed);

  return <>
    <PageHead eyebrow="EVALUATION" title="先展示失败，再解释通过。" description="v5 锁定合成集 N=60，仅用于机制质量评估；AI 辅助复核不等于独立人工审计，也不代表真实业务分布。" />
    <section className="panel">
      <h2>四工作流套件 v5：已评分，未晋级</h2>
      <p>状态：{suite.evaluation_state}；数据：{suite.dataset_version}。内容生成工作流全部通过，但结构化与聚类仍有四项质量门失败，因此整体候选不替换公开基线。</p>
      <p className="callout">未通过：{failed.map((gate: any) => `${gate.label} ${Number(gate.actual).toFixed(3)} / ${Number(gate.threshold).toFixed(2)}`).join("；")}。</p>
    </section>
    <h2>结构化与重复问题识别</h2>
    <section className="metrics-grid">
      <Metric label="问题类型 Macro-F1" value={problemF1.toFixed(3)} detail="门槛 0.80，未通过" />
      <Metric label="产品区域 Macro-F1" value={areaF1.toFixed(3)} detail="门槛 0.80，通过" />
      <Metric label="quote 自动定位" value={`${((structure.evidence_auto_location_rate ?? 0) * 100).toFixed(1)}%`} detail="失败进入人工复核" />
      <Metric label="责任路由一致率" value={`${((structure.owner_policy_consistency ?? 0) * 100).toFixed(1)}%`} detail="门槛 85%，未通过" />
      <Metric label="重复识别精确率" value={`${((clustering.pairwise?.precision ?? 0) * 100).toFixed(1)}%`} detail="错误合并仍需收敛" />
      <Metric label="重复识别召回率" value={`${((clustering.pairwise?.recall ?? 0) * 100).toFixed(1)}%`} detail="门槛 50%，未通过" />
      <Metric label="聚类纯度" value={`${((clustering.purity ?? 0) * 100).toFixed(1)}%`} detail="面试展示指标" />
      <Metric label="B³ F1" value={(clustering.b_cubed?.f1 ?? 0).toFixed(3)} detail="技术报告指标" />
    </section>
    <h2>内容生成工作流</h2>
    <section className="metrics-grid">
      <Metric label="问题簇叙事" value={`${((contentMetrics.cluster_success_rate ?? 0) * 100).toFixed(0)}%`} detail={`${workflows.attempts?.cluster ?? 0} 次真实调用`} />
      <Metric label="候选 SOP" value={`${((contentMetrics.sop_success_rate ?? 0) * 100).toFixed(0)}%`} detail={`${workflows.attempts?.sop ?? 0} 次真实调用`} />
      <Metric label="周报叙事" value={`${((contentMetrics.report_success_rate ?? 0) * 100).toFixed(0)}%`} detail={`${workflows.attempts?.report ?? 0} 次真实调用`} />
      <Metric label="证据引用有效" value={`${((contentMetrics.evidence_valid_rate ?? 0) * 100).toFixed(0)}%`} detail="服务端再次校验 ticket_id" />
    </section>
    <section className="two-col"><div className="panel"><h2>错误合并案例</h2><pre>{JSON.stringify(latest.clustering?.false_merge_examples ?? [], null, 2)}</pre></div><div className="panel"><h2>错误拆分案例</h2><pre>{JSON.stringify(latest.clustering?.false_split_examples ?? [], null, 2)}</pre></div></section>
    <p className="callout">公开 v1 基线仍保留；其未通过项为：{baselineFailed.map((gate: any) => gate.label).join("、") || "无"}。v5 已被读取并评分，后续调参必须生成全新的 v6 锁定集，不能反复利用 v5。</p>
  </>;
}
