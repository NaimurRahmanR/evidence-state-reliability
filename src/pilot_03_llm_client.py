from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, NoReturn
from uuid import uuid4

from src.pilot_03_dry_run import (
    DRY_RUN_MODEL_NAME,
    make_dry_run_audit_response,
    make_dry_run_decision_response,
    make_dry_run_escalation_response,
)
from src.pilot_03_prompts import Pilot03PromptRecord
from src.pilot_03_tasks import Pilot03Task


DRY_RUN_CLIENT_MODE = "dry_run"
REAL_CLIENT_MODE = "real_llm"

DRY_RUN_PROVIDER = "local"
REAL_PROVIDER_PLACEHOLDER = "not_configured"


@dataclass(frozen=True)
class Pilot03LLMCallRecord:
    """One logged Pilot 03 model call record.

    In dry-run mode, this records a local deterministic response.
    In real-LLM mode later, this same structure will record the real raw response.
    """

    call_id: str
    task_id: str
    task_type: str
    stage: str
    client_mode: str
    provider: str
    model_name: str
    dry_run: bool
    prompt_version: str
    prompt_text: str
    raw_response_text: str
    parsed_response: dict[str, Any]
    error: str | None
    metadata: dict[str, Any]
    created_at_utc: str


class Pilot03BaseLLMClient:
    """Small interface for Pilot 03 model clients."""

    client_mode: str
    provider: str
    model_name: str
    dry_run: bool

    def run_decision(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        raise NotImplementedError

    def run_audit(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        decision_response_text: str,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        raise NotImplementedError

    def run_escalation(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        decision_response_text: str,
        audit_response_text: str,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        raise NotImplementedError


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _make_call_record(
    *,
    task: Pilot03Task,
    prompt_record: Pilot03PromptRecord,
    stage: str,
    client_mode: str,
    provider: str,
    model_name: str,
    dry_run: bool,
    raw_response_text: str,
    parsed_response: dict[str, Any],
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Pilot03LLMCallRecord:
    """Create one consistent call record for dry-run and future real-LLM calls."""
    return Pilot03LLMCallRecord(
        call_id=f"P03-CALL-{uuid4().hex[:12]}",
        task_id=task.task_id,
        task_type=task.task_type,
        stage=stage,
        client_mode=client_mode,
        provider=provider,
        model_name=model_name,
        dry_run=dry_run,
        prompt_version=prompt_record.prompt_version,
        prompt_text=prompt_record.prompt_text,
        raw_response_text=raw_response_text,
        parsed_response=parsed_response,
        error=error,
        metadata={} if metadata is None else metadata,
        created_at_utc=_now_utc(),
    )


class Pilot03DryRunLLMClient(Pilot03BaseLLMClient):
    """Local deterministic client for Pilot 03 dry-run experiments.

    This client intentionally does not call a real LLM.
    """

    client_mode = DRY_RUN_CLIENT_MODE
    provider = DRY_RUN_PROVIDER
    model_name = DRY_RUN_MODEL_NAME
    dry_run = True

    def run_decision(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        output = make_dry_run_decision_response(
            task=task,
            visible_evidence_unit_ids=visible_evidence_unit_ids,
        )
        return _make_call_record(
            task=task,
            prompt_record=prompt_record,
            stage=output.stage,
            client_mode=self.client_mode,
            provider=self.provider,
            model_name=self.model_name,
            dry_run=self.dry_run,
            raw_response_text=output.response_text,
            parsed_response=output.parsed_response,
            metadata={
                "source": "local_deterministic_dry_run",
                "visible_evidence_unit_ids": visible_evidence_unit_ids,
            },
        )

    def run_audit(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        decision_response_text: str,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        output = make_dry_run_audit_response(
            task=task,
            decision_json=decision_response_text,
            visible_evidence_unit_ids=visible_evidence_unit_ids,
        )
        return _make_call_record(
            task=task,
            prompt_record=prompt_record,
            stage=output.stage,
            client_mode=self.client_mode,
            provider=self.provider,
            model_name=self.model_name,
            dry_run=self.dry_run,
            raw_response_text=output.response_text,
            parsed_response=output.parsed_response,
            metadata={
                "source": "local_deterministic_dry_run",
                "visible_evidence_unit_ids": visible_evidence_unit_ids,
            },
        )

    def run_escalation(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        decision_response_text: str,
        audit_response_text: str,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        output = make_dry_run_escalation_response(
            task=task,
            decision_json=decision_response_text,
            audit_json=audit_response_text,
            visible_evidence_unit_ids=visible_evidence_unit_ids,
        )
        return _make_call_record(
            task=task,
            prompt_record=prompt_record,
            stage=output.stage,
            client_mode=self.client_mode,
            provider=self.provider,
            model_name=self.model_name,
            dry_run=self.dry_run,
            raw_response_text=output.response_text,
            parsed_response=output.parsed_response,
            metadata={
                "source": "local_deterministic_dry_run",
                "visible_evidence_unit_ids": visible_evidence_unit_ids,
            },
        )


class Pilot03RealLLMClient(Pilot03BaseLLMClient):
    """Placeholder for future real LLM calls.

    This is deliberately locked for now. Pilot 03 must first prove that the
    dry-run pipeline, logging, parsing, and analysis work correctly.
    """

    client_mode = REAL_CLIENT_MODE
    provider = REAL_PROVIDER_PLACEHOLDER
    model_name = "not_configured"
    dry_run = False

    def _raise_not_enabled(self) -> NoReturn:
        raise RuntimeError(
            "Real LLM calls are not enabled yet. "
            "Use get_pilot_03_client(mode='dry_run') until the real LLM runner is explicitly implemented."
        )

    def run_decision(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        self._raise_not_enabled()

    def run_audit(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        decision_response_text: str,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        self._raise_not_enabled()

    def run_escalation(
        self,
        task: Pilot03Task,
        prompt_record: Pilot03PromptRecord,
        decision_response_text: str,
        audit_response_text: str,
        visible_evidence_unit_ids: list[str] | None = None,
    ) -> Pilot03LLMCallRecord:
        self._raise_not_enabled()


def get_pilot_03_client(mode: str = DRY_RUN_CLIENT_MODE) -> Pilot03BaseLLMClient:
    """Return the requested Pilot 03 client.

    For now, dry_run is the only usable mode. real_llm exists only as a guarded
    placeholder so we do not accidentally call an external API.
    """
    normalised_mode = mode.strip().lower()

    if normalised_mode == DRY_RUN_CLIENT_MODE:
        return Pilot03DryRunLLMClient()

    if normalised_mode == REAL_CLIENT_MODE:
        return Pilot03RealLLMClient()

    raise ValueError(f"Unknown Pilot 03 client mode: {mode}")


def llm_call_record_to_dict(record: Pilot03LLMCallRecord) -> dict[str, Any]:
    """Convert one LLM call record into a dictionary."""
    return asdict(record)


def llm_call_records_to_dicts(records: list[Pilot03LLMCallRecord]) -> list[dict[str, Any]]:
    """Convert LLM call records into dictionaries."""
    return [llm_call_record_to_dict(record) for record in records]


def summarise_llm_call_records(records: list[Pilot03LLMCallRecord]) -> dict[str, Any]:
    """Return a compact summary of Pilot 03 call records."""
    stage_counts = Counter(record.stage for record in records)
    mode_counts = Counter(record.client_mode for record in records)
    provider_counts = Counter(record.provider for record in records)
    dry_run_counts = Counter(str(record.dry_run) for record in records)
    error_count = sum(1 for record in records if record.error)

    final_decisions = Counter(
        record.parsed_response.get("final_decision")
        for record in records
        if "final_decision" in record.parsed_response
    )

    audit_passed = Counter(
        str(record.parsed_response.get("audit_passed"))
        for record in records
        if "audit_passed" in record.parsed_response
    )

    return {
        "n_call_records": len(records),
        "stage_counts": dict(stage_counts),
        "mode_counts": dict(mode_counts),
        "provider_counts": dict(provider_counts),
        "dry_run_counts": dict(dry_run_counts),
        "error_count": error_count,
        "final_decisions": dict(final_decisions),
        "audit_passed": dict(audit_passed),
    }


if __name__ == "__main__":
    from src.pilot_03_prompts import (
        build_audit_prompt_record,
        build_decision_prompt_record,
        build_escalation_prompt_record,
    )
    from src.pilot_03_tasks import generate_pilot_03_tasks

    task = generate_pilot_03_tasks(n_tasks=1)[0]
    client = get_pilot_03_client(mode=DRY_RUN_CLIENT_MODE)

    decision_prompt = build_decision_prompt_record(task)
    decision_call = client.run_decision(task, decision_prompt)

    audit_prompt = build_audit_prompt_record(
        task=task,
        decision_json=decision_call.raw_response_text,
    )
    audit_call = client.run_audit(
        task=task,
        prompt_record=audit_prompt,
        decision_response_text=decision_call.raw_response_text,
    )

    escalation_prompt = build_escalation_prompt_record(
        task=task,
        decision_json=decision_call.raw_response_text,
        audit_json=audit_call.raw_response_text,
    )
    escalation_call = client.run_escalation(
        task=task,
        prompt_record=escalation_prompt,
        decision_response_text=decision_call.raw_response_text,
        audit_response_text=audit_call.raw_response_text,
    )

    calls = [decision_call, audit_call, escalation_call]
    print(summarise_llm_call_records(calls))
    for call in calls:
        print(call.stage, call.client_mode, call.raw_response_text)