import bpy, json, math
from pathlib import Path

p=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v002_lit_centered.blend")
bpy.ops.wm.open_mainfile(filepath=str(p))
scene=bpy.context.scene
cam=bpy.data.objects.get('CG_Cam_Main') or scene.camera
focus=bpy.data.objects.get('CG_Focus')

# collect keyframes from camera location/lens
frames=set()
if cam and cam.animation_data and cam.animation_data.action:
    for fc in cam.animation_data.action.fcurves:
        if fc.data_path in ('location','rotation_euler'):
            for kp in fc.keyframe_points:
                frames.add(int(round(kp.co.x)))
if cam and cam.data.animation_data and cam.data.animation_data.action:
    for fc in cam.data.animation_data.action.fcurves:
        if fc.data_path=='lens':
            for kp in fc.keyframe_points:
                frames.add(int(round(kp.co.x)))

rows=[]
for f in sorted(frames):
    scene.frame_set(f)
    if cam and focus:
        d=(cam.matrix_world.translation-focus.matrix_world.translation).length
    else:
        d=None
    rows.append({
        'f':f,
        'loc':[round(v,3) for v in cam.location],
        'lens':round(cam.data.lens,2),
        'dist':round(d,3) if d is not None else None,
    })

print(json.dumps({'count':len(rows),'rows':rows},ensure_ascii=False))
