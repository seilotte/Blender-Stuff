import bpy

obj = bpy.context.active_object

list_normals = []
for vec in obj.data.attributes['Normals'].data:
    list_normals.append(vec.vector)

obj.data.normals_split_custom_set(list_normals)