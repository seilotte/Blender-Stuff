import bpy

vg_name = 'name'

obj = bpy.context.active_object

idx = obj.vertex_groups[vg_name].index
obj.vertex_groups.active_index = idx

x = 1 + obj.vertex_groups[vg_name].index 
for i in range(len(obj.vertex_groups) - x):
    bpy.ops.object.vertex_group_move(direction='DOWN')