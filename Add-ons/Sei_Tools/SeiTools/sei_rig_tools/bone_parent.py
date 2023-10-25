import bpy

obj = bpy.context.view_layer.objects.active
active_mode = obj.mode

if obj.type == 'ARMATURE':
    
    bpy.ops.object.mode_set(mode = 'EDIT') # Edit bones only exist in edit mode.
#    bones = bpy.context.selected_editable_bones

#    for bone in bones:
#        bone.parent = 
    bpy.ops.armature.parent_set(type='OFFSET')

    bpy.ops.object.mode_set(mode = active_mode)