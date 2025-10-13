# Project Activation and Namespace System

The Glyphcard system now supports project-scoped workflows with human-controlled activation and deactivation.

## Core Concepts

### Project Mode vs Conversation Mode

- **Conversation Mode**: Default mode where all cards across all projects are visible
- **Project Mode**: Focused mode where only cards from the active project are shown

### Project Context Persistence

Project activation state persists across Claude sessions and is stored in `.glyphcard/project_state.json`.

## Available Commands

### Human CLI Commands

```bash
# List all projects
python project_manager.py list

# Activate a project  
python project_manager.py activate mcp_server_docs

# Deactivate current project (return to conversation mode)
python project_manager.py deactivate

# Show current status
python project_manager.py status
```

### MCP Tools (Available to AI Agents)

#### `list_projects()`
Shows all available projects with card counts and status.

```json
{
  "active_project": "my_web_app",
  "projects": [
    {"name": "my_web_app", "active": true, "card_count": 15},
    {"name": "mobile_app", "active": false, "card_count": 8}
  ],
  "total_projects": 2
}
```

#### `activate_project(project_name)`
Activates a specific project for focused work.

```json
{
  "success": true,
  "active_project": "my_web_app",
  "message": "Activated project 'my_web_app'",
  "card_count": 15
}
```

#### `deactivate_project()`
Returns to conversation mode (all projects visible).

```json
{
  "success": true,
  "deactivated_project": "my_web_app",
  "message": "Deactivated project 'my_web_app'. Now in conversation mode."
}
```

#### `get_project_context()`
Shows current session context and mode.

```json
{
  "mode": "project",
  "active_project": "my_web_app",
  "card_count": 15,
  "timestamp": "2025-10-12T15:30:00.000000"
}
```

## Namespace Integration

### Work Discovery Filtering

When a project is active, `list_my_work()` and `start_work()` automatically filter to only show cards from that project.

**Conversation Mode**: Shows all cards assigned to the agent
**Project Mode**: Shows only cards from the active project assigned to the agent

### Card Creation

The `glyphcard_create_card()` tool now defaults to the active project when no project is specified:

```python
# In project mode - automatically uses active project
glyphcard_create_card(
    title="New Feature",
    deliverables=["Implementation", "Tests"]
)

# Explicit project (works in any mode)
glyphcard_create_card(
    title="Cross-Project Feature", 
    project="other_project",
    deliverables=["Implementation"]
)
```

### Migration Support

Existing cards without proper project fields are automatically discovered and can be migrated:

- Projects are auto-discovered from existing card `project` fields
- Cards can be filtered and managed by project
- No immediate migration required - works with existing card structure

## Workflow Integration

### Project-Scoped Workflows

The system provides the foundation for LangGraph workflow orchestration:

1. **Project Activation**: Human-controlled project switching
2. **Context Isolation**: Work discovery respects project boundaries  
3. **State Persistence**: Project context maintained across sessions
4. **Namespace Consistency**: All tools respect active project context

### Human Control Points

Project activation/deactivation is intentionally human-controlled to ensure:

- Deliberate project switching decisions
- Clear workflow boundaries  
- Human oversight of project scope changes
- Prevention of accidental cross-project work

## File Structure

```
.glyphcard/
  project_state.json      # Project activation state and metadata

project_manager.py        # Core project management functionality
mcp_server.py            # Enhanced with project activation tools
create_card_ai.py        # Updated for project namespace support
```

## Example Workflow

```bash
# Human activates project
python project_manager.py activate my_web_app

# AI agent sees only my_web_app cards
list_my_work()  # Returns only cards from my_web_app project

# AI works within project scope
start_work()    # Starts next available card in my_web_app

# Create new cards in active project context
glyphcard_create_card(
    title="Add Payment Processing",
    deliverables=["Implementation", "Documentation"]
)  # Automatically assigned to my_web_app project

# Human switches projects
python project_manager.py activate mobile_app

# AI now sees different card set
list_my_work()  # Returns only cards from mobile_app project
```

This system provides the foundation for sophisticated workflow orchestration while maintaining human control over project boundaries and context switching.