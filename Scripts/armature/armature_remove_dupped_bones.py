import bpy

obj = bpy.context.active_object
active_mode = obj.mode

bpy.ops.object.mode_set(mode = 'EDIT')

# Removes dupped bones.
for bone in obj.data.edit_bones:
    if '.001' in bone.name:
        for child in bone.children_recursive:
            if child.parent == bone:
                child.parent = obj.data.edit_bones[bone.name[:-4]]
        obj.data.edit_bones.remove(bone)

bpy.ops.object.mode_set(mode = active_mode)