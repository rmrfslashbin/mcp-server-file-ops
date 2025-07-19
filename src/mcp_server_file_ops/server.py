"""MCP server for cross-platform file operations."""

import asyncio
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("mcp-server-file-ops")


def get_platform_commands():
    """Get platform-specific commands for file operations."""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        return {
            "open": ["open"],
            "reveal": ["open", "-R"]
        }
    elif system == "linux":
        return {
            "open": ["xdg-open"],
            "reveal": ["xdg-open"]  # Will open containing directory
        }
    elif system == "windows":
        return {
            "open": ["start", ""],  # Empty string is required for start command
            "reveal": ["explorer", "/select,"]
        }
    else:
        raise OSError(f"Unsupported platform: {system}")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available file operation tools."""
    return [
        Tool(
            name="open_file",
            description="Open a file or directory with the system's default application",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory to open (absolute or relative)",
                    },
                    "application": {
                        "type": "string",
                        "description": "Specific application to use for opening (macOS only, optional)",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="reveal_file",
            description="Reveal/show a file or directory in the system's file manager",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory to reveal (absolute or relative)",
                    },
                },
                "required": ["path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls for file operations."""
    if name == "open_file":
        return await open_file_tool(**arguments)
    elif name == "reveal_file":
        return await reveal_file_tool(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def open_file_tool(
    path: str,
    application: Optional[str] = None
) -> list[TextContent]:
    """Open a file or directory with the system's default application."""
    
    logger.info(f"Opening file: {path}")
    
    try:
        # Resolve and validate path
        file_path = Path(path).resolve()
        if not file_path.exists():
            error_msg = f"❌ **File Not Found**\\n\\nPath does not exist: `{file_path}`"
            logger.error(f"File not found: {file_path}")
            return [TextContent(type="text", text=error_msg)]
        
        # Get platform-specific commands
        try:
            commands = get_platform_commands()
        except OSError as e:
            error_msg = f"❌ **Platform Error**\\n\\n{str(e)}"
            logger.error(str(e))
            return [TextContent(type="text", text=error_msg)]
        
        # Build command
        cmd = commands["open"].copy()
        
        # Handle macOS-specific application parameter
        if application and platform.system().lower() == "darwin":
            cmd.extend(["-a", application])
        elif application:
            logger.warning(f"Application parameter '{application}' ignored on {platform.system()}")
        
        # Add the file path
        cmd.append(str(file_path))
        
        # Execute command
        logger.debug(f"Executing command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            app_info = f" with {application}" if application else ""
            response_text = f"""✅ **File Opened Successfully!**

**Path:** `{file_path}`
**Action:** Opened{app_info} with system default application
**Platform:** {platform.system()}

The file has been opened and should now be visible in the appropriate application."""
            
            logger.info(f"Successfully opened: {file_path}")
            return [TextContent(type="text", text=response_text)]
        else:
            stderr_text = stderr.decode('utf-8').strip() if stderr else "No error details"
            error_msg = f"""❌ **Failed to Open File**

**Path:** `{file_path}`
**Error Code:** {process.returncode}
**Error Details:** {stderr_text}
**Command:** `{' '.join(cmd)}`"""
            
            logger.error(f"Command failed with return code {process.returncode}: {stderr_text}")
            return [TextContent(type="text", text=error_msg)]
            
    except Exception as e:
        error_msg = f"❌ **Unexpected Error**\\n\\n**Error:** {str(e)}\\n**Path:** `{path}`"
        logger.error(f"Unexpected error opening file: {str(e)}")
        return [TextContent(type="text", text=error_msg)]


async def reveal_file_tool(path: str) -> list[TextContent]:
    """Reveal a file or directory in the system's file manager."""
    
    logger.info(f"Revealing file: {path}")
    
    try:
        # Resolve and validate path
        file_path = Path(path).resolve()
        if not file_path.exists():
            error_msg = f"❌ **File Not Found**\\n\\nPath does not exist: `{file_path}`"
            logger.error(f"File not found: {file_path}")
            return [TextContent(type="text", text=error_msg)]
        
        # Get platform-specific commands
        try:
            commands = get_platform_commands()
        except OSError as e:
            error_msg = f"❌ **Platform Error**\\n\\n{str(e)}"
            logger.error(str(e))
            return [TextContent(type="text", text=error_msg)]
        
        # Build command
        cmd = commands["reveal"].copy()
        
        # Platform-specific path handling
        system = platform.system().lower()
        if system == "windows":
            # Windows explorer requires forward slashes to be converted
            cmd.append(str(file_path).replace('/', '\\'))
        else:
            cmd.append(str(file_path))
        
        # Execute command
        logger.debug(f"Executing command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Get appropriate file manager name
            file_manager = {
                "darwin": "Finder",
                "linux": "File Manager", 
                "windows": "Explorer"
            }.get(system, "File Manager")
            
            response_text = f"""✅ **File Revealed Successfully!**

**Path:** `{file_path}`
**Action:** Revealed in {file_manager}
**Platform:** {platform.system()}

The file location has been opened in your system's file manager."""
            
            logger.info(f"Successfully revealed: {file_path}")
            return [TextContent(type="text", text=response_text)]
        else:
            stderr_text = stderr.decode('utf-8').strip() if stderr else "No error details"
            error_msg = f"""❌ **Failed to Reveal File**

**Path:** `{file_path}`
**Error Code:** {process.returncode}
**Error Details:** {stderr_text}
**Command:** `{' '.join(cmd)}`"""
            
            logger.error(f"Command failed with return code {process.returncode}: {stderr_text}")
            return [TextContent(type="text", text=error_msg)]
            
    except Exception as e:
        error_msg = f"❌ **Unexpected Error**\\n\\n**Error:** {str(e)}\\n**Path:** `{path}`"
        logger.error(f"Unexpected error revealing file: {str(e)}")
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Run the MCP file operations server."""
    logger.info("Starting MCP File Operations Server...")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())