# Houdini MCP GUI - Quick Start

**🎯 Goal**: Get professional GUI control panel running in 5 minutes.

---

## Step 1: Install (2 minutes)

### Windows (Recommended)

Double-click `install_gui.bat` and wait for completion.

### Manual Installation

```bash
cd C:/Users/wepie/houdini-mcp
pip install -r requirements_gui.txt
```

---

## Step 2: Configure Claude Code (1 minute)

**Edit**: `C:/Users/wepie/AppData/Roaming/Claude/claude_desktop_config.json`

Change:
```json
{
  "mcpServers": {
    "houdini": {
      "command": "...",
      "args": ["-m", "houdini_mcp.server"]  ← OLD
    }
  }
}
```

To:
```json
{
  "mcpServers": {
    "houdini": {
      "command": "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe",
      "args": ["-m", "houdini_mcp.server_with_gui"],  ← NEW
      "env": {
        "HOUDINI_PATH": "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin",
        "PYTHONPATH": "C:/Users/wepie/houdini-mcp"
      }
    }
  }
}
```

**Key change**: `houdini_mcp.server` → `houdini_mcp.server_with_gui`

---

## Step 3: Restart Claude Code (1 minute)

Close and reopen Claude Code.

**⚠️ This is the ONLY time you need to restart Claude Code!**

After this, all restarts can be done from GUI.

---

## Step 4: Launch GUI (1 minute)

```bash
cd C:/Users/wepie/houdini-mcp
python run_gui.py
```

Or create a desktop shortcut:
- Right-click Desktop → New → Shortcut
- Target: `C:\Program Files\Python311\python.exe "C:\Users\wepie\houdini-mcp\run_gui.py"`
- Name: `Houdini MCP Control Panel`

---

## Step 5: Test Hot Restart

1. Open GUI (should show "● Connected")
2. Click "🔄 Restart Houdini"
3. Watch status change: Running → Restarting → Running (2 seconds)
4. Go back to Claude Code
5. **IT STILL WORKS!** No restart needed ✅

---

## 🎉 Done!

You now have:
- ✅ Real-time monitoring dashboard
- ✅ Operation history tracking
- ✅ Live log viewing
- ✅ Hot-restart capability

**No more restarting Claude Code when Houdini acts up!**

---

## 💡 Pro Tips

### Shortcut 1: Always-on Monitoring

Keep GUI open while working with Claude Code. See every operation in real-time.

### Shortcut 2: Debug Failed Operations

When operation fails:
1. Go to Operations tab
2. Find the failed operation (red ✗)
3. Check parameters and error message
4. Fix and retry

### Shortcut 3: Log Analysis

Having issues?
1. Go to Logs tab
2. Set level filter to "DEBUG"
3. Search for error messages
4. Copy logs for debugging

---

## 🆘 Troubleshooting

**Problem**: GUI shows "● Disconnected"

**Solutions**:
1. Is Claude Code running? (Start it)
2. Is MCP using GUI-enabled server? (Check config)
3. Check logs tab for errors

---

**Problem**: Can't find `claude_desktop_config.json`

**Location**: `C:/Users/[YOUR_USERNAME]/AppData/Roaming/Claude/claude_desktop_config.json`

Press `Win+R`, type: `%APPDATA%\Claude`

---

**Problem**: Import errors when running GUI

**Solution**:
```bash
pip install -r requirements_gui.txt
```

---

**Problem**: "Port 9876 already in use"

**Solutions**:
1. Close any other instance of GUI
2. Or change port in Settings tab (after connecting)

---

## 📚 More Info

- Full documentation: `README_GUI.md`
- Architecture details: `DESIGN.md`
- MCP protocol: `README.md`

---

**Questions?** Check logs or ask Master.

**Enjoy your hot-reloadable Houdini MCP!** 🚀
