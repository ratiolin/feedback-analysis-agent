from .schemas import ImpactSignals, Owner, ProblemType, ProductArea, Severity


def route_owner(problem_type: ProblemType, product_area: ProductArea) -> Owner:
    if problem_type == ProblemType.PERFORMANCE:
        return Owner.ENGINEERING_TRIAGE
    if problem_type == ProblemType.DATA_CONSISTENCY:
        return Owner.QA_TRIAGE
    if problem_type == ProblemType.FEATURE_REQUEST:
        return Owner.PRODUCT_OPS
    if problem_type == ProblemType.INTEGRATION or product_area == ProductArea.OPEN_API:
        return Owner.TECHNICAL_SUPPORT
    if problem_type == ProblemType.PERMISSION or product_area == ProductArea.MEMBER_PERMISSION:
        return Owner.IMPLEMENTATION_SUPPORT
    return Owner.CUSTOMER_SUCCESS


def derive_severity(signals: ImpactSignals) -> Severity:
    if signals.data_loss_claimed:
        return Severity.CRITICAL
    if signals.affected_scope.value == "organization" and signals.workflow_blocked:
        return Severity.CRITICAL
    if signals.workflow_blocked and signals.affected_scope.value in {"team", "organization"}:
        return Severity.HIGH
    if signals.repeat_contacts >= 2:
        return Severity.HIGH
    if signals.workflow_blocked:
        return Severity.MEDIUM
    return Severity.LOW


def needs_escalation(severity: Severity, signals: ImpactSignals) -> bool:
    return severity in {Severity.HIGH, Severity.CRITICAL} or signals.repeat_contacts >= 2

