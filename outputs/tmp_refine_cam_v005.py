import bpy, json
from pathlib import Path

SRC=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v004_lit_centered_refined.blend")
OUT_BLEND=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v005_lit_centered_refined2.blend")
OUT_JSON=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v005_lit_centered_refined2_report.json")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
cam=bpy.data.objects.get('CG_Cam_Main') or scene.camera
focus=bpy.data.objects.get('CG_Focus')

# close-shot height + pullback adjustments
fixes={
    361:(-0.82,-2.35,1.68,36.0),
    438:(-0.62,-2.08,1.66,37.0),
    450:(-0.62,-2.08,1.66,37.0),

    631:(-0.56,-2.05,1.72,38.0),
    654:(-0.54,-2.00,1.73,38.0),
    678:(-0.58,-2.08,1.71,38.0),
    720:(-0.55,-2.02,1.72,38.0),

    885:(-0.64,-2.12,1.68,36.0),
    900:(-0.64,-2.12,1.68,36.0),
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

rows=[]
for f in sorted(fixes.keys()):
    scene.frame_set(f)
    d=(cam.matrix_world.translation-focus.matrix_world.translation).length if focus else None
    rows.append({'f':f,'loc':[round(v,3) for v in cam.location],'lens':round(cam.data.lens,2),'dist':round(d,3) if d else None})

report={'source':str(SRC),'output_blend':str(OUT_BLEND),'rows':rows}

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
