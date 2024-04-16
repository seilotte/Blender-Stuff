import bpy

for obj in bpy.context.selected_objects:
    if obj.type != 'MESH':
        continue

    for shape_key in obj.data.shape_keys.key_blocks:
        obj.shape_key_remove(shape_key)