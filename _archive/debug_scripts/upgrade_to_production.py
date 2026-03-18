#!/usr/bin/env python3
"""Upgrade script to add production features to server.py."""

import re
import shutil
from pathlib import Path


def upgrade_server():
    """Add production features to existing server.py."""

    server_file = Path("houdini_mcp/server.py")
    backup_file = Path("houdini_mcp/server.py.backup")

    print("🔧 Upgrading server.py to production version...")

    # Backup original
    if not backup_file.exists():
        shutil.copy2(server_file, backup_file)
        print(f"✅ Backup created: {backup_file}")

    # Read original
    content = server_file.read_text(encoding='utf-8')

    # 1. Add imports at the top (after existing imports)
    imports_to_add = '''
# Production utilities
from houdini_mcp.utils.logging_config import setup_logging, log_operation, log_error
from houdini_mcp.utils.tool_wrapper import production_tool
from houdini_mcp.utils.health_check import create_simple_health_checker
from houdini_mcp.utils.timeout import TimeoutError
'''

    # Find the line after "from houdini_mcp.adapter.houdini_adapter import get_adapter"
    content = content.replace(
        'from houdini_mcp.adapter.houdini_adapter import get_adapter',
        'from houdini_mcp.adapter.houdini_adapter import get_adapter' + imports_to_add
    )

    # 2. Replace basic logging with production logging
    content = content.replace(
        '''# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("houdini-mcp-server")''',
        '''# Configure production logging
logger = setup_logging(
    name="houdini-mcp",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)
logger.info("=" * 80)
logger.info("🚀 Houdini MCP Server - Production Mode")
logger.info("=" * 80)'''
    )

    # 3. Add @production_tool decorator to all @mcp.tool() functions
    # Find all tool definitions
    tool_pattern = r'(@mcp\.tool\(\)\s+def\s+\w+\()'

    def add_production_wrapper(match):
        return f'@production_tool(timeout_seconds=30.0, retry_count=1)\n    {match.group(1)}'

    content = re.sub(tool_pattern, add_production_wrapper, content)

    # 4. Add health checker initialization in create_server
    health_check_code = '''
    # Initialize health checker
    logger.info("🏥 Starting health checker...")
    health_checker = create_simple_health_checker(
        get_scene_state_func=adapter.get_scene_state,
        interval=15.0,  # Check every 15 seconds
    )
    health_checker.start()
    logger.info("🏥 Health checker active")
'''

    # Insert before "# Register MCP Tools"
    content = content.replace(
        '    # Register MCP Tools',
        health_check_code + '\n    # Register MCP Tools'
    )

    # 5. Add health check tool
    health_tool_code = '''
    @mcp.tool()
    @production_tool(timeout_seconds=5.0)
    def health_check() -> dict:
        """Check MCP server and Houdini health status.

        Returns:
            dict: Health status information.
        """
        try:
            health_status = health_checker.get_status()
            scene_state = adapter.get_scene_state()

            return {
                "success": True,
                "server_healthy": health_status["healthy"],
                "houdini_running": scene_state is not None,
                "consecutive_failures": health_status["consecutive_failures"],
                "last_check": health_status["last_check"],
            }
        except Exception as e:
            log_error(logger, "health_check", e)
            return {
                "success": False,
                "error": str(e)
            }

'''

    # Insert after the boolean tool, before resources
    content = content.replace(
        '    # Register resources',
        health_tool_code + '\n    # Register resources'
    )

    # Write upgraded version
    server_file.write_text(content, encoding='utf-8')
    print(f"✅ Upgraded {server_file}")
    print(f"📝 Backup saved at: {backup_file}")
    print()
    print("🎉 Production features added:")
    print("   - ✅ File logging (~/.mcp_logs/houdini-mcp/)")
    print("   - ✅ Colored console output")
    print("   - ✅ 30s timeout on all operations")
    print("   - ✅ Auto-retry (1 attempt)")
    print("   - ✅ Health checking (15s interval)")
    print("   - ✅ Detailed error context")
    print("   - ✅ Operation timing")
    print()
    print("To test: python -m houdini_mcp.server")


if __name__ == "__main__":
    upgrade_server()
