import bpy, json, traceback
from pathlib import Path

MODEL = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\【芙宁娜】_by_原神_dd7a8a03e7a7dfa6593053d639fa3025\【芙宁娜】.pmx")
VMD = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\1.vmd")
OUT_BLEND = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx1vmd_autofix_v002.blend")
OUT_JSON = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx1vmd_autofix_v002_report.json")

r = {"model": str(MODEL), "vmd": str(VMD)}

try:
    bpy.ops.preferences.addon_enable(module='bl_ext.blender_org.mmd_tools')
    from bl_ext.blender_org.mmd_tools.core.vmd import File as VMDFile
    from bl_ext.blender_org.mmd_tools.core.vmd.importer import VMDImporter, RenamedBoneMapper

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module='bl_ext.blender_org.mmd_tools')

    vf = VMDFile()
    vf.load(filepath=str(VMD))

    model_name = getattr(vf, 'modelName', None)
    counts = {
        'bone': len(getattr(vf, 'boneAnimation', []) or []),
        'shape': len(getattr(vf, 'shapeKeyAnimation', []) or []),
        'camera': len(getattr(vf, 'cameraAnimation', []) or []),
        'lamp': len(getattr(vf, 'lampAnimation', []) or []),
        'self_shadow': len(getattr(vf, 'selfShadowAnimation', []) or []),
        'property': len(getattr(vf, 'propertyAnimation', []) or []),
    }
    r['vmd_model_name'] = model_name
    r['vmd_counts'] = counts

    bpy.ops.mmd_tools.import_model(filepath=str(MODEL), scale=0.08, types={'MESH','ARMATURE','MORPHS'}, log_level='INFO')

    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    root = next((o for o in bpy.data.objects if o.type == 'EMPTY' and getattr(o, 'mmd_type', '') == 'ROOT'), None)
    r['armature'] = arm.name if arm else None
    r['root'] = root.name if root else None

    if not arm:
        raise RuntimeError('No armature found after PMX import')

    mode = 'camera_only' if counts['bone'] == 0 and counts['camera'] > 0 else 'bone_or_mixed'
    r['detected_mode'] = mode

    if mode == 'bone_or_mixed':
        importer = VMDImporter(
            filepath=str(VMD),
            scale=0.08,
            bone_mapper=(lambda arm_obj: RenamedBoneMapper(rename_LR_bones=True, use_underscore=False).init(arm_obj)),
            use_pose_mode=False,
            convert_mmd_camera=(counts['camera'] > 0),
            convert_mmd_light=(counts['lamp'] > 0),
            frame_margin=0,
            use_mirror=False,
            use_nla=False,
            detect_camera_changes=(counts['camera'] > 0),
            detect_light_changes=(counts['lamp'] > 0),
        )
        importer.assign(arm, action_name='vmd1_auto_bone')

    cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
    if not cams:
        bpy.ops.object.camera_add(location=(0, -3.2, 1.45), rotation=(1.23, 0.0, 0.0))
        cams = [bpy.context.active_object]

    cam_target = cams[0]
    if counts['camera'] > 0:
        cam_importer = VMDImporter(
            filepath=str(VMD),
            scale=0.08,
            bone_mapper=None,
            use_pose_mode=False,
            convert_mmd_camera=True,
            convert_mmd_light=(counts['lamp'] > 0),
            frame_margin=0,
            use_mirror=False,
            use_nla=False,
            detect_camera_changes=True,
            detect_light_changes=(counts['lamp'] > 0),
        )
        cam_importer.assign(cam_target, action_name='vmd1_auto_camera')

    scene = bpy.context.scene
    scene.camera = cam_target
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.fps = 30

    # auto frame range by existing keyframes
    minf, maxf = 999999, -999999
    for a in bpy.data.actions:
        for fc in a.fcurves:
            for kp in fc.keyframe_points:
                f = int(round(kp.co.x))
                minf = min(minf, f)
                maxf = max(maxf, f)
    if maxf >= minf:
        scene.frame_start = max(1, minf)
        scene.frame_end = maxf
    else:
        scene.frame_start = 1
        scene.frame_end = 120

    arm_action = None
    if arm.animation_data and arm.animation_data.action:
        a = arm.animation_data.action
        arm_action = {
            'name': a.name,
            'fcurves': len(a.fcurves),
            'groups': len(a.groups),
            'keyframes': sum(len(fc.keyframe_points) for fc in a.fcurves),
        }
    r['arm_action'] = arm_action

    camera_actions = []
    for c in bpy.data.objects:
        if c.type == 'CAMERA' and c.animation_data and c.animation_data.action:
            a = c.animation_data.action
            camera_actions.append({
                'camera': c.name,
                'action': a.name,
                'fcurves': len(a.fcurves),
                'keyframes': sum(len(fc.keyframe_points) for fc in a.fcurves),
            })
    r['camera_actions'] = camera_actions
    r['frame_range'] = [scene.frame_start, scene.frame_end]

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    r['output_blend'] = str(OUT_BLEND)

except Exception:
    r['error'] = traceback.format_exc()

OUT_JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(r, ensure_ascii=False))
