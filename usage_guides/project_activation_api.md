# Project Activation API Quick Reference

**Copyright (c) 2025 Megan Folsom**
Licensed under the MIT License - see [LICENSE](../LICENSE) for details.

## MCP Tools for AI Agents

### `list_projects()`
**Purpose**: Show all available projects with status and card counts  
**Arguments**: None  
**Returns**: Project list with active status and metadata

```json
{
  "active_project": "mcp_server_docs",
  "projects": [
    {"name": "mcp_server_docs", "active": true, "card_count": 7, "registered": true},
    {"name": "cat_picture_app", "active": false, "card_count": 12, "registered": false}
  ],
  "total_projects": 4
}
```

### `activate_project(project_name)`
**Purpose**: Switch to project mode for focused work  
**Arguments**: `project_name` (string) - Name of project to activate  
**Returns**: Activation status and project information

```json
{
  "success": true,
  "active_project": "mcp_server_docs",
  "previous_project": null,
  "message": "Activated project 'mcp_server_docs'",
  "card_count": 7
}
```

### `deactivate_project()`
**Purpose**: Return to conversation mode (all projects visible)  
**Arguments**: None  
**Returns**: Deactivation status

```json
{
  "success": true,
  "deactivated_project": "mcp_server_docs",
  "message": "Deactivated project 'mcp_server_docs'. Now in conversation mode."
}
```

### `get_project_context()`
**Purpose**: Get current session context and mode  
**Arguments**: None  
**Returns**: Current project context with metadata

```json
{
  "mode": "project",
  "active_project": "mcp_server_docs",
  "timestamp": "2025-09-30T17:47:42.820959",
  "card_count": 7,
  "project_info": {
    "first_activated": "2025-09-30T17:46:31.404075",
    "activation_count": 2,
    "last_activated": "2025-09-30T17:46:31.404084"
  }
}
```

## Enhanced Existing Tools

### `list_my_work()` - Now Project-Aware
- **Conversation Mode**: Shows all cards assigned to agent across all projects
- **Project Mode**: Shows only cards from active project assigned to agent

### `start_work()` - Now Project-Aware  
- **Conversation Mode**: Starts next available card from any project
- **Project Mode**: Starts next available card from active project only

### `glyphcard_create_card()` - Now Project-Aware
- **Project Parameter**: Now optional, defaults to active project
- **Fallback**: Requires explicit project if no project is active

```python
# In project mode - uses active project automatically
glyphcard_create_card(
    title="New Feature",
    deliverables=["Implementation", "Tests"]
)

# Explicit project specification (works in any mode)
glyphcard_create_card(
    title="Cross-Project Feature",
    project="other_project", 
    deliverables=["Implementation"]
)
```

## CLI Commands for Humans

### List Projects
```bash
python project_manager.py list
```
Shows all projects with active status and card counts.

### Activate Project
```bash
python project_manager.py activate <project_name>
```
Activates specified project for focused work mode.

### Deactivate Project
```bash
python project_manager.py deactivate
```
Returns to conversation mode (all projects visible).

### Show Status
```bash
python project_manager.py status
```
Displays current project context and session information.

## Workflow Patterns

### Start Work in Project Context
```python
# Human sets project context
activate_project("mcp_server_docs")

# AI agent works within project scope
work = list_my_work()  # Only shows mcp_server_docs cards
start_work()           # Starts next card in mcp_server_docs
```

### Switch Project Context
```python
# Check current status
context = get_project_context()

# Switch to different project
activate_project("cat_picture_app") 

# Work is now scoped to new project
work = list_my_work()  # Only shows cat_picture_app cards
```

### Return to Multi-Project View
```python
# Exit project mode
deactivate_project()

# See all work across projects
work = list_my_work()  # Shows cards from all projects
```

## Error Handling

All project tools return consistent error structures:

```json
{
  "success": false,
  "error": "Project 'nonexistent' not found",
  "available_projects": ["mcp_server_docs", "cat_picture_app"]
}
```

Common error scenarios:
- **Project not found**: Check spelling and use `list_projects()` to see available projects
- **No active project**: Some operations require active project context
- **Permission errors**: Check file system permissions for `.glyphcard/` directory

## State Management

### Project State Location
- **File**: `.glyphcard/project_state.json`
- **Format**: Human-readable JSON
- **Persistence**: Survives session restarts and system reboots

### State Structure
```json
{
  "active_project": "mcp_server_docs",
  "projects": {
    "mcp_server_docs": {
      "first_activated": "2025-09-30T17:46:31.404075",
      "activation_count": 3,
      "last_activated": "2025-09-30T17:47:42.820959"
    }
  },
  "last_updated": "2025-09-30T17:47:42.820959",
  "version": "1.0"
}
```

This project activation system provides the foundation for sophisticated workflow orchestration while maintaining clear human control over project boundaries and context switching.