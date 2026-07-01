import { PageHead } from "@/components/UI";

export default function AboutPage() {
  return <><PageHead eyebrow="BOUNDARIES" title="这个作品证明什么，也不证明什么。" description="把合成机制、模型建议与真实业务能力分开，是系统的一部分。" /><section className="three-col"><article className="panel"><span className="kicker">已证明</span><h2>机制可运行</h2><p>Schema、证据定位、规则路由、会话审核、聚类评测与周报引用可以自动复跑。</p></article><article className="panel"><span className="kicker amber">部分支持</span><h2>合成质量</h2><p>N=60 锁定集可说明合成场景表现，不能代表真实客户语言和真实问题分布。</p></article><article className="panel"><span className="kicker red">未证明</span><h2>业务收益</h2><p>没有真实效率提升、客户满意度、生产稳定性或真实根因准确率证据。</p></article></section><section className="panel flow"><span>非结构化反馈</span><b>→</b><span>LLM 建议</span><b>→</b><span>确定性硬门</span><b>→</b><span>人工确认</span><b>→</b><span>候选改进</span></section></>;
}

