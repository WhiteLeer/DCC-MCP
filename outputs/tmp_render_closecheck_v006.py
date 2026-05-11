import bpy
from pathlib import Path
BLEND=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v006_lit_centered_final.blend")
OUT=Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\previews_cam30s_v006_final")
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.image_settings.file_format='PNG'
for f in [361,450,720,885]:
    scene.frame_set(f)
    scene.render.filepath=str(OUT / f"v006_f{f}.png")
    bpy.ops.render.render(write_still=True)
print(str(OUT))
