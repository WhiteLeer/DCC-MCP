import bpy, json, math
from pathlib import Path

SRC = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx0vmd_autofix_v003.blend")
OUT_BLEND = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v001.blend")
OUT_JSON = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v001_report.json")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 900

# Remove previous custom camera/focus if re-run
for name in ["CG_Cam_Main", "CG_Focus"]:
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)

# Create focus empty
focus = bpy.data.objects.new("CG_Focus", None)
focus.empty_display_type = 'SPHERE'
focus.empty_display_size = 0.06
bpy.context.collection.objects.link(focus)

# Create camera
cam_data = bpy.data.cameras.new("CG_Cam_Main_Data")
cam = bpy.data.objects.new("CG_Cam_Main", cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam

# Track target
con = cam.constraints.new(type='DAMPED_TRACK')
con.target = focus
con.track_axis = 'TRACK_NEGATIVE_Z'

# Add slight roll capability
cam.rotation_mode = 'XYZ'

# Helpers

def set_key(frame, cam_loc, focus_loc, lens, roll_deg=0.0):
    scene.frame_set(frame)
    cam.location = cam_loc
    focus.location = focus_loc
    cam.data.lens = lens
    cam.rotation_euler.z = math.radians(roll_deg)
    cam.keyframe_insert(data_path='location', frame=frame)
    cam.keyframe_insert(data_path='rotation_euler', frame=frame)
    cam.data.keyframe_insert(data_path='lens', frame=frame)
    focus.keyframe_insert(data_path='location', frame=frame)

# Character roughly around origin, head near z~1.30
# 10 shots x 3s => 90f each
# Each shot follows the markdown intent with one dominant movement.
shots = [
    # 1) 0-3s 全身远景: 慢推近 + 微右弧
    (1,   (-0.80, -4.10, 1.55), (0.00, -0.12, 1.00), 28, 0),
    (90,  (-0.35, -3.35, 1.45), (0.00, -0.10, 1.03), 30, 0),

    # 2) 3-6s 半身 左前45°: 轻微∞漂移
    (91,  (-1.35, -2.25, 1.45), (0.03, -0.11, 1.20), 40, 0),
    (135, (-1.15, -2.05, 1.52), (-0.02, -0.09, 1.23), 42, 0),
    (180, (-1.30, -2.00, 1.42), (0.02, -0.10, 1.18), 41, 0),

    # 3) 6-9s 全身低机位: 先稳后轻拉远
    (181, (-0.10, -2.65, 0.82), (0.00, -0.08, 0.92), 27, 0),
    (210, (-0.08, -2.65, 0.82), (0.00, -0.08, 0.92), 27, 0),
    (270, (-0.15, -3.05, 0.88), (0.00, -0.08, 0.95), 26, 0),

    # 4) 9-12s 3/4侧中景: 绕角色1/4圆弧
    (271, (-1.55, -1.95, 1.25), (0.00, -0.10, 1.12), 35, 0),
    (360, (-0.35, -1.70, 1.25), (0.00, -0.09, 1.15), 35, 0),

    # 5) 12-15s 甜感特写: 推到眼神点并稳0.4s
    (361, (-0.55, -1.25, 1.42), (0.00, -0.13, 1.28), 48, 0),
    (438, (-0.35, -0.95, 1.36), (0.00, -0.13, 1.30), 50, 0),
    (450, (-0.35, -0.95, 1.36), (0.00, -0.13, 1.30), 50, 0),

    # 6) 15-18s 全身正前: 后退跟拍 + 微升高
    (451, (-0.05, -2.55, 1.18), (0.00, -0.10, 1.02), 30, 0),
    (540, (-0.10, -3.35, 1.38), (0.00, -0.09, 1.08), 29, 0),

    # 7) 18-21s 广角大全景: 快侧移半拍再稳
    (541, (1.15, -4.25, 1.65), (0.00, -0.10, 1.00), 24, 0),
    (555, (-1.05, -4.15, 1.62), (0.00, -0.10, 1.00), 24, 0),
    (630, (-1.00, -4.10, 1.62), (0.00, -0.10, 1.00), 24, 0),

    # 8) 21-24s 面部近景: 极小手持感
    (631, (-0.28, -0.92, 1.36), (0.00, -0.14, 1.29), 52, 0.4),
    (654, (-0.26, -0.90, 1.38), (0.01, -0.13, 1.28), 52, -0.4),
    (678, (-0.30, -0.93, 1.35), (-0.01, -0.14, 1.30), 52, 0.3),
    (720, (-0.27, -0.91, 1.37), (0.00, -0.13, 1.29), 52, -0.3),

    # 9) 24-27s 全身中景: 前-侧-前短弧
    (721, (-0.10, -2.80, 1.16), (0.00, -0.10, 1.02), 31, 0),
    (765, (0.75, -2.55, 1.18), (0.00, -0.10, 1.04), 31, 0),
    (810, (-0.06, -2.70, 1.17), (0.00, -0.10, 1.03), 31, 0),

    # 10) 27-30s 中近景推近: 最后0.5s定格
    (811, (-0.65, -1.65, 1.30), (0.00, -0.12, 1.20), 39, 0),
    (885, (-0.38, -1.08, 1.32), (0.00, -0.12, 1.25), 44, 0),
    (900, (-0.38, -1.08, 1.32), (0.00, -0.12, 1.25), 44, 0),
]

for s in shots:
    set_key(*s)

# Smoother interpolation
for obj, data_paths in [(cam, {'location','rotation_euler'}), (cam.data, {'lens'}), (focus, {'location'})]:
    ad = obj.animation_data
    if not ad or not ad.action:
        continue
    for fc in ad.action.fcurves:
        if fc.data_path in data_paths:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'

report = {
    'source': str(SRC),
    'output_blend': str(OUT_BLEND),
    'camera': cam.name,
    'focus': focus.name,
    'fps': scene.render.fps,
    'frame_range': [scene.frame_start, scene.frame_end],
    'shot_key_count': len(shots),
    'camera_action': cam.animation_data.action.name if cam.animation_data and cam.animation_data.action else None,
    'focus_action': focus.animation_data.action.name if focus.animation_data and focus.animation_data.action else None,
}

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
