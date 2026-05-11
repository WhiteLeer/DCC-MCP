import bpy, json
from pathlib import Path
p=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v001.blend")
bpy.ops.wm.open_mainfile(filepath=str(p))
scene=bpy.context.scene
cam=scene.camera
arm=next((o for o in bpy.data.objects if o.type=='ARMATURE'),None)
out={
 'camera': cam.name if cam else None,
 'camera_constraints':[c.type for c in cam.constraints] if cam else [],
 'focus_exists': bpy.data.objects.get('CG_Focus') is not None,
 'lights':[(o.name,o.type) for o in bpy.data.objects if o.type=='LIGHT'],
 'arm':arm.name if arm else None,
 'arm_bones_sample':[]
}
if arm:
 out['arm_bones_sample']=list(arm.pose.bones.keys())[:30]
print(json.dumps(out,ensure_ascii=False))
