import bpy

obj = bpy.context.view_layer.objects.active
active_mode = obj.mode

bpy.ops.object.mode_set(mode = 'EDIT')
#for bone in obj.data.edit_bones:
for bone in bpy.context.selected_editable_bones:
    bone.select = False
    if '_def' in bone.name:
        bone.select = True
bpy.ops.object.mode_set(mode = active_mode)