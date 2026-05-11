import bpy, json
from pathlib import Path

SRC=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v005_lit_centered_refined2.blend")
OUT_BLEND=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v006_lit_centered_final.blend")
OUT_JSON=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v006_lit_centered_final_report.json")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
cam=bpy.data.objects.get('CG_Cam_Main') or scene.camera

fixes={
    361:(-0.86,-2.45,1.78,34.0),
    438:(-0.66,-2.20,1.76,35.0),
    450:(-0.66,-2.20,1.76,35.0),

    631:(-0.60,-2.25,1.88,35.0),
    654:(-0.58,-2.22,1.89,35.0),
    678:(-0.62,-2.30,1.87,35.0),
    720:(-0.59,-2.24,1.88,35.0),

    885:(-0.68,-2.30,1.84,34.0),
    900:(-0.68,-2.30,1.84,34.0),
}

for f,(x,y,z,lens) in fixes.items():
    scene.frame_set(f)
    cam.location=(x,y,z)
    cam.data.lens=lens
    cam.keyframe_insert(data_path='location',frame=f)
    cam.data.keyframe_insert(data_path='lens',frame=f)

# smooth
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

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
report={'source':str(SRC),'output_blend':str(OUT_BLEND),'fixed_frames':sorted(fixes.keys())}
OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
