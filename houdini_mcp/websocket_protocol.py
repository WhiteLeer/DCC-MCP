"""WebSocket Protocol for MCP GUI Control.

Messages between GUI and MCP Server.
"""

from typing import Any, Dict, Optional
from enum import Enum
import json


class MessageType(str, Enum):
    """Message types for WebSocket communication."""

    # GUI -> Server (Commands)
    RESTART_HOUDINI = "restart_houdini"
    RESTART_MCP_SERVER = "restart_mcp_server"
    GET_PROCESS_COUNT = "get_process_count"
    RELOAD_CONFIG = "reload_config"
    CLEAR_CACHE = "clear_cache"
    UPDATE_TIMEOUT = "update_timeout"
    SHUTDOWN = "shutdown"
    GET_STATUS = "get_status"
    INVOKE_TOOL = "invoke_tool"

    # Server -> GUI (Status updates)
    STATUS_UPDATE = "status_update"
    PROCESS_COUNT = "process_count"
    OPERATION_LOG = "operation_log"
    LOG_MESSAGE = "log_message"
    PERFORMANCE_METRICS = "performance_metrics"
    TOOL_RESULT = "tool_result"
    ERROR = "error"


class WSMessage:
    """WebSocket message wrapper."""

    def __init__(
        self,
        message_type: MessageType,
        data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.type = message_type
        self.data = data or {}
        self.request_id = request_id

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "request_id": self.request_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> "WSMessage":
        """Parse from JSON string."""
        data = json.loads(json_str)
        return cls(
            message_type=MessageType(data["type"]),
            data=data.get("data", {}),
            request_id=data.get("request_id")
        )


# Response builders for common messages

def status_update(
    server_running: bool,
    uptime_seconds: float,
    houdini_connected: bool,
    houdini_pid: Optional[int] = None,
    backend_pid: Optional[int] = None,
    scene_node_count: Optional[int] = None,
    hip_file: Optional[str] = None,
) -> WSMessage:
    """Create status update message."""
    return WSMessage(
        MessageType.STATUS_UPDATE,
        {
            "server_running": server_running,
            "uptime_seconds": uptime_seconds,
            "houdini_connected": houdini_connected,
            "houdini_pid": houdini_pid,
            "backend_pid": backend_pid,
            "scene_node_count": scene_node_count,
            "hip_file": hip_file,
        }
    )


def operation_log(
    timestamp: str,
    operation: str,
    status: str,
    duration: float,
    params: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> WSMessage:
    """Create operation log message."""
    return WSMessage(
        MessageType.OPERATION_LOG,
        {
            "timestamp": timestamp,
            "operation": operation,
            "status": status,
            "duration": duration,
            "params": params,
            "result": result,
            "error": error
        }
    )


def log_message(level: str, message: str, timestamp: str) -> WSMessage:
    """Create log message."""
    return WSMessage(
        MessageType.LOG_MESSAGE,
        {
            "level": level,
            "message": message,
            "timestamp": timestamp
        }
    )


def performance_metrics(
    total_operations: int,
    success_rate: float,
    avg_response_time: float,
    p95_response_time: float,
    p99_response_time: float
) -> WSMessage:
    """Create performance metrics message."""
    return WSMessage(
        MessageType.PERFORMANCE_METRICS,
        {
            "total_operations": total_operations,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time
        }
    )


def error_message(error: str, details: Optional[str] = None) -> WSMessage:
    """Create error message."""
    return WSMessage(
        MessageType.ERROR,
        {
            "error": error,
            "details": details
        }
    )


def process_count_message(
    hython_count: int,
    total_count: int,
    backend_count: Optional[int] = None,
    worker_count: Optional[int] = None,
) -> WSMessage:
    """Create process count message."""
    return WSMessage(
        MessageType.PROCESS_COUNT,
        {
            "hython_count": hython_count,
            "total_count": total_count,
            "backend_count": backend_count,
            "worker_count": worker_count,
        }
    )
