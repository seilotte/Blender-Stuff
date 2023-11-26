import bpy

def unlink_from_collections(object):
    for collection in object.users_collection:
        collection.objects.unlink(object)

obj = bpy.context.active_object
obj_name = obj.name.capitalize()

# Create collections.
col_main = bpy.data.collections.new(obj_name)

col_rigs = bpy.data.collections.new(obj_name[:3] + " Rigs")
col_mesh = bpy.data.collections.new(obj_name[:3] + " Mesh")

col_metarig = bpy.data.collections.new(obj_name[:3] + "Metarig")
col_rig = bpy.data.collections.new(obj_name[:3] + "Rig")

# Link collections.
bpy.context.scene.collection.children.link(col_main)

col_main.children.link(col_rigs)
col_main.children.link(col_mesh)

col_rigs.children.link(col_metarig)
col_rigs.children.link(col_rig)

# Add meshes to collections.
unlink_from_collections(obj)
col_mesh.objects.link(obj)

for mod in obj.modifiers:
    if mod.type != 'ARMATURE': continue
    if mod.object:
        unlink_from_collections(mod.object)
        col_metarig.objects.link(mod.object)