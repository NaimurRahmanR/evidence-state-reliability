"""
Evidence-state data structures for the Evidence-State Reliability project.

This file defines the basic objects used to represent:
1. A required evidence unit
2. The evidence available at a pipeline stage
"""

from dataclasses import dataclass, field


@dataclass
class EvidenceUnit:
    """
    A single required piece of task-relevant evidence.

    Example:
        unit_id: "F001"
        text: "The patient has a fever."
        importance: 1.0
    """

    unit_id: str
    text: str
    importance: float = 1.0


@dataclass
class EvidenceState:
    """
    The evidence available to one stage of a multi-stage LLM pipeline.

    Example stages:
        original
        retrieved
        summary
        decision
        audit
        escalation
    """

    task_id: str
    stage_name: str
    evidence_text: str
    preserved_units: set[str] = field(default_factory=set)
    lost_units: set[str] = field(default_factory=set)
    mutated_units: set[str] = field(default_factory=set)
    contradicted_units: set[str] = field(default_factory=set)
    unsupported_additions: list[str] = field(default_factory=list)
    uncertainty_removed: bool = False

    def reliability_score(self, required_units: list[EvidenceUnit]) -> float:
        """
        Compute a simple evidence-state reliability score.

        Current pilot definition:
            preserved required units / total required units

        This is an initial operational metric, not a validated final theory.
        """

        if not required_units:
            return 0.0

        required_ids = {unit.unit_id for unit in required_units}
        preserved_required = self.preserved_units.intersection(required_ids)

        return len(preserved_required) / len(required_ids)

    def degradation_count(self) -> int:
        """
        Count visible evidence-state degradation events.

        This is a simple pilot metric.
        Later we may weight different degradation types differently.
        """

        count = 0
        count += len(self.lost_units)
        count += len(self.mutated_units)
        count += len(self.contradicted_units)
        count += len(self.unsupported_additions)

        if self.uncertainty_removed:
            count += 1

        return count