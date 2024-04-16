import bpy

new_uv_name = 'UVBase'

for obj in bpy.context.selected_objects:
    if obj.type != 'MESH':
        continue
    if obj.data.uv_layers:
        for uv in obj.data.uv_layers:
            uv.name = new_uv_name