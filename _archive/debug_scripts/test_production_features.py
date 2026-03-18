#!/usr/bin/env python3
"""Quick test for production features."""

import time

from houdini_mcp.utils.logging_config import setup_logging, log_operation, log_error
from houdini_mcp.utils.timeout import timeout, TimeoutError
from houdini_mcp.utils.tool_wrapper import production_tool

# Setup logging
logger = setup_logging(name="test", log_level="DEBUG")

logger.info("=" * 60)
logger.info("Testing Production Features")
logger.info("=" * 60)

# Test 1: Logging
logger.info("✅ Test 1: Logging system")
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

# Test 2: Timeout decorator
logger.info("\n✅ Test 2: Timeout protection")

@timeout(seconds=2.0)
def quick_operation():
    time.sleep(0.5)
    return "success"

@timeout(seconds=1.0)
def slow_operation():
    time.sleep(5.0)
    return "should timeout"

try:
    result = quick_operation()
    logger.info(f"Quick operation: {result}")
except TimeoutError as e:
    logger.error(f"Unexpected timeout: {e}")

try:
    result = slow_operation()
    logger.error(f"Should not reach here: {result}")
except TimeoutError as e:
    logger.info(f"Caught expected timeout: {e}")

# Test 3: Production tool wrapper
logger.info("\n✅ Test 3: Production tool wrapper")

@production_tool(timeout_seconds=2.0, retry_count=1)
def test_tool(value: int) -> dict:
    """Test tool function."""
    if value < 0:
        raise ValueError("Negative value not allowed")
    time.sleep(0.2)
    return {
        "success": True,
        "result": value * 2
    }

# Success case
result = test_tool(value=5)
logger.info(f"Result: {result}")

# Failure case
result = test_tool(value=-1)
logger.info(f"Error result: {result}")

# Test 4: Error logging
logger.info("\n✅ Test 4: Error context")

try:
    raise RuntimeError("Test error with context")
except Exception as e:
    log_error(logger, "test_operation", e, param1="value1", param2=123)

logger.info("\n" + "=" * 60)
logger.info("All tests completed!")
logger.info("Check logs at: ~/.mcp_logs/test/")
logger.info("=" * 60)
