import bpy, json, traceback
from pathlib import Path

MODEL = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\【芙宁娜】_by_原神_dd7a8a03e7a7dfa6593053d639fa3025\【芙宁娜】.pmx")
VMD_MOTION = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\0.vmd")
OUT_BLEND = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx0vmd_v001.blend")
OUT_JSON = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx0vmd_v001_report.json")
OUT_IMG = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx0vmd_v001_preview.png")

r = {}
try:
    bpy.ops.preferences.addon_enable(module='bl_ext.blender_org.mmd_tools')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module='bl_ext.blender_org.mmd_tools')

    bpy.ops.mmd_tools.import_model(filepath=str(MODEL), scale=0.08, types={'MESH','ARMATURE','MORPHS'}, log_level='INFO')

    root = None
    arm = None
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and getattr(o, 'mmd_type', '') == 'ROOT':
            root = o
        if o.type == 'ARMATURE':
            arm = o

    if not root:
        raise RuntimeError('No MMD root found after PMX import')

    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root

    ret = bpy.ops.mmd_tools.import_vmd(
        filepath=str(VMD_MOTION),
        scale=0.08,
        bone_mapper='RENAMED_BONES',
        rename_bones=True,
        create_new_action=True,
        use_nla=False,
        update_scene_settings=True,
        detect_camera_changes=False,
        detect_light_changes=False,
        log_level='INFO',
        save_log=False,
    )

    r['import_vmd_ret'] = list(ret)
    r['actions'] = {a.name: len(a.fcurves) for a in bpy.data.actions}

    if arm and arm.animation_data and arm.animation_data.action:
        act = arm.animation_data.action
        r['arm_action'] = {
            'name': act.name,
            'fcurves': len(act.fcurves),
            'groups': [g.name for g in act.groups[:40]],
        }
    else:
        r['arm_action'] = None

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.frame_set(max(scene.frame_start, 1))
    cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
    if cams:
        scene.camera = cams[0]
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(OUT_IMG)
    bpy.ops.render.render(write_still=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    r['output_blend'] = str(OUT_BLEND)
    r['preview_image'] = str(OUT_IMG)
except Exception:
    r['error'] = traceback.format_exc()

OUT_JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(r, ensure_ascii=False))
