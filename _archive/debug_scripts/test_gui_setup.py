"""Test GUI setup and dependencies."""

import sys
import os

def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    errors = []

    # Test PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        print("  ✓ PyQt6")
    except ImportError as e:
        errors.append(f"  ✗ PyQt6: {e}")

    # Test qasync
    try:
        import qasync
        print("  ✓ qasync")
    except ImportError as e:
        errors.append(f"  ✗ qasync: {e}")

    # Test websockets
    try:
        import websockets
        print("  ✓ websockets")
    except ImportError as e:
        errors.append(f"  ✗ websockets: {e}")

    # Test psutil
    try:
        import psutil
        print("  ✓ psutil")
    except ImportError as e:
        errors.append(f"  ✗ psutil: {e}")

    # Test MCP
    try:
        from mcp.server.fastmcp import FastMCP
        print("  ✓ mcp (FastMCP)")
    except ImportError as e:
        errors.append(f"  ✗ mcp: {e}")

    return errors


def test_gui_modules():
    """Test GUI modules."""
    print("\nTesting GUI modules...")

    errors = []

    try:
        from houdini_mcp.gui.main_window import MainWindow
        print("  ✓ main_window")
    except Exception as e:
        errors.append(f"  ✗ main_window: {e}")

    try:
        from houdini_mcp.gui.widgets.dashboard_widget import DashboardWidget
        print("  ✓ dashboard_widget")
    except Exception as e:
        errors.append(f"  ✗ dashboard_widget: {e}")

    try:
        from houdini_mcp.gui.widgets.operations_widget import OperationsWidget
        print("  ✓ operations_widget")
    except Exception as e:
        errors.append(f"  ✗ operations_widget: {e}")

    try:
        from houdini_mcp.gui.widgets.logs_widget import LogsWidget
        print("  ✓ logs_widget")
    except Exception as e:
        errors.append(f"  ✗ logs_widget: {e}")

    try:
        from houdini_mcp.gui.widgets.settings_widget import SettingsWidget
        print("  ✓ settings_widget")
    except Exception as e:
        errors.append(f"  ✗ settings_widget: {e}")

    return errors


def test_server_modules():
    """Test server modules."""
    print("\nTesting server modules...")

    errors = []

    try:
        from houdini_mcp.websocket_protocol import WSMessage, MessageType
        print("  ✓ websocket_protocol")
    except Exception as e:
        errors.append(f"  ✗ websocket_protocol: {e}")

    try:
        from houdini_mcp.connection_manager import HoudiniConnectionManager
        print("  ✓ connection_manager")
    except Exception as e:
        errors.append(f"  ✗ connection_manager: {e}")

    try:
        from houdini_mcp.websocket_server import WebSocketControlServer
        print("  ✓ websocket_server")
    except Exception as e:
        errors.append(f"  ✗ websocket_server: {e}")

    try:
        from houdini_mcp.server_with_gui import create_server_with_gui
        print("  ✓ server_with_gui")
    except Exception as e:
        errors.append(f"  ✗ server_with_gui: {e}")

    return errors


def test_file_structure():
    """Test file structure."""
    print("\nTesting file structure...")

    required_files = [
        "requirements_gui.txt",
        "run_gui.py",
        "houdini_mcp/gui/__init__.py",
        "houdini_mcp/gui/app.py",
        "houdini_mcp/gui/main_window.py",
        "houdini_mcp/gui/widgets/__init__.py",
        "houdini_mcp/gui/widgets/dashboard_widget.py",
        "houdini_mcp/gui/widgets/operations_widget.py",
        "houdini_mcp/gui/widgets/logs_widget.py",
        "houdini_mcp/gui/widgets/settings_widget.py",
        "houdini_mcp/websocket_protocol.py",
        "houdini_mcp/connection_manager.py",
        "houdini_mcp/websocket_server.py",
        "houdini_mcp/server_with_gui.py",
    ]

    errors = []
    base_dir = os.path.dirname(__file__)

    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"  ✓ {file_path}")
        else:
            errors.append(f"  ✗ Missing: {file_path}")

    return errors


def main():
    """Run all tests."""
    print("=" * 60)
    print("Houdini MCP GUI - Setup Test")
    print("=" * 60)

    all_errors = []

    # Test imports
    errors = test_imports()
    all_errors.extend(errors)

    # Test GUI modules
    errors = test_gui_modules()
    all_errors.extend(errors)

    # Test server modules
    errors = test_server_modules()
    all_errors.extend(errors)

    # Test file structure
    errors = test_file_structure()
    all_errors.extend(errors)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if not all_errors:
        print("✅ All tests passed!")
        print("\nYou can now:")
        print("  1. Run: python run_gui.py")
        print("  2. Or install: install_gui.bat")
        return 0
    else:
        print(f"❌ {len(all_errors)} error(s) found:\n")
        for error in all_errors:
            print(error)
        print("\nPlease fix errors and run test again.")
        print("\nTo install dependencies:")
        print("  pip install -r requirements_gui.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
