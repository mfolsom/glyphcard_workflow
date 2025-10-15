import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import yaml

try:  # pragma: no cover - import shim to satisfy test environment
    import fastmcp  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - exercised in CI without fastmcp
    class DummyFastMCP:
        def __init__(self, *args, **kwargs):
            pass

        def tool(self, func):
            return func

    dummy_fastmcp = ModuleType("fastmcp")
    dummy_fastmcp.FastMCP = DummyFastMCP
    sys.modules["fastmcp"] = dummy_fastmcp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mcp_server


def call_tool(tool, *args, **kwargs):
    """Invoke an MCP tool regardless of FastMCP wrapping."""
    target = getattr(tool, "fn", tool)
    return target(*args, **kwargs)


def test_get_orientation_context_internal_missing_packet(monkeypatch, tmp_path):
    """Missing orientation packet should return an explicit error."""
    monkeypatch.setattr(mcp_server.workflow, "orientation_dir", tmp_path)

    result = mcp_server._get_orientation_context_internal("999")

    assert "error" in result
    assert "not found" in result["error"]


def test_get_orientation_context_internal_with_packet(monkeypatch, tmp_path):
    """Orientation packets are parsed with truncated review notes."""
    orientation_dir = tmp_path / "orientation"
    orientation_dir.mkdir()
    packet_path = orientation_dir / "orientation_packet_027.yaml"
    long_notes = "note" * 200  # 800 characters to trigger truncation
    packet_data = {
        "card_id": "027",
        "title": "Test Card",
        "deliverables": ["Demo deliverable"],
        "validation": ["Run pytest"],
        "context_brief": {"context_needs": ["Need context"]},
        "open_questions": [],
        "review_notes": [{"notes": long_notes}],
    }
    packet_path.write_text(yaml.dump(packet_data))
    monkeypatch.setattr(mcp_server.workflow, "orientation_dir", orientation_dir)

    result = mcp_server._get_orientation_context_internal("027")

    assert result["card_id"] == "027"
    assert result["title"] == "Test Card"
    assert result["has_review_notes"] is True
    assert result["review_notes_summary"].endswith("...")
    assert len(result["review_notes_summary"]) <= 503


def test_discover_available_work_filters_by_project_and_dependencies(monkeypatch):
    """Only unblocked cards in the active project should be marked available."""
    state = {
        27: {"blocked": False, "parents": [], "missing_parents": [], "pending_parents": []},
        28: {"blocked": True, "parents": ["026"], "missing_parents": [], "pending_parents": ["026"]},
        30: {"blocked": False, "parents": [], "missing_parents": [], "pending_parents": []},
    }
    entries = [
        {
            "id": 27,
            "id_str": "027",
            "data": {
                "id": 27,
                "title": "Ready Card",
                "status": "available",
                "assigned_to": "claude",
                "project": "workspace_management",
                "size": "2-4 hours",
                "review_notes": [],
            },
        },
        {
            "id": 28,
            "id_str": "028",
            "data": {
                "id": 28,
                "title": "Blocked Card",
                "status": "available",
                "assigned_to": "claude",
                "project": "workspace_management",
                "size": "2-4 hours",
                "review_notes": [],
            },
        },
        {
            "id": 30,
            "id_str": "030",
            "data": {
                "id": 30,
                "title": "Other Agent Card",
                "status": "available",
                "assigned_to": "someone_else",
                "project": "workspace_management",
                "size": "2-4 hours",
                "review_notes": [],
            },
        },
        {
            "id": 31,
            "id_str": "031",
            "data": {
                "id": 31,
                "title": "Other Project Card",
                "status": "available",
                "assigned_to": "claude",
                "project": "another_project",
                "size": "2-4 hours",
                "review_notes": [],
            },
        },
    ]

    monkeypatch.setattr(mcp_server, "compute_dependency_state", lambda: (state, entries))
    monkeypatch.setattr(mcp_server.workflow.project_manager, "get_active_project", lambda: "workspace_management")

    result = mcp_server._discover_available_work_internal()

    assert result["available_cards"] == [
        {"id": 27, "title": "Ready Card", "status": "available", "size": "2-4 hours", "project": "workspace_management", "has_review_notes": False}
    ]
    assert result["blocked_cards"] == [
        {"id": 28, "title": "Blocked Card", "status": "available", "size": "2-4 hours", "project": "workspace_management", "has_review_notes": False}
    ]
    assert result["count"] == 1
    assert result["blocked_count"] == 1


def test_start_work_returns_waiting_when_only_blocked(monkeypatch):
    """When no cards are available, the tool should indicate a waiting state."""
    monkeypatch.setattr(
        mcp_server,
        "_discover_available_work_internal",
        lambda: {
            "available_cards": [],
            "blocked_cards": [{"id": 99, "title": "Blocked"}],
            "count": 0,
            "blocked_count": 1,
        },
    )

    result = call_tool(mcp_server.start_work)

    assert result["action"] == "waiting"
    assert "No work available" in result["message"]
    assert result["blocked_cards"] == [{"id": 99, "title": "Blocked"}]


def test_start_work_runs_reorienter_on_available_card(monkeypatch):
    """Available cards should trigger the reorienter script with the padded ID."""
    monkeypatch.setattr(
        mcp_server,
        "_discover_available_work_internal",
        lambda: {
            "available_cards": [{"id": 27, "title": "Card Title", "status": "available", "size": "2-4 hours", "project": "workspace_management", "has_review_notes": False}],
            "blocked_cards": [],
            "count": 1,
            "blocked_count": 0,
        },
    )
    monkeypatch.setattr(
        mcp_server,
        "_summarize_dependencies",
        lambda card_id: {"card_id": card_id, "dependencies_met": True, "dependencies": [], "blocking": [], "blocking_count": 0},
    )
    monkeypatch.setattr(
        mcp_server,
        "_collect_card_progress",
        lambda card_id, run_tests=False, test_command=None: {"progress": {"reoriented": True}, "next_actions": [], "dependencies": {}},
    )
    captured = {}

    def fake_run(cmd, capture_output, text, cwd):
        if cmd[0] == "git" and cmd[1] == "status":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["capture_output"] = capture_output
        captured["text"] = text
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(mcp_server.subprocess, "run", fake_run)

    result = call_tool(mcp_server.start_work)

    assert result["action"] == "started"
    assert result["card_id"] == "27"
    assert captured["cmd"][0] == sys.executable
    assert captured["cmd"][1] == str(mcp_server.workflow.orientation_dir / "reorienter.py")
    assert captured["cmd"][3] == "027"
    assert captured["capture_output"] is True
    assert captured["text"] is True
    assert captured["cwd"] == str(mcp_server.workflow.base_dir)
    assert "dependency_summary" in result


def test_check_dependencies_reports_pending_and_modules(monkeypatch, tmp_path):
    """Dependency checks surface linked cards, pending status, and module progress."""
    orientation_dir = tmp_path / "orientation"
    orientation_dir.mkdir()
    packet_path = orientation_dir / "orientation_packet_27.yaml"
    packet_data = {
        "card_id": "027",
        "title": "Card with Modules",
        "deliverables": [],
        "validation": [],
        "context_brief": {
            "linked_modules": {
                "sync_module": {"status": "in_progress", "linked_cards": ["040"]},
                "docs_module": {"status": "completed", "linked_cards": []},
            },
        },
        "open_questions": [],
        "review_notes": [],
    }
    packet_path.write_text(yaml.dump(packet_data))
    monkeypatch.setattr(mcp_server.workflow, "orientation_dir", orientation_dir)

    state = {
        27: {
            "blocked": True,
            "parents": ["026"],
            "missing_parents": [],
            "pending_parents": ["026"],
        },
        26: {
            "blocked": False,
            "parents": [],
            "missing_parents": [],
            "pending_parents": [],
        },
    }
    entries = [
        {
            "id": 27,
            "id_str": "027",
            "data": {"id": 27, "title": "Card with Modules", "status": "in_progress"},
        },
        {
            "id": 26,
            "id_str": "026",
            "data": {"id": 26, "title": "Parent Card", "status": "submitted"},
        },
    ]

    monkeypatch.setattr(mcp_server, "compute_dependency_state", lambda: (state, entries))

    result = call_tool(mcp_server.check_dependencies, "27")

    assert result["card_id"] == "27"
    assert result["dependencies_met"] is False
    dependency_types = {dep["type"] for dep in result["dependencies"]}
    assert dependency_types == {"linked_card", "module"}
    linked_card = next(dep for dep in result["dependencies"] if dep["type"] == "linked_card")
    assert linked_card["card_id"] == "026"
    assert linked_card["met"] is False
    module_entries = [dep for dep in result["dependencies"] if dep["type"] == "module"]
    assert {mod["module_name"] for mod in module_entries} == {"sync_module", "docs_module"}
    sync_module = next(mod for mod in module_entries if mod["module_name"] == "sync_module")
    assert sync_module["met"] is False
    assert result["blocking"] == []
    assert result["blocking_count"] == 0


def test_get_card_progress_reports_status(monkeypatch, tmp_path):
    """Progress checklist highlights orientation, docs, workspace, tests, and dependencies."""
    orientation_dir = tmp_path / "orientation"
    orientation_dir.mkdir()
    orientation_file = orientation_dir / "orientation_packet_025.yaml"
    orientation_file.write_text("summary: ok")

    workspace_dir = tmp_path / "agent_workspaces" / "claude" / "workspace_management"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    doc_path = tmp_path / "agent_workspaces" / "claude" / "output_025.md"
    doc_path.write_text("Documenting work.\n" * 50)  # >200 chars

    glyphcards_dir = tmp_path / "glyphcards"
    glyphcards_dir.mkdir()
    card_file = glyphcards_dir / "025_progress.yaml"
    card_data = {
        "id": 25,
        "title": "Progress Checklist",
        "project": "workspace_management",
        "status": "in_progress",
        "linked_to": None,
    }
    card_file.write_text(yaml.dump(card_data))

    monkeypatch.setattr(mcp_server.workflow, "base_dir", tmp_path)
    monkeypatch.setattr(mcp_server.workflow, "orientation_dir", orientation_dir)
    monkeypatch.setattr(mcp_server.workflow, "glyphcards_dir", glyphcards_dir)
    monkeypatch.setattr(
        mcp_server,
        "_summarize_dependencies",
        lambda cid: {
            "card_id": cid,
            "dependencies_met": True,
            "dependencies": [
                {"type": "module", "module_name": "demo", "status": "archived", "linked_cards": [], "met": True, "explanation": "Module status: archived"}
            ],
            "blocking": [],
            "blocking_count": 0,
        },
    )
    monkeypatch.setattr(mcp_server, "_collect_git_status", lambda prefix: [{"status": "M", "path": f"{prefix}/file.txt"}])

    result = call_tool(mcp_server.get_card_progress, "25")

    assert result["orientation"]["present"] is True
    assert result["documentation"]["present"] is True
    assert result["documentation"]["length"] > 200
    assert result["workspace"]["exists"] is True
    assert result["workspace"]["tracked_changes"] == [{"status": "M", "path": "agent_workspaces/claude/workspace_management/file.txt"}]
    assert result["tests"]["status"] == "not_run"
    assert result["dependencies"]["dependencies_met"] is True
    assert result["dependencies"]["dependencies"][0]["met"] is True
    assert result["progress"]["documentation_ready"] is True
    assert result["ready_to_submit"] is True
    assert "Run pytest" in " ".join(result["next_actions"])
