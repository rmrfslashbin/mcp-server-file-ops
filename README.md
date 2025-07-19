# MCP Server - File Operations

A Model Context Protocol (MCP) server that provides cross-platform file operations like opening files with default applications and revealing files in file explorers.

## Features

- **Open files**: Open any file with its default application (`open` on macOS, `xdg-open` on Linux, `start` on Windows)
- **Reveal in file manager**: Show files in Finder (macOS), file manager (Linux), or Explorer (Windows)
- **Cross-platform**: Works on macOS, Linux, and Windows
- **Path validation**: Ensures files exist before attempting operations
- **Detailed logging**: Comprehensive error reporting and operation tracking

## Tools Available

### `open_file`
Opens a file or directory with the system's default application.
- **Parameters:**
  - `path` (required): Absolute or relative path to the file/directory
  - `application` (optional): Specific application to use (macOS only)

### `reveal_file`
Reveals a file or directory in the system's file manager.
- **Parameters:**
  - `path` (required): Absolute or relative path to the file/directory

## Installation

```bash
# Install with uv (recommended)
uv add mcp-server-file-ops

# Or install with pip
pip install mcp-server-file-ops
```

## Usage with MCP

Add to your MCP configuration:

```json
{
  "servers": {
    "file-ops": {
      "command": ["uv", "run", "python", "-m", "mcp_server_file_ops"],
      "cwd": "/path/to/mcp-server-file-ops"
    }
  }
}
```

## Examples

```python
# Open an image with default application
open_file(path="./generated_image.png")

# Open a specific application on macOS
open_file(path="./document.pdf", application="Preview")

# Reveal a file in file manager
reveal_file(path="./important_file.txt")
```

## Development

```bash
# Clone the repository
git clone https://github.com/rmrfslashbin/mcp-server-file-ops.git
cd mcp-server-file-ops

# Install dependencies
uv sync

# Run the server
uv run python -m mcp_server_file_ops
```

## License

MIT License - see LICENSE file for details.