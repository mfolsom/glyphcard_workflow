# Glyphcard MCP Tools Reference

Complete reference for all MCP tools provided by the Glyphcard workflow automation server.

## Core Workflow Tools

### `start_work()`
**Description:** Automatically discover and start the next available card.

**Returns:**
- `action`: "started", "waiting", "no_work", or "error"
- `card_id`: ID of the card started
- `title`: Card title
- `message`: Human-readable status
- `workflow_reminder`: 4-step workflow guide
- `next_step`: What to do next

**Example:**
```python
start_work()
# Returns: {"action": "started", "card_id": "3", "title": "Fetch Cat Images", ...}
```

**Use when:** Ready to pick up new work automatically.

---

### `get_card_context(card_id: str)`
**Description:** Get everything you need to know about a card in clean, actionable format.

**Parameters:**
- `card_id`: The ID of the card to get context for

**Returns:**
- `card_id`: Card identifier
- `title`: Card title
- `what_to_build`: List of deliverables
- `how_to_validate`: List of validation criteria
- `context_you_need`: List of context needs
- `questions_to_resolve`: Open questions
- `has_feedback`: Boolean - has review notes
- `feedback_summary`: Review notes if any
- `progress`: Progress checklist object
- `next_recommended_action`: What to do next
- `ready_to_code`: Boolean - ready to start

**Example:**
```python
get_card_context(card_id="3")
# Returns detailed context with progress tracking
```

**Use when:** Need to understand what to build and current progress.

---

### `submit_card(card_id: str, module_name: str = None)`
**Description:** Submit completed work with mandatory documentation validation.

**Parameters:**
- `card_id`: The ID of the card to submit
- `module_name`: Optional module name (auto-generated if not provided)

**Returns:**
- `success`: Boolean
- `card_id`: Card identifier
- `module`: Module name used
- `message`: Status message
- `warnings`: List of warnings (if any)
- `next_action`: What happens next

**Validation:**
- ✅ **Blocks** if `output_{card_id}.md` doesn't exist
- ⚠️ **Warns** if documentation < 200 characters
- ⚠️ **Warns** if no section headers found

**Example:**
```python
submit_card(card_id="3")
# Returns: {"success": True, "message": "Card 3 submitted successfully!", ...}
```

**Use when:** Work is complete and documented.

---

### `get_card_progress(card_id: str, run_tests: bool = False, test_command: str = None)`
**Description:** Provide detailed progress checklist for a glyphcard, optionally running tests.

**Parameters:**
- `card_id`: The ID of the card to check progress for
- `run_tests`: Boolean - whether to run tests (default: False)
- `test_command`: Optional test command (default: "pytest")

**Returns:**
- `card_id`: Card identifier
- `title`: Card title
- `project`: Project name
- `orientation`: Orientation packet status
  - `present`: Boolean - orientation exists
  - `path`: Path to orientation packet
  - `last_modified`: ISO timestamp
- `documentation`: Documentation status
  - `present`: Boolean - documentation exists
  - `path`: Path to output file
  - `length`: Documentation length in characters
  - `last_modified`: ISO timestamp
- `workspace`: Workspace status
  - `path`: Workspace directory path
  - `exists`: Boolean - workspace exists
  - `tracked_changes`: List of git-tracked changes
- `tests`: Test status
  - `tests_present`: Boolean - tests exist
  - `status`: "passed", "failed", "not_run", or "error"
  - `command`: Test command used
  - `stdout`: Test output (if run)
  - `stderr`: Test errors (if run)
- `dependencies`: Full dependency analysis
- `progress`: Progress summary
  - `reoriented`: Boolean
  - `documentation_exists`: Boolean
  - `documentation_ready`: Boolean
  - `tests_status`: Test status
  - `dependencies_met`: Boolean
  - `ready_to_submit`: Boolean
- `next_actions`: List of recommended next steps
- `ready_to_submit`: Boolean - overall submission readiness

**Example:**
```python
get_card_progress(card_id="3", run_tests=True)
# Returns comprehensive progress tracking with test results
```

**Use when:** Need detailed progress check or want to validate tests before submission.

---

### `list_my_work()`
**Description:** Show all work assigned to you in easy-to-understand format.

**Returns:**
- `available_now`: List of cards ready to work on
- `blocked`: List of cards blocked by dependencies
- `summary`: Human-readable summary
- `suggestion`: Recommended next action

**Example:**
```python
list_my_work()
# Returns: {"available_now": [...], "blocked": [...], "summary": "2 cards ready, 1 blocked"}
```

**Use when:** Want to see what work is available.

---

## Project Management Tools

### `list_projects()`
**Description:** List all available projects with status information.

**Returns:**
- `active_project`: Currently active project name (or null)
- `projects`: List of project objects
  - `name`: Project name
  - `active`: Boolean - is this the active project
  - `card_count`: Number of cards in project
  - `registered`: Boolean - is project registered
- `total_projects`: Total number of projects

**Example:**
```python
list_projects()
# Returns: {"active_project": "cat_picture_app", "projects": [...], ...}
```

**Use when:** Want to see available projects.

---

### `activate_project(project_name: str)`
**Description:** Activate a specific project for focused work.

**Parameters:**
- `project_name`: Name of the project to activate

**Returns:**
- `success`: Boolean
- `active_project`: Name of activated project
- `previous_project`: Previously active project (if any)
- `message`: Status message
- `card_count`: Number of cards in project

**Example:**
```python
activate_project(project_name="cat_picture_app")
# Returns: {"success": True, "active_project": "cat_picture_app", ...}
```

**Use when:** Switching to work on a specific project.

---

### `deactivate_project()`
**Description:** Deactivate current project and return to conversation mode.

**Returns:**
- `success`: Boolean
- `deactivated_project`: Name of project that was deactivated
- `message`: Status message

**Example:**
```python
deactivate_project()
# Returns: {"success": True, "deactivated_project": "cat_picture_app", ...}
```

**Use when:** Done with project work, want to return to conversation mode.

---

### `get_project_context()`
**Description:** Get complete project context for current session.

**Returns:**
- `mode`: "conversation" or "project"
- `active_project`: Name of active project (or null)
- `card_count`: Number of cards in active project
- `timestamp`: When context was retrieved

**Example:**
```python
get_project_context()
# Returns: {"mode": "project", "active_project": "cat_picture_app", ...}
```

**Use when:** Need to check current project state.

---

### `create_project(project_name: str, description: str = None)`
**Description:** Create a new project with basic workspace setup.

**Parameters:**
- `project_name`: Name of the project (lowercase, underscores only)
- `description`: Optional description for the project

**Returns:**
- `success`: Boolean
- `project_name`: Name of created project
- `workspace_path`: Path to project workspace
- `message`: Status message

**Example:**
```python
create_project(project_name="todo_app", description="A simple todo application")
# Returns: {"success": True, "project_name": "todo_app", ...}
```

**Use when:** Starting a new project.

---

## Card Management Tools

### `create_card(title: str, deliverables: List[str], ...)`
**Description:** Create a new glyphcard with specified details.

**Parameters:**
- `title`: The title/name of the card (required)
- `deliverables`: List of deliverables for this card (required)
- `project`: Project name (defaults to active project)
- `context_needs`: List of context requirements (optional)
- `validation`: List of validation criteria (optional)
- `open_questions`: List of open questions (optional)
- `linked_to`: ID of prerequisite card (optional)
- `assigned_to`: Who card is assigned to (default: "claude")
- `size`: Estimated time to complete (default: "2-4 hours")

**Returns:**
- `success`: Boolean
- `card_id`: ID of created card
- `title`: Card title
- `status`: Initial card status
- `project`: Project name
- `file_path`: Path to card file
- `message`: Status message

**Example:**
```python
create_card(
    title="Add User Authentication",
    deliverables=["Login page", "Auth API", "Tests"],
    validation=["Users can log in", "Tests pass"],
    linked_to=5
)
```

**Use when:** Need to create new work cards.

---

### `check_dependencies(card_id: str)`
**Description:** Verify linked cards and prerequisites are met for a card.

**Parameters:**
- `card_id`: The ID of the card to check

**Returns:**
- `card_id`: Card identifier
- `dependencies_met`: Boolean - all dependencies satisfied
- `dependencies`: List of dependency objects
  - `card_id`: Dependency card ID
  - `title`: Dependency card title
  - `status`: Dependency status
  - `accepted`: Boolean - is dependency accepted
- `workflow_note`: Reminder about acceptance requirements

**Example:**
```python
check_dependencies(card_id="5")
# Returns: {"dependencies_met": False, "dependencies": [...], ...}
```

**Use when:** Want to understand why a card is blocked.

---

## Archive Management Tools

### `archive_card(card_id: str)`
**Description:** Archive an accepted card and its related files.

**Parameters:**
- `card_id`: The ID of the card to archive

**Returns:**
- `success`: Boolean
- `card_id`: Card identifier
- `archived_files`: List of files archived
- `message`: Status message

**Example:**
```python
archive_card(card_id="3")
# Returns: {"success": True, "card_id": "3", ...}
```

**Use when:** Cleaning up completed, accepted cards.

---

### `list_archived_cards()`
**Description:** List all archived cards.

**Returns:**
- `archived_cards`: List of archived card objects
- `total_archived`: Total number of archived cards
- `archive_path`: Path to archive directory

**Example:**
```python
list_archived_cards()
# Returns: {"archived_cards": [...], "total_archived": 5, ...}
```

**Use when:** Want to see archived work history.

---

### `cleanup_acceptance_tracking()`
**Description:** Remove archived cards from acceptance.yaml tracking.

**Returns:**
- `success`: Boolean
- `cleaned_count`: Number of entries cleaned
- `message`: Status message

**Example:**
```python
cleanup_acceptance_tracking()
# Returns: {"success": True, "cleaned_count": 3, ...}
```

**Use when:** Cleaning up acceptance tracking after archiving cards.

---

## System Tools

### `health_check()`
**Description:** Health check endpoint to verify server is running correctly.

**Returns:**
- `status`: "healthy" or error status
- `service`: Service name
- `version`: Server version
- `working_directory`: Current working directory
- `server_name`: Full server name
- `agent`: Current agent name

**Example:**
```python
health_check()
# Returns: {"status": "healthy", "version": "2.0.0", ...}
```

**Use when:** Testing server connectivity or debugging.

---

## Workflow Patterns

### Starting New Work
```python
# 1. See what's available
list_my_work()

# 2. Start next card automatically
start_work()

# 3. Get full context
get_card_context(card_id="3")

# 4. Build deliverables...

# 5. Check progress and run tests
get_card_progress(card_id="3", run_tests=True)

# 6. Submit when done
submit_card(card_id="3")
```

### Working with Projects
```python
# 1. See available projects
list_projects()

# 2. Activate a project
activate_project(project_name="cat_picture_app")

# 3. Work on cards in that project
start_work()

# 4. When done with project
deactivate_project()
```

### Creating New Cards
```python
# 1. Make sure project is active
get_project_context()

# 2. Create card with dependencies
create_card(
    title="New Feature",
    deliverables=["Implementation", "Tests"],
    validation=["Feature works", "Tests pass"],
    linked_to=5  # Blocks until card 5 is accepted
)

# 3. Check if dependencies met
check_dependencies(card_id="6")
```

## Important Notes

### Documentation Validation
The `submit_card()` tool enforces mandatory documentation:
- **Hard block:** No submission without `output_{card_id}.md`
- **Soft warning:** Documentation < 200 chars
- **Soft warning:** No section headers (`##`)

### Human Review Gates
- Only humans can accept/reject cards
- Cards in `awaiting_acceptance` block downstream work
- Dependencies require acceptance, not just completion

### Project Modes
- **Conversation mode:** No active project, workflow tools show all cards
- **Project mode:** Active project, workflow tools filtered to that project

### Dependency System
- Cards use `linked_to` field to specify blocking cards
- Cards auto-block if dependencies not accepted
- Cards auto-unblock when dependencies accepted
- Check dependencies with `check_dependencies(card_id)`
