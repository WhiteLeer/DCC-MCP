# Blender MCP Setup

## 1) Blender 路径

默认读取环境变量 `BLENDER_EXE`，当前建议值：

`D:\常用软件\Blender 4.2\blender.exe`

你也可以在启动前设置：

```powershell
$env:BLENDER_EXE="D:\常用软件\Blender 4.2\blender.exe"
```

## 2) 启动 GUI

```powershell
python run_blender_gui.py
```

或双击：

`启动BlenderGUI.bat`

## 3) 可用 MCP 工具（当前）

- `get_scene_state`
- `create_cube`
- `clean_scene`
- `import_geometry`
- `export_fbx`
- `decimate_mesh`
- `triangulate_mesh`
- `recalculate_normals`
- `shade_smooth`
- `merge_by_distance`

说明：当前是“高稳定后台模式”（`--background`），适合自动化流水线。  
每个工具可通过 `input_blend` / `output_blend` 串联成流程。
