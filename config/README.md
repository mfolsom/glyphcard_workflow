# Glyphcard MCP Server Configuration Examples

## Basic Configuration

### For Claude Code CLI
Place this configuration in `~/.config/claude-code/mcp_servers.json`:

```json
{
  "servers": {
    "glyphcard-workflow": {
      "command": "python",
      "args": ["/path/to/your/glyphcard/mcp_server.py"],
      "description": "Glyphcard workflow automation server"
    }
  }
}
```

### For Other MCP Clients
```json
{
  "servers": {
    "glyphcard": {
      "command": "/path/to/python",
      "args": ["/path/to/glyphcard/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/glyphcard"
      }
    }
  }
}
```

## Advanced Configuration

### With Virtual Environment
```json
{
  "servers": {
    "glyphcard-workflow": {
      "command": "/path/to/glyphcard/.venv/bin/python",
      "args": ["/path/to/glyphcard/mcp_server.py"],
      "description": "Glyphcard workflow automation server",
      "env": {
        "VIRTUAL_ENV": "/path/to/glyphcard/.venv"
      }
    }
  }
}
```

### With Custom Agent Name
```json
{
  "servers": {
    "glyphcard-workflow": {
      "command": "python",
      "args": ["/path/to/glyphcard/mcp_server.py"],
      "description": "Glyphcard workflow automation server",
      "env": {
        "GLYPHCARD_AGENT": "gpt"
      }
    }
  }
}
```

## Environment Variables

- `GLYPHCARD_AGENT`: Set the agent name (default: "claude")
- `GLYPHCARD_BASE_DIR`: Override the base directory path
- `PYTHONPATH`: Ensure Python can find required modules

## Troubleshooting

### Common Issues

1. **Server not starting**: Check Python path and dependencies
2. **Tools not available**: Verify MCP client configuration
3. **Permission errors**: Ensure files are readable and executable

### Validation
Use the setup helper to validate your configuration:
```bash
python integration/setup_mcp.py --validate
```