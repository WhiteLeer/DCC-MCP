import bpy, json
from pathlib import Path

src = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_pmx0vmd_autofix_v003.blend")
bpy.ops.wm.open_mainfile(filepath=str(src))

arm = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
info = {
  'scene_fps': bpy.context.scene.render.fps,
  'frame_range': [bpy.context.scene.frame_start, bpy.context.scene.frame_end],
  'arm_name': arm.name if arm else None,
  'arm_loc': list(arm.location) if arm else None,
  'arm_rot': list(arm.rotation_euler) if arm else None,
}
if arm:
    pb = arm.pose.bones
    for name in ['頭','head','Head','センター','首']:
        if name in pb:
            m = arm.matrix_world @ pb[name].matrix
            info[f'bone_{name}_loc'] = [m.translation.x, m.translation.y, m.translation.z]

print(json.dumps(info, ensure_ascii=False))
