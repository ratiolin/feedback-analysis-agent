import { api } from "@/lib/api";
import { Metric, PageHead } from "@/components/UI";

export default async function EvaluationPage() {
  const data = await api.evaluation() as any;
  const structure = data.structure ?? {};
  const clustering = data.clustering?.holdout_metrics ?? {};
  const problemF1 = structure.problem_type?.report?.["macro avg"]?.["f1-score"] ?? 0;
  return <><PageHead eyebrow="EVALUATION" title="先展示错误，再展示分数。" description="锁定人工校验集 N=60，仅用于合成场景机制评估，不代表真实业务分布。" />
    <section className="metrics-grid"><Metric label="问题类型 Macro-F1" value={problemF1.toFixed(3)} detail="含每类 support 与混淆矩阵" /><Metric label="证据自动定位" value={`${((structure.evidence_auto_location_rate ?? 0) * 100).toFixed(1)}%`} detail="失败进入人工复核" /><Metric label="重复匹配精确率" value={`${((clustering.pairwise?.precision ?? 0) * 100).toFixed(1)}%`} detail="不是全样本 accuracy" /><Metric label="聚类纯度" value={`${((clustering.purity ?? 0) * 100).toFixed(1)}%`} detail="B³ F1 留在技术报告" /></section>
    <section className="two-col"><div className="panel"><h2>错误合并案例</h2><pre>{JSON.stringify(data.clustering?.false_merge_examples ?? [], null, 2)}</pre></div><div className="panel"><h2>错误拆分案例</h2><pre>{JSON.stringify(data.clustering?.false_split_examples ?? [], null, 2)}</pre></div></section>
    <p className="callout">当前 demo_rules 是透明故障兜底，不满足模型质量门；只有 DeepSeek/Dify 锁定集复跑达标后才更新公开质量结论。</p>
  </>;
}

