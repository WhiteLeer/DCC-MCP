import bpy, json
from pathlib import Path

SRC=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v002_lit_centered.blend")
OUT_BLEND=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v003_lit_centered_noclose.blend")
OUT_JSON=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v003_lit_centered_noclose_report.json")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
cam=bpy.data.objects.get('CG_Cam_Main') or scene.camera
focus=bpy.data.objects.get('CG_Focus')

# Targeted fixes for over-close shots (keep same shot language, reduce aggression)
# frame: (x,y,z,lens)
fixes={
    360:(-0.48,-2.05,1.28,33.0),
    361:(-0.62,-1.75,1.40,42.0),
    438:(-0.42,-1.45,1.38,44.0),
    450:(-0.42,-1.45,1.38,44.0),

    631:(-0.34,-1.32,1.40,46.0),
    654:(-0.32,-1.28,1.41,46.0),
    678:(-0.36,-1.34,1.39,46.0),
    720:(-0.33,-1.30,1.40,46.0),

    811:(-0.72,-1.95,1.32,37.0),
    885:(-0.45,-1.58,1.34,40.0),
    900:(-0.45,-1.58,1.34,40.0),
}

for f,(x,y,z,lens) in fixes.items():
    scene.frame_set(f)
    cam.location=(x,y,z)
    cam.data.lens=lens
    cam.keyframe_insert(data_path='location',frame=f)
    cam.data.keyframe_insert(data_path='lens',frame=f)

# smooth handles
if cam.animation_data and cam.animation_data.action:
    for fc in cam.animation_data.action.fcurves:
        if fc.data_path=='location':
            for kp in fc.keyframe_points:
                kp.interpolation='BEZIER'
                kp.handle_left_type='AUTO_CLAMPED'
                kp.handle_right_type='AUTO_CLAMPED'
if cam.data.animation_data and cam.data.animation_data.action:
    for fc in cam.data.animation_data.action.fcurves:
        if fc.data_path=='lens':
            for kp in fc.keyframe_points:
                kp.interpolation='BEZIER'
                kp.handle_left_type='AUTO_CLAMPED'
                kp.handle_right_type='AUTO_CLAMPED'

# measure distances at keyframes
frames=sorted(set(fixes.keys()))
rows=[]
min_d=999
for f in frames:
    scene.frame_set(f)
    d=(cam.matrix_world.translation-focus.matrix_world.translation).length if focus else None
    if d is not None:
        min_d=min(min_d,d)
    rows.append({'f':f,'loc':[round(v,3) for v in cam.location],'lens':round(cam.data.lens,2),'dist':round(d,3) if d else None})

report={
    'source':str(SRC),
    'output_blend':str(OUT_BLEND),
    'fixed_frames':frames,
    'min_distance_after_fix': round(min_d,3) if min_d<999 else None,
    'rows':rows,
}

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
