# Local MCP Troubleshooting

This guide covers the most common reasons a **local coding agent** (such as a locally hosted Codex instance) cannot discover the Glyphcard MCP tools, along with diagnostic steps to fix the issue.

## 1. Confirm the MCP Server Starts

The local agent can only enumerate tools if the `mcp_server.py` process is reachable.

```bash
cd /path/to/glyphcard_workflow
source .venv/bin/activate
python mcp_server.py --health-check
```

- If you see `MCP server healthy`, the command path is valid.
- If the process crashes, resolve the Python or dependency issue before proceeding.

> **Tip:** Run `pip install -r requirements.txt` inside the virtual environment if dependencies are missing.

## 2. Verify the Config File the Agent Reads

Most local MCP-capable agents read configuration from one of the following files:

- `.mcp.json` in the current workspace (used by VSCode and several Codex-based shells).
- `~/.config/mcp/servers.json` (global configuration for some CLI agents).

Make sure the entry pointing at Glyphcard matches your environment. A working example looks like:

```json
{
  "servers": {
    "glyphcard-workflow": {
      "type": "stdio",
      "command": "/absolute/path/to/.venv/bin/python",
      "args": [
        "/absolute/path/to/glyphcard_workflow/mcp_server.py"
      ]
    }
  },
  "inputs": []
}
```

### Quick Checks

- The `command` must be the **exact** Python executable inside the active virtual environment.
- The `args` path must resolve to the Glyphcard `mcp_server.py` file.
- Use absolute paths—relative paths will fail for most agents.

## 3. Test Tool Discovery Manually

Once the configuration is correct, run the agent’s built-in command to list available tools. For example, the local Codex agent accepts:

```text
list tools
```

If the response is empty:

1. Restart the agent to ensure it reloads the MCP configuration.
2. Run the agent in verbose/logging mode (usually `--debug`) to inspect MCP connection errors.

## 4. Common Failure Modes

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ENOENT` or "file not found" in logs | Config points to the wrong Python executable or repo path | Regenerate the `.mcp.json` entry with absolute paths |
| Agent says "no MCP servers configured" | Config file is not in the workspace the agent opened | Copy `.mcp.json` to that directory or provide a global config |
| Agent times out | MCP server waiting for stdin/stdout but agent trying to connect via sockets | Ensure server `type` is set to `stdio` |
| Tools partially load | Missing environment variables (e.g., `PYTHONPATH`) | Launch agent from a shell where the virtual environment is activated |

## 5. When All Else Fails

- Run the MCP server directly with logging enabled:

  ```bash
  python mcp_server.py --log-level DEBUG
  ```

- Capture the output and compare it against the agent’s error logs.
- If the agent still cannot discover the tools, file an issue with:
  - Your OS and shell
  - Agent name/version
  - Exact command used to start the agent
  - The MCP configuration snippet

With these diagnostics, maintainers can quickly spot path or environment mismatches that prevent tool discovery.
