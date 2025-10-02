# VSCode MCP Setup Guide

This guide shows how to set up the Glyphcard MCP server in VSCode (including VSCode with WSL).

## Prerequisites

- VSCode with MCP extension installed
- Python 3.12+
- Glyphcard repository cloned

## Setup Steps

### 1. Activate Virtual Environment and Get Python Path

**On WSL/Ubuntu:**
```bash
cd /path/to/glyphcard
source .venv/bin/activate
which python
```

**On macOS/Linux:**
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

Copy the Python path that gets printed (e.g., `/home/username/glyphcard/.venv/bin/python`)

### 2. Add MCP Server in VSCode

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type and select: **MCP: Add Server**
3. Choose: **command (stdio)**
4. Enter the command:
   ```
   /path/to/your/.venv/bin/python /path/to/your/glyphcard/mcp_server.py
   ```
   **Example on WSL:**
   ```
   /home/rowandev/glyphcard/.venv/bin/python /home/rowandev/glyphcard/mcp_server.py
   ```

   **Example on macOS:**
   ```
   /Users/yourname/glyphcard/.venv/bin/python /Users/yourname/glyphcard/mcp_server.py
   ```

   **Example on Windows:**
   ```
   C:\Users\yourname\glyphcard\.venv\Scripts\python.exe C:\Users\yourname\glyphcard\mcp_server.py
   ```

5. Choose: **workspace**
6. Enter name: **glyphcard-workflow**

### 3. Verify Configuration

VSCode will create a `.mcp.json` file in your workspace with content like:

**WSL/Ubuntu/macOS:**
```json
{
    "servers": {
        "glyphcard-workflow": {
            "type": "stdio",
            "command": "/home/rowandev/glyphcard/.venv/bin/python",
            "args": [
                "/home/rowandev/glyphcard/mcp_server.py"
            ]
        }
    },
    "inputs": []
}
```

**Windows:**
```json
{
    "servers": {
        "glyphcard-workflow": {
            "type": "stdio",
            "command": "C:\\Users\\yourname\\glyphcard\\.venv\\Scripts\\python.exe",
            "args": [
                "C:\\Users\\yourname\\glyphcard\\mcp_server.py"
            ]
        }
    },
    "inputs": []
}
```

### 4. Reload VSCode

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P`)
2. Type and select: **Developer: Reload Window**

### 5. Test the Connection

In your AI assistant panel in VSCode, try:
- "list my work"
- "what projects are available?"
- "health check"

You should see the MCP tools responding with Glyphcard data.

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

## Troubleshooting

### Server shows as "Failed"

**Check Python Path:**
```bash
source .venv/bin/activate
which python  # This path must exactly match what's in .mcp.json
```

**Verify Server Runs Standalone:**
```bash
source .venv/bin/activate
python mcp_server.py
```
You should see the FastMCP banner. Press `Ctrl+C` to exit.

**Check Dependencies:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### WSL-Specific Issues

**Ensure WSL path format:**
- Use `/home/username/...` not `\\wsl$\Ubuntu\home\...`
- Use forward slashes `/` not backslashes `\`

**Check WSL Python:**
```bash
# Inside WSL terminal
source .venv/bin/activate
which python
# Should show: /home/username/glyphcard/.venv/bin/python
```

### Windows-Specific Issues

**Use double backslashes in JSON:**
```json
"command": "C:\\Users\\yourname\\glyphcard\\.venv\\Scripts\\python.exe"
```

**Or use forward slashes:**
```json
"command": "C:/Users/yourname/glyphcard/.venv/Scripts/python.exe"
```

## Platform-Specific Notes

### WSL (Windows Subsystem for Linux)
- Open your project in WSL: Remote-WSL extension
- Use Linux-style paths in `.mcp.json`
- Python path format: `/home/username/...`

### macOS
- Python path format: `/Users/username/...`
- May need to use full path even with venv activated

### Windows (Native)
- Use `.venv\Scripts\python.exe` not `bin/python`
- Escape backslashes in JSON: `\\`
- Or use forward slashes: `/`
