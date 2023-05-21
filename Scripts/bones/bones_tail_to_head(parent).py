import bpy

# You need to be in edit mode.
for bone in bpy.context.selected_editable_bones:
    if bone.parent:
        bone.parent.tail.xyz = bone.head.xyz