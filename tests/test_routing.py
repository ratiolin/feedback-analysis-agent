from feedback_app.routing import derive_severity, needs_escalation, route_owner
from feedback_app.schemas import (
    AffectedScope,
    ImpactSignals,
    Owner,
    ProblemType,
    ProductArea,
    Severity,
)


def test_owner_is_deterministic_not_model_controlled() -> None:
    assert route_owner(ProblemType.INTEGRATION, ProductArea.OPEN_API) == Owner.TECHNICAL_SUPPORT
    assert route_owner(ProblemType.DATA_CONSISTENCY, ProductArea.IMPORT_EXPORT) == Owner.QA_TRIAGE
    assert route_owner(ProblemType.FEATURE_REQUEST, ProductArea.TASK) == Owner.PRODUCT_OPS


def test_organization_wide_block_is_critical_and_escalated() -> None:
    signals = ImpactSignals(
        affected_scope=AffectedScope.ORGANIZATION,
        workflow_blocked=True,
        repeat_contacts=0,
    )
    severity = derive_severity(signals)
    assert severity == Severity.CRITICAL
    assert needs_escalation(severity, signals)


def test_sentiment_is_not_part_of_severity_contract() -> None:
    signals = ImpactSignals(affected_scope=AffectedScope.INDIVIDUAL, workflow_blocked=False)
    assert derive_severity(signals) == Severity.LOW
