# MCP Server Integration Guides

Step-by-step setup guides for using the Glyphcard MCP server with different AI coding assistants.

## Available Guides

### ✅ Claude Code CLI
**File:** [claude_code_setup.md](claude_code_setup.md)

Complete guide for setting up Glyphcard MCP server in Claude Code CLI.
- Works on Linux, macOS, Windows, and WSL
- Command-line configuration
- Troubleshooting tips

### ✅ VSCode (with MCP Extension)
**File:** [vscode_setup.md](vscode_setup.md)

Complete guide for setting up Glyphcard MCP server in VSCode.
- Works with native VSCode and Remote-WSL
- GUI-based configuration
- Platform-specific examples

## Coming Soon

We're working on setup guides for:
- [ ] Cursor IDE
- [ ] Windsurf
- [ ] Other MCP-compatible clients

## Quick Start

Choose your environment:

**Claude Code:**
```bash
claude mcp add glyphcard-workflow \
  /path/to/.venv/bin/python \
  /path/to/mcp_server.py \
  -s local
```

**VSCode:**
1. Press `Ctrl+Shift+P`
2. Choose "MCP: Add Server"
3. Follow the prompts

See the detailed guides above for complete instructions.

## Available MCP Tools

Once configured, AI assistants have access to **15 MCP tools**:

**Core Workflow:**
- `start_work()` - Auto-discover and start next card
- `get_card_context()` - Get card details with progress tracking
- `submit_card()` - Submit with mandatory documentation validation
- `list_my_work()` - See available and blocked cards

**Project Management:**
- `list_projects()` - View all projects
- `activate_project()` - Switch to project mode
- `deactivate_project()` - Return to conversation mode
- `get_project_context()` - Get current project status
- `create_project()` - Create new project workspace

**Card Management:**
- `create_card()` - Create new work cards
- `check_dependencies()` - Verify card prerequisites

**Archive Management:**
- `archive_card()` - Archive completed cards
- `list_archived_cards()` - View archived cards
- `cleanup_acceptance_tracking()` - Clean up tracking

**System:**
- `health_check()` - Verify server is running

**📚 See [../mcp_server_docs/tools_reference.md](../mcp_server_docs/tools_reference.md) for complete tool documentation with examples.**

## Prerequisites

All guides assume you have:
- Python 3.12 or higher
- Glyphcard repository cloned
- Virtual environment created: `python -m venv .venv`
- Dependencies installed: `pip install -r requirements.txt`

## Troubleshooting

### Server Shows as "Failed"

1. **Verify Python path is correct**
   ```bash
   source .venv/bin/activate
   which python  # Use this exact path
   ```

2. **Test server runs standalone**
   ```bash
   source .venv/bin/activate
   python mcp_server.py
   ```

3. **Check dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

### Platform-Specific Issues

**WSL:** Use Linux paths (`/home/...`) not Windows paths
**Windows:** Use `.venv\Scripts\python.exe` not `bin/python`
**macOS:** May need full path even with venv activated

See the individual setup guides for detailed troubleshooting.

## Need Help?

- Check the detailed setup guide for your platform
- Review [../mcp_server_docs/tools_reference.md](../mcp_server_docs/tools_reference.md)
- Open an issue on GitHub

## Contributing

Have a working setup for another MCP client? We'd love to add it!

Please submit a PR with your setup guide following the format of existing guides.
