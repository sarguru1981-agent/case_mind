"""Tests for agentic_ai.decomposer — deterministic and LLM-injectable paths."""
import pytest

from services.agentic_ai.decomposer import decompose
from services.agentic_ai.models import Priority, TaskStatus, TaskType


BROAD_MISSION = (
    "Investigate the Operation Nightfall robbery series, determine whether the"
    " four incidents are connected, identify the strongest persons of interest,"
    " evaluate significant alternative leads, and produce an evidence-backed"
    " investigation assessment for human review."
)


# ---------------------------------------------------------------------------
# Deterministic fallback (no llm_fn)
# ---------------------------------------------------------------------------

class TestDeterministicDecompose:
    def test_returns_at_least_two_tasks(self):
        tasks = decompose(BROAD_MISSION)
        assert len(tasks) >= 2

    def test_t001_is_archive_investigation(self):
        tasks = decompose(BROAD_MISSION)
        t001  = next(t for t in tasks if t.task_id == "T-001")
        assert t001.task_type           == TaskType.ARCHIVE_INVESTIGATION
        assert t001.priority            == Priority.CRITICAL
        assert t001.status              == TaskStatus.READY
        assert t001.assigned_capability == "agentic_rag"
        assert t001.dependencies        == []

    def test_t002_is_synthesis_blocked(self):
        tasks = decompose(BROAD_MISSION)
        t002  = next(t for t in tasks if t.task_id == "T-002")
        assert t002.task_type           == TaskType.SYNTHESIS
        assert t002.status              == TaskStatus.BLOCKED
        assert t002.assigned_capability == "synthesis"
        assert "T-001" in t002.dependencies

    def test_all_tasks_have_created_from(self):
        tasks = decompose(BROAD_MISSION)
        for task in tasks:
            assert task.created_from == "mission_decomposition"

    def test_all_tasks_have_priority_history(self):
        tasks = decompose(BROAD_MISSION)
        for task in tasks:
            assert len(task.priority_history) >= 1

    def test_no_forward_knowledge_injected(self):
        tasks = decompose(BROAD_MISSION)
        forbidden = ["MBK-4172", "Marcus Vale", "NF-3847", "Daniel Mercer"]
        for task in tasks:
            for word in forbidden:
                assert word not in task.objective, (
                    f"Forward knowledge '{word}' found in {task.task_id} objective"
                )

    def test_decompose_never_creates_external_tasks(self):
        # External tasks are created by the orchestrator (Rule 0) after T-001
        # completes — the decomposer must never pre-create them regardless of
        # what keywords appear in the mission text.
        for mission in (
            "Investigate using external surveillance records.",
            "Investigate external records, vehicles, financial data.",
            BROAD_MISSION,
        ):
            tasks = decompose(mission)
            types = {t.task_type for t in tasks}
            assert TaskType.EXTERNAL_INVESTIGATION not in types, (
                f"Decomposer should not create EXTERNAL_INVESTIGATION tasks: {tasks}"
            )

    def test_all_missions_return_exactly_archive_and_synthesis(self):
        for mission in ("Review the archive.", "Minimal.", BROAD_MISSION):
            tasks = decompose(mission)
            assert len(tasks) == 2
            ids   = {t.task_id for t in tasks}
            assert ids == {"T-001", "T-002"}

    def test_t002_blocked_only_on_t001_initially(self):
        tasks = decompose(BROAD_MISSION)
        t002  = next(t for t in tasks if t.task_id == "T-002")
        assert t002.dependencies == ["T-001"], (
            f"T-002 should be blocked only on T-001 at decomposition, "
            f"got: {t002.dependencies}"
        )


# ---------------------------------------------------------------------------
# LLM-injectable path
# ---------------------------------------------------------------------------

_STUB_LLM_RESPONSE = """\
T-001 | Archive Investigation | Search the case archive for patterns | ARCHIVE_INVESTIGATION | CRITICAL | agentic_rag | Archive first
T-002 | Synthesis | Synthesise all findings | SYNTHESIS | HIGH | synthesis | Required final step
"""

_BAD_LLM_RESPONSE = "this is not a valid task line"


class TestLLMDecompose:
    def test_llm_fn_called_when_provided(self):
        calls = []

        def stub_llm(prompt: str) -> str:
            calls.append(prompt)
            return _STUB_LLM_RESPONSE

        decompose(BROAD_MISSION, llm_fn=stub_llm)
        assert len(calls) == 1

    def test_llm_prompt_contains_mission(self):
        captured = []

        def stub_llm(prompt: str) -> str:
            captured.append(prompt)
            return _STUB_LLM_RESPONSE

        decompose(BROAD_MISSION, llm_fn=stub_llm)
        assert BROAD_MISSION in captured[0]

    def test_llm_parse_produces_tasks(self):
        tasks = decompose(BROAD_MISSION, llm_fn=lambda _: _STUB_LLM_RESPONSE)
        assert len(tasks) >= 2
        ids = {t.task_id for t in tasks}
        assert "T-001" in ids
        assert "T-002" in ids

    def test_fallback_on_bad_llm_response(self):
        tasks = decompose(BROAD_MISSION, llm_fn=lambda _: _BAD_LLM_RESPONSE)
        # Deterministic fallback always includes T-001 and T-002
        ids = {t.task_id for t in tasks}
        assert "T-001" in ids
        assert "T-002" in ids

    def test_fallback_on_llm_exception(self):
        def failing_llm(prompt: str) -> str:
            raise RuntimeError("LLM unavailable")

        tasks = decompose(BROAD_MISSION, llm_fn=failing_llm)
        ids = {t.task_id for t in tasks}
        assert "T-001" in ids
        assert "T-002" in ids

    def test_llm_tasks_have_required_fields(self):
        tasks = decompose(BROAD_MISSION, llm_fn=lambda _: _STUB_LLM_RESPONSE)
        for task in tasks:
            assert task.task_id
            assert task.title
            assert task.objective
            assert task.assigned_capability in ("agentic_rag", "ai_agent", "synthesis")

    def test_duplicate_task_ids_deduplicated(self):
        duplicate_response = _STUB_LLM_RESPONSE + _STUB_LLM_RESPONSE
        tasks = decompose(BROAD_MISSION, llm_fn=lambda _: duplicate_response)
        ids   = [t.task_id for t in tasks]
        assert len(ids) == len(set(ids)), "Duplicate task IDs found"
