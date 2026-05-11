import bpy, json
fbx = r'C:\Users\wepie\Desktop\crystal_hq_500\crystal_hq_664_bin.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True)
ret = bpy.ops.import_scene.fbx(filepath=fbx)
meshes=[]
for o in bpy.data.objects:
    if o.type=='MESH':
        meshes.append({'name':o.name,'uv_layers':len(o.data.uv_layers),'polys':len(o.data.polygons)})
print(json.dumps({'ret':list(ret),'meshes':meshes},ensure_ascii=False))
