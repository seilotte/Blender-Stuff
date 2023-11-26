import bpy

obj_types_list = ['MESH', 'ARMATURE', 'LIGHT', 'CAMERA',]

for obj in bpy.data.objects:
    if obj.type in obj_types_list:
        obj.data.name = obj.name