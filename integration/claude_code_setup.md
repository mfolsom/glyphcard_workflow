# Claude Code MCP Setup Guide

This guide shows how to set up the Glyphcard MCP server in Claude Code CLI.

## Prerequisites

- Claude Code CLI installed
- Python 3.12+
- Glyphcard repository cloned
- Virtual environment created and dependencies installed

## Setup Steps

### 1. Get Your Python Virtual Environment Path

**On Linux/macOS/WSL:**
```bash
cd /path/to/glyphcard
source .venv/bin/activate
which python
```

**On Windows:**
```bash
cd C:\path\to\glyphcard
.venv\Scripts\activate
where python
```

Copy the full path to your virtual environment's Python (e.g., `/home/username/glyphcard/.venv/bin/python`)

### 2. Add MCP Server via CLI

**Important:** You need to provide both the Python interpreter AND the server script as separate arguments.

**On Linux/macOS/WSL:**
```bash
claude mcp add glyphcard-workflow \
  /home/yourname/glyphcard/.venv/bin/python \
  /home/yourname/glyphcard/mcp_server.py \
  -s local
```

**On Windows:**
```bash
claude mcp add glyphcard-workflow ^
  C:\Users\yourname\glyphcard\.venv\Scripts\python.exe ^
  C:\Users\yourname\glyphcard\mcp_server.py ^
  -s local
```

### 3. Verify Configuration

Check that it was added correctly:
```bash
claude mcp get glyphcard-workflow
```

You should see:
```
glyphcard-workflow:
  Scope: Local (private to you in this project)
  Type: stdio
  Command: /path/to/.venv/bin/python
  Args: /path/to/mcp_server.py
  Environment:
```

### 4. Restart Claude Code

Close and reopen your Claude Code session for the MCP server to load.

### 5. Test the Connection

In Claude Code, try:
- "list my work"
- "what projects are available?"
- "health check the glyphcard server"

You should see responses from the Glyphcard MCP tools.

## Available Tools

Once configured, you'll have access to **15 MCP tools**:

**Core Workflow:**
- `start_work()` - Auto-discover and start next card
- `get_card_context()` - Get card details with progress
- `submit_card()` - Submit with documentation validation
- `list_my_work()` - See available/blocked cards

**Project Management:**
- `list_projects()` - View all projects
- `activate_project()` - Switch to project mode
- `deactivate_project()` - Return to conversation mode
- `get_project_context()` - Current project status
- `create_project()` - Create new project

**Card Management:**
- `create_card()` - Create new cards
- `check_dependencies()` - Verify prerequisites

**Archive:**
- `archive_card()` - Archive completed cards
- `list_archived_cards()` - View archive
- `cleanup_acceptance_tracking()` - Clean tracking

**System:**
- `health_check()` - Verify server status

See [../mcp_server_docs/tools_reference.md](../mcp_server_docs/tools_reference.md) for complete tool documentation.

## Configuration File

Claude Code stores the configuration in: `~/.config/claude-code/mcp_servers.json`

The file should look like:

**Linux/macOS/WSL:**
```json
{
  "mcpServers": {
    "glyphcard-workflow": {
      "command": "/home/yourname/glyphcard/.venv/bin/python",
      "args": [
        "/home/yourname/glyphcard/mcp_server.py"
      ],
      "cwd": "/home/yourname/glyphcard",
      "env": {}
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "glyphcard-workflow": {
      "command": "C:\\Users\\yourname\\glyphcard\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\yourname\\glyphcard\\mcp_server.py"
      ],
      "cwd": "C:\\Users\\yourname\\glyphcard",
      "env": {}
    }
  }
}
```

## Troubleshooting

### Server shows as "Failed"

**Common Issue: Wrong Command Format**

❌ **WRONG:**
```bash
# Don't do this - it tries to execute the .py file directly
claude mcp add glyphcard-workflow /path/to/mcp_server.py
```

✅ **CORRECT:**
```bash
# Provide Python interpreter first, then script path
claude mcp add glyphcard-workflow \
  /path/to/.venv/bin/python \
  /path/to/mcp_server.py \
  -s local
```

**Check Dependencies:**
```bash
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Verify Server Runs Standalone:**
```bash
source .venv/bin/activate
python mcp_server.py
```

You should see the FastMCP banner. Press `Ctrl+C` to exit.

**Check Python Path is Correct:**
```bash
source .venv/bin/activate
which python  # Linux/macOS/WSL
where python  # Windows
```

The path must exactly match what you used in the `claude mcp add` command.

### Remove and Re-add Server

If you need to start over:

```bash
# Remove the server
claude mcp remove glyphcard-workflow -s local

# Add it again with correct paths
claude mcp add glyphcard-workflow \
  /correct/path/to/.venv/bin/python \
  /correct/path/to/mcp_server.py \
  -s local

# Restart Claude Code
```

### WSL-Specific Notes

- Use Linux-style paths: `/home/username/...`
- Don't use Windows paths like `\\wsl$\Ubuntu\...`
- The Python path should be from inside WSL

### Windows-Specific Notes

- Use `.venv\Scripts\python.exe` not `bin/python`
- Paths can use forward slashes `/` or double backslashes `\\`
- Run commands in PowerShell or Command Prompt

## Platform Examples

### Ubuntu/WSL Example
```bash
claude mcp add glyphcard-workflow \
  /home/rowandev/glyphcard/.venv/bin/python \
  /home/rowandev/glyphcard/mcp_server.py \
  -s local
```

### macOS Example
```bash
claude mcp add glyphcard-workflow \
  /Users/yourname/glyphcard/.venv/bin/python \
  /Users/yourname/glyphcard/mcp_server.py \
  -s local
```

### Windows Example
```bash
claude mcp add glyphcard-workflow ^
  C:/Users/yourname/glyphcard/.venv/Scripts/python.exe ^
  C:/Users/yourname/glyphcard/mcp_server.py ^
  -s local
```
