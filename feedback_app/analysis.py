from .evidence import locate_evidence
from .routing import derive_severity, needs_escalation, route_owner, supplement_impact_signals
from .schemas import FinalAnalysis, LLMAnalysis, ReviewStatus


def finalize_analysis(
    message: str,
    llm_analysis: LLMAnalysis,
    workflow_version: str,
    analysis_source: str,
) -> FinalAnalysis:
    evidence = locate_evidence(message, llm_analysis.evidence_spans)
    impact_signals = supplement_impact_signals(message, llm_analysis.impact_signals)
    severity = derive_severity(impact_signals)
    owner = route_owner(llm_analysis.problem_type, llm_analysis.product_area)
    review_reasons = list(evidence.failures)
    if not evidence.located:
        review_reasons.append("no_located_evidence")
    review_status = ReviewStatus.NEEDS_REVIEW if review_reasons else ReviewStatus.ACCEPTED
    return FinalAnalysis(
        summary=llm_analysis.summary,
        problem_type=llm_analysis.problem_type,
        product_area=llm_analysis.product_area,
        sentiment=llm_analysis.sentiment,
        suggested_owner=owner,
        llm_owner_suggestion=llm_analysis.llm_owner_suggestion,
        root_cause_hypothesis=llm_analysis.root_cause_hypothesis,
        impact_signals=impact_signals,
        evidence_spans=evidence.located,
        severity=severity,
        needs_escalation=needs_escalation(severity, impact_signals),
        review_status=review_status,
        review_reasons=review_reasons,
        workflow_version=workflow_version,
        analysis_source=analysis_source,
    )
