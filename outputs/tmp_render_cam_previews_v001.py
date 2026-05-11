import bpy
from pathlib import Path

BLEND = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v001.blend")
OUT_DIR = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\previews_cam30s_v001")
OUT_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

frames = [1, 135, 270, 450, 630, 720, 900]
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = str(OUT_DIR / f"cam30s_f{f}.png")
    bpy.ops.render.render(write_still=True)

print('done', str(OUT_DIR))
