import bpy

obj = bpy.context.active_object

if obj.type == 'MESH':
    for mat in bpy.data.materials:
        obj.data.materials.append(mat)