#!/usr/bin/env python3
"""Test process-isolated execution."""

import logging
from houdini_mcp.core.process_executor import ProcessExecutor, ProcessTimeoutError
from houdini_mcp.core.operation_scripts import CREATE_BOX_SCRIPT, GET_SCENE_STATE_SCRIPT
from houdini_mcp.utils.logging_config import setup_logging

# Setup logging
logger = setup_logging(name="test-process", log_level="INFO")

logger.info("=" * 60)
logger.info("Testing Process-Isolated Execution")
logger.info("=" * 60)

# Create executor
hython_path = "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe"
executor = ProcessExecutor(hython_path, default_timeout=30.0)

logger.info(f"Hython path: {hython_path}")

# Test 1: Get scene state (quick)
logger.info("\n✅ Test 1: Get scene state (should be fast)")
try:
    result = executor.execute(GET_SCENE_STATE_SCRIPT, timeout=10.0)
    logger.info(f"Result: {result['success']}")
    if result["success"]:
        logger.info(f"Scene data: {result['data']}")
    else:
        logger.error(f"Error: {result.get('error')}")
except ProcessTimeoutError as e:
    logger.error(f"Timeout: {e}")

# Test 2: Create box (normal operation)
logger.info("\n✅ Test 2: Create box")
try:
    result = executor.execute(
        CREATE_BOX_SCRIPT,
        timeout=15.0,
        context={"node_name": "test_box", "size_x": 2.0, "size_y": 1.0, "size_z": 1.5}
    )
    logger.info(f"Result: {result['success']}")
    if result["success"]:
        logger.info(f"Box data: {result['data']}")
        logger.info(f"Timing: {result.get('_timing')}")
    else:
        logger.error(f"Error: {result.get('error')}")
except ProcessTimeoutError as e:
    logger.error(f"Timeout: {e}")

# Test 3: Timeout test (intentional hang)
logger.info("\n✅ Test 3: Timeout protection (will timeout in 5s)")
timeout_script = '''
import time
import hou

# This will hang for 30 seconds
print("Starting hang...")
time.sleep(30)

_MCP_RESULT["data"] = {"message": "Should not see this"}
'''

try:
    result = executor.execute(timeout_script, timeout=5.0)
    logger.error(f"Should not reach here! Result: {result}")
except ProcessTimeoutError as e:
    logger.info(f"✅ Timeout caught correctly: {e}")

logger.info("\n" + "=" * 60)
logger.info("All tests completed!")
logger.info("=" * 60)
