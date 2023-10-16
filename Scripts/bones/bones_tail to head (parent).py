import bpy

# You need to be in edit mode.
for bone in bpy.context.selected_editable_bones:
    if bone.parent:
        bone.parent.tail.xyz = bone.head.xyz

# Edit mode check.
#if bpy.context.active_object.mode == 'EDIT'\
#    or bpy.context.active_object.mode == 'POSE':
#        bpy.ops.object.mode_set(mode = 'EDIT')