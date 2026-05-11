import bpy, json, math
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view

SRC = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v001.blend")
OUT_BLEND = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v002_lit_centered.blend")
OUT_JSON = Path(r"C:\Users\wepie\Desktop\MMD_Furina_Project\mmd_furina_0vmd_cam30s_cg_v002_lit_centered_report.json")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 900
scene.render.fps = 30

arm = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
if not arm:
    raise RuntimeError('No armature found')

bone_name = 'センター' if 'センター' in arm.pose.bones else arm.pose.bones[0].name

# Ensure camera and focus
cam = bpy.data.objects.get('CG_Cam_Main') or scene.camera
if cam is None:
    cam_data = bpy.data.cameras.new('CG_Cam_Main_Data')
    cam = bpy.data.objects.new('CG_Cam_Main', cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

focus = bpy.data.objects.get('CG_Focus')
if focus is None:
    focus = bpy.data.objects.new('CG_Focus', None)
    focus.empty_display_type = 'SPHERE'
    focus.empty_display_size = 0.06
    bpy.context.collection.objects.link(focus)

# Camera track constraint
for c in list(cam.constraints):
    if c.type in {'TRACK_TO','DAMPED_TRACK'}:
        cam.constraints.remove(c)
trk = cam.constraints.new(type='DAMPED_TRACK')
trk.target = focus
trk.track_axis = 'TRACK_NEGATIVE_Z'

# Focus: remove animation and bind to center bone
if focus.animation_data and focus.animation_data.action:
    act = focus.animation_data.action
    if act:
        for fc in list(act.fcurves):
            act.fcurves.remove(fc)
for c in list(focus.constraints):
    focus.constraints.remove(c)
cl = focus.constraints.new(type='COPY_LOCATION')
cl.target = arm
cl.subtarget = bone_name
cl.target_space = 'WORLD'
cl.owner_space = 'WORLD'

# Slight vertical offset so frame tends to chest/head line in close shots
focus.location = (0.0, 0.0, 0.12)

# lighting helpers

def ensure_light(name, ltype, loc, rot, color, energy):
    obj = bpy.data.objects.get(name)
    if obj and obj.type != 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        data = bpy.data.lights.new(name + '_Data', type=ltype)
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
    obj.data.type = ltype
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.color = color
    obj.data.energy = energy
    return obj

# 3-point setup
key = ensure_light('CG_Key', 'AREA', (-2.2, -2.4, 3.0), (math.radians(58), 0.0, math.radians(-28)), (1.00, 0.88, 0.78), 900)
fill = ensure_light('CG_Fill', 'AREA', (2.5, -1.8, 1.8), (math.radians(35), 0.0, math.radians(35)), (0.72, 0.83, 1.00), 320)
rim = ensure_light('CG_Rim', 'SPOT', (0.0, 2.8, 3.2), (math.radians(120), 0.0, math.radians(180)), (0.76, 0.93, 1.00), 520)

key.data.shape = 'RECTANGLE'
key.data.size = 1.8
key.data.size_y = 1.2
fill.data.shape = 'RECTANGLE'
fill.data.size = 1.6
fill.data.size_y = 1.2
rim.data.spot_size = math.radians(75)
rim.data.spot_blend = 0.35

# Animate lighting by segments
# 0-9s (1-270): stable soft
# 9-18s (271-540): key/rim slightly stronger
# 18-24s (541-720): pulse every 30f (~2 beats feeling)
# 24-30s (721-900): stable + face boost in last 0.5s

for l in [key, fill, rim]:
    if l.animation_data and l.animation_data.action:
        act=l.animation_data.action
        for fc in list(act.fcurves):
            act.fcurves.remove(fc)

# Base keys
base_keys = [
    (1,   900, 320, 520),
    (270, 900, 320, 520),
    (540, 1020, 340, 620),
    (720, 1020, 340, 620),
    (885, 950, 320, 560),
    (900, 1120, 340, 620),  # final 0.5s slight lift on face area
]
for f,ke,fe,re in base_keys:
    scene.frame_set(f)
    key.data.energy = ke; key.data.keyframe_insert(data_path='energy', frame=f)
    fill.data.energy = fe; fill.data.keyframe_insert(data_path='energy', frame=f)
    rim.data.energy = re; rim.data.keyframe_insert(data_path='energy', frame=f)

# Pulse (10-15% around segment energy) in高潮段 541..720
pulse_frames = list(range(541, 721, 30))
for i,f in enumerate(pulse_frames):
    phase = 1.12 if i % 2 == 0 else 0.90
    scene.frame_set(f)
    key.data.energy = 1020 * phase
    rim.data.energy = 620 * (1.0 + (phase-1.0)*0.9)
    fill.data.energy = 340 * (1.0 + (phase-1.0)*0.4)
    key.data.keyframe_insert(data_path='energy', frame=f)
    fill.data.keyframe_insert(data_path='energy', frame=f)
    rim.data.keyframe_insert(data_path='energy', frame=f)

# Smooth light curves
for l in [key, fill, rim]:
    ad = l.data.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'

# Optional world ambient soft tint
if scene.world:
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.045, 0.055, 0.07, 1.0)
        bg.inputs[1].default_value = 0.55

# Alignment check: project center bone over key frames
frames = [1,90,180,270,360,450,540,630,720,810,900]
align = []
max_dev = 0.0
for f in frames:
    scene.frame_set(f)
    pb = arm.pose.bones[bone_name]
    world_pos = arm.matrix_world @ pb.matrix
    v = world_to_camera_view(scene, cam, world_pos.translation)
    dx = abs(v.x - 0.5)
    dy = abs(v.y - 0.5)
    dev = (dx*dx + dy*dy) ** 0.5
    max_dev = max(max_dev, dev)
    align.append({'frame':f,'screen':[round(v.x,4), round(v.y,4)],'dev':round(dev,4)})

report = {
    'source': str(SRC),
    'output_blend': str(OUT_BLEND),
    'center_bone': bone_name,
    'camera': cam.name,
    'focus': focus.name,
    'lights': ['CG_Key','CG_Fill','CG_Rim'],
    'frame_range': [scene.frame_start, scene.frame_end],
    'alignment_samples': align,
    'max_center_deviation': round(max_dev,4)
}

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
