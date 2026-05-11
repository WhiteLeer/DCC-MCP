import bpy, json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view

SRC=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v003_lit_centered_noclose.blend")
OUT_BLEND=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v004_lit_centered_refined.blend")
OUT_JSON=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v004_lit_centered_refined_report.json")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
cam=bpy.data.objects.get('CG_Cam_Main') or scene.camera
focus=bpy.data.objects.get('CG_Focus')
arm=next((o for o in bpy.data.objects if o.type=='ARMATURE'),None)

if not (cam and focus and arm):
    raise RuntimeError('Missing camera/focus/armature')

# rebind focus to upper body for better framing center
sub='上半身' if '上半身' in arm.pose.bones else ('上半身2' if '上半身2' in arm.pose.bones else '首')
for c in list(focus.constraints):
    focus.constraints.remove(c)
cl=focus.constraints.new(type='COPY_LOCATION')
cl.target=arm
cl.subtarget=sub
cl.target_space='WORLD'
cl.owner_space='WORLD'
focus.location=(0.0,0.0,0.08)

# refine close shots: farther distance and milder focal length
fixes={
    360:(-0.62,-2.25,1.34,32.0),
    361:(-0.78,-2.05,1.42,38.0),
    438:(-0.58,-1.82,1.40,39.0),
    450:(-0.58,-1.82,1.40,39.0),

    631:(-0.52,-1.78,1.46,40.0),
    654:(-0.50,-1.74,1.47,40.0),
    678:(-0.54,-1.80,1.45,40.0),
    720:(-0.51,-1.76,1.46,40.0),

    811:(-0.86,-2.08,1.38,35.0),
    885:(-0.60,-1.90,1.40,37.0),
    900:(-0.60,-1.90,1.40,37.0),
}

for f,(x,y,z,lens) in fixes.items():
    scene.frame_set(f)
    cam.location=(x,y,z)
    cam.data.lens=lens
    cam.keyframe_insert(data_path='location',frame=f)
    cam.data.keyframe_insert(data_path='lens',frame=f)

# smooth curves
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

# diagnostics
check_frames=[1,90,180,270,360,450,540,630,720,810,900]
align=[]
for f in check_frames:
    scene.frame_set(f)
    pb=arm.pose.bones[sub]
    w=arm.matrix_world @ pb.matrix
    v=world_to_camera_view(scene,cam,w.translation)
    d=(cam.matrix_world.translation-focus.matrix_world.translation).length
    align.append({'f':f,'screen':[round(v.x,4),round(v.y,4)],'dist':round(d,3),'lens':round(cam.data.lens,2)})

report={
    'source':str(SRC),
    'output_blend':str(OUT_BLEND),
    'focus_bone':sub,
    'fixed_frames':sorted(fixes.keys()),
    'align_samples':align
}

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
