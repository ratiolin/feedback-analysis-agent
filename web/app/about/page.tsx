import { PageHead } from "@/components/UI";

export default function AboutPage() {
  return <>
    <PageHead eyebrow="BOUNDARIES" title="这个作品证明什么，也不证明什么。" description="把模型建议、确定性约束、候选知识与正式规则分开，是系统本身的一部分。" />
    <section className="three-col">
      <article className="panel"><span className="kicker">已证明</span><h2>四工作流真实可运行</h2><p>结构化、问题簇叙事、候选 SOP、周报叙事均已发布并完成真实 API 回放；证据 ID 仍由服务端确定性复核。</p></article>
      <article className="panel"><span className="kicker amber">部分支持</span><h2>合成机制质量</h2><p>内容生成工作流门禁全部通过；v5 的问题类型、责任路由和重复识别仍未达门槛，因此整个套件保持候选状态。</p></article>
      <article className="panel"><span className="kicker red">未证明</span><h2>真实业务收益</h2><p>没有独立人工审计、真实效率提升、客户满意度、生产稳定性或真实根因准确率证据。</p></article>
    </section>
    <section className="panel flow"><span>非结构化反馈</span><b>→</b><span>LLM 建议</span><b>→</b><span>确定性硬门</span><b>→</b><span>人工确认</span><b>→</b><span>候选改进</span></section>
  </>;
}
