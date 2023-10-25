import bpy

obj = bpy.context.view_layer.objects.active
active_mode = obj.mode

if obj.type == 'ARMATURE':
    
    bpy.ops.object.mode_set(mode = 'EDIT') # Edit bones only exist in edit mode.
    bones = bpy.context.selected_editable_bones
    
    for bone in bones:
        if bone.children:
            for child in bone.children_recursive:
                child.select = True
    
    bpy.ops.object.mode_set(mode = active_mode)