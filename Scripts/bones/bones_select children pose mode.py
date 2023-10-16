import bpy

if bpy.context.mode == "POSE":
    bpy.ops.object.mode_set(mode = 'EDIT')
    bones = bpy.context.selected_editable_bones
    for bone in bones:
        if bone.parent is not None:
            for c in bone.children_recursive:
                c.select = True
    bpy.ops.object.mode_set(mode = 'POSE')