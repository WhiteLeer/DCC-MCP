"""Process-isolated execution for Houdini operations."""

import json
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ProcessExecutionError(Exception):
    """Raised when process execution fails."""
    pass


class ProcessTimeoutError(ProcessExecutionError):
    """Raised when process execution times out."""
    pass


class ProcessExecutor:
    """Execute Houdini operations in isolated processes."""

    def __init__(self, hython_path: str, default_timeout: float = 30.0):
        """Initialize process executor.

        Args:
            hython_path: Path to hython executable
            default_timeout: Default timeout in seconds
        """
        self.hython_path = hython_path
        self.default_timeout = default_timeout

    def execute(
        self,
        script_content: str,
        timeout: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute Python script in isolated hython process.

        Args:
            script_content: Python script to execute
            timeout: Timeout in seconds (default: self.default_timeout)
            context: Context data to pass to script

        Returns:
            dict: Result from script execution

        Raises:
            ProcessTimeoutError: If execution times out
            ProcessExecutionError: If execution fails
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        # Create temporary script file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            # Wrap script with context injection and result capture
            wrapper_script = self._create_wrapper_script(script_content, context)
            f.write(wrapper_script)
            script_path = f.name

        try:
            logger.debug(f"Executing script in process (timeout={timeout}s)")
            logger.debug(f"Script: {script_path}")

            # Start hython process
            proc = subprocess.Popen(
                [self.hython_path, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait with timeout
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                returncode = proc.returncode

                elapsed = time.time() - start_time
                logger.debug(f"Process completed in {elapsed:.2f}s (returncode={returncode})")

                # Parse result
                result = self._parse_result(stdout, stderr, returncode, elapsed)
                return result

            except subprocess.TimeoutExpired:
                # Kill the process
                elapsed = time.time() - start_time
                logger.error(f"⏰ Process timeout after {elapsed:.2f}s, killing...")

                proc.kill()
                proc.wait(timeout=5.0)

                raise ProcessTimeoutError(
                    f"Operation timed out after {timeout}s"
                )

        finally:
            # Cleanup temp file
            try:
                Path(script_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp script: {e}")

    def _create_wrapper_script(
        self,
        user_script: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create wrapper script with context and result handling.

        Args:
            user_script: User's operation script
            context: Context data to inject

        Returns:
            str: Complete wrapped script
        """
        context_json = json.dumps(context or {}, ensure_ascii=True)
        context_literal = repr(context_json)

        wrapper = f'''#!/usr/bin/env hython
"""Auto-generated wrapper script for isolated execution."""

import json
import sys
import traceback

# Inject context
_MCP_CONTEXT = json.loads({context_literal})

# Result container
_MCP_RESULT = {{
    "success": False,
    "error": None,
    "data": None,
}}

try:
    # Execute user script
    {self._indent_script(user_script)}

    # If we got here, success
    _MCP_RESULT["success"] = True

except Exception as e:
    _MCP_RESULT["success"] = False
    _MCP_RESULT["error"] = str(e)
    _MCP_RESULT["error_type"] = type(e).__name__
    _MCP_RESULT["traceback"] = traceback.format_exc()
    print(f"ERROR: {{e}}", file=sys.stderr)

# Output result as JSON (last line of stdout)
print("__MCP_RESULT_START__")
print(json.dumps(_MCP_RESULT))
print("__MCP_RESULT_END__")
'''
        return wrapper

    def _indent_script(self, script: str, indent: int = 4) -> str:
        """Indent script lines.

        Args:
            script: Script content
            indent: Number of spaces to indent

        Returns:
            str: Indented script
        """
        lines = script.split('\n')
        indented = [' ' * indent + line if line.strip() else line for line in lines]
        return '\n'.join(indented)

    def _parse_result(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
        elapsed: float
    ) -> Dict[str, Any]:
        """Parse process output to extract result.

        Args:
            stdout: Process stdout
            stderr: Process stderr
            returncode: Process return code
            elapsed: Execution time in seconds

        Returns:
            dict: Parsed result

        Raises:
            ProcessExecutionError: If parsing fails
        """
        # Try to extract JSON result from stdout
        try:
            # Look for result markers
            if "__MCP_RESULT_START__" in stdout and "__MCP_RESULT_END__" in stdout:
                start = stdout.index("__MCP_RESULT_START__") + len("__MCP_RESULT_START__")
                end = stdout.index("__MCP_RESULT_END__")
                result_json = stdout[start:end].strip()

                result = json.loads(result_json)
                result["_timing"] = {
                    "duration_seconds": elapsed,
                    "returncode": returncode,
                }

                # Add stderr if any (warnings, etc)
                if stderr:
                    result["_stderr"] = stderr[:500]  # First 500 chars

                return result

        except Exception as e:
            logger.error(f"Failed to parse result: {e}")

        # Failed to parse, return error
        return {
            "success": False,
            "error": "Failed to parse process result",
            "error_type": "ProcessExecutionError",
            "_timing": {
                "duration_seconds": elapsed,
                "returncode": returncode,
            },
            "_stdout": stdout[:500] if stdout else None,
            "_stderr": stderr[:500] if stderr else None,
        }


def execute_houdini_operation(
    hython_path: str,
    operation_script: str,
    timeout: float = 30.0,
    **params
) -> Dict[str, Any]:
    """Convenience function to execute Houdini operation.

    Args:
        hython_path: Path to hython executable
        operation_script: Python script to execute
        timeout: Timeout in seconds
        **params: Parameters to pass to script

    Returns:
        dict: Operation result
    """
    executor = ProcessExecutor(hython_path, default_timeout=timeout)
    return executor.execute(operation_script, timeout=timeout, context=params)
