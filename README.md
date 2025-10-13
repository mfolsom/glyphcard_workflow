# Glyphcard Workflow System

An agent-friendly project management system that breaks work into atomic cards and guides AI agents through a structured four-step development workflow.

## Why Glyphcard?

Coding agents often fail in the same ways poorly managed engineering teams do: they lose context, forget project state, and produce shallow output when micromanaged or left without structure.

After decades managing engineering teams at eBay, Amazon, and Airbus, I realized AI agents need the same scaffolding that makes human teams thrive: clear tasks, feedback loops, and space to reason through problems.

**📖 Read the full story**: [Coding agents are faltering because you're mis-managing them](https://medium.com/@mfolsom/coding-agents-are-faltering-because-youre-mis-managing-them-7dd1693323bb)

---

## Quick Start

### For AI Agents (via MCP)

The recommended way to use Glyphcard is through the MCP server:

Setup guides:
- Claude Code: [integration/claude_code_setup.md](integration/claude_code_setup.md)
- VSCode: [integration/vscode_setup.md](integration/vscode_setup.md)
- Local MCP troubleshooting: [usage_guides/local_mcp_troubleshooting.md](usage_guides/local_mcp_troubleshooting.md)

Then use MCP tools in your AI agent:
- `start_work()` - Pick up and orient on next available card
- `get_card_context(card_id)` - Get detailed card information
- `submit_card(card_id)` - Submit completed work for review
- `list_my_work()` - See available and blocked cards

See [mcp_server_docs/api.md](../mcp_server_docs/api.md) for complete tool reference.

### For Humans (Manual Workflow)

```bash
# View review queue
python show_review_queue.py

# Start web dashboard
./start_dashboard.sh

# Create new card (interactive)
python new_card.py

# Review a card
python review_card.py
```

## Core Tools

### Orientation & Submission (Usually via MCP)
- **reorienter.py** - Generate orientation packet for a card
- **submit_output.py** - Submit completed work for review

### Human Workflows
- **new_card.py** - Interactive card creation for humans
- **review_card.py** - Accept or request changes on submitted cards
- **show_review_queue.py** - View all cards pending review

### Project Management
- **project_manager.py** - Activate/deactivate projects, manage namespaces
- **pm_dashboard.py** - Web UI for card visualization and review

### Card Creation
- **create_card_ai.py** - Programmatic card creation (used by MCP tools)

### Archive Management
- **archive_manager.py** - Archive completed cards and maintain history

## The Four-Step Workflow

Every card follows this mandatory process:

### 1. REORIENT
```bash
python orientation/reorienter.py --card 001
```
Creates `orientation_packet_001.yaml` with:
- Card requirements and deliverables
- Dependency context
- Review notes (if resubmitting)
- Project context

### 2. WORK
Work in your project workspace:
```
agent_workspaces/{agent_name}/{project_name}/
```
Each card builds incrementally on previous work in the same shared workspace.

### 3. DOCUMENT
Create comprehensive documentation:
```
agent_workspaces/{agent_name}/output_{card_id}.md
```

Required sections:
- Summary of what was completed
- Deliverables checklist (✅/❌)
- Validation against card criteria
- Files created/modified with paths
- Handoff notes or next steps

### 4. SUBMIT
```bash
python orientation/submit_output.py --card 001 --module project_setup
```
Updates card status to `awaiting_acceptance` and adds to review queue.

## Project Activation System

Glyphcard supports two operational modes:

**Conversation Mode (Default)**
- No active project
- Brainstorming and exploration
- Glyphcard workflow tools inactive

**Project Mode (Activated)**
```bash
python project_manager.py activate my_project
```
- All implementation uses glyphcard workflow
- Namespace filtering active
- Context persists across sessions

## Card Structure

Cards are YAML files in `glyphcards/`:

```yaml
id: 3
title: "Implement User Authentication"
project: "my_app"
assigned_to: "claude"
status: "available"
size: "2-4 hours"
deliverables:
  - "OAuth integration"
  - "Session management"
validation:
  - "Users can sign in/out"
  - "Sessions persist correctly"
context_needs:
  - "Framework selection from card 002"
linked_to: 2  # Blocks until card 2 is accepted
open_questions: []
```

## Dependency Management

Cards use explicit dependency tracking via `linked_to` field:

- Cards start `blocked` if dependencies aren't accepted
- When dependency accepted → card becomes `available`
- If dependency regresses → downstream cards re-blocked
- Only human acceptance unblocks (not just completion)

```bash
# Check dependencies
from dependency_manager import compute_dependency_state
```

## Human Review Gates

Cards cannot proceed without human acceptance:

```bash
# Review via dashboard
./start_dashboard.sh

# Or via CLI
python review_card.py
```

Review decisions logged in `acceptance.yaml`:
- `accepted` - Work approved, downstream cards unblocked
- `needs_revision` - Work requires changes, resubmit
- `pending_reviews` - Awaiting human review

## File Organization

```
glyphcards/              # Card definitions (YAML)
orientation/             # Orientation packets and scripts
  ├── orientation_packet_{id}.yaml
  ├── reorienter.py
  ├── submit_output.py
  └── system_state.json

agent_workspaces/        # Agent work directories
  ├── claude/
  │   ├── output_001.md
  │   └── {project_name}/  # Shared project workspace

.glyphcard/              # Project state and config
  └── project_state.json

acceptance.yaml          # Review decisions log
archive/                 # Completed cards
```

## MCP Server

The MCP server (`mcp_server.py`) provides 15 automated workflow tools for AI agents.

**Setup:**
- [Integration Guides](integration/) - Setup for Claude Code, VSCode, and more
- [Tools Reference](mcp_server_docs/tools_reference.md) - Complete documentation of all 15 tools

**Quick Overview:**
- **Core Workflow:** `start_work()`, `get_card_context()`, `submit_card()`, `list_my_work()`
- **Project Management:** `list_projects()`, `activate_project()`, `create_project()`
- **Card Management:** `create_card()`, `check_dependencies()`
- **Archive:** `archive_card()`, `list_archived_cards()`
- **System:** `health_check()`

See the [Tools Reference](mcp_server_docs/tools_reference.md) for detailed documentation with examples.

## Agent Output Requirements

Each agent saves work under `agent_workspaces/{agent_name}/`:

- **Output documentation**: `output_{card_id}.md`
- **Project code**: `{project_name}/` (shared workspace)

The system is agent-agnostic - use any name (claude, gpt, custom).

## State Management

All state is explicit and snapshot-friendly:

- **Card state**: YAML files in `glyphcards/`
- **Orientation state**: `orientation/system_state.json`
- **Review state**: `acceptance.yaml`
- **Project state**: `.glyphcard/project_state.json`

Any agent can join at any time and see current context.

## License

MIT License - Copyright (c) 2025 Megan Folsom

See [LICENSE](../LICENSE) for details.
