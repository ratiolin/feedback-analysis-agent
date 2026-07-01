import csv
import hashlib
import json

import pytest

from tools.evaluate import load_and_verify_manifest, load_audit_status


def test_candidate_manifest_rejects_prompt_changed_after_freeze(tmp_path) -> None:
    prompt = tmp_path / "candidate.yml"
    prompt.write_text("version: one\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "candidate_prompt_path": str(prompt),
                "candidate_prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    assert load_and_verify_manifest(manifest)["candidate_prompt_path"] == str(prompt)
    prompt.write_text("version: two\n", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after holdout freeze"):
        load_and_verify_manifest(manifest)


def test_audit_must_match_holdout_and_be_complete(tmp_path) -> None:
    audit = tmp_path / "audit.csv"
    with audit.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["ticket_id", "message", "audit_label_text_consistent", "auditor"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "ticket_id": "T1",
                "message": "message",
                "audit_label_text_consistent": "yes",
                "auditor": "AI-assisted",
            }
        )
    status = load_audit_status(audit, [{"ticket_id": "T1", "message": "message"}])
    assert status["consistent"] == 1
    with pytest.raises(ValueError, match="do not match"):
        load_audit_status(audit, [{"ticket_id": "T2", "message": "message"}])
