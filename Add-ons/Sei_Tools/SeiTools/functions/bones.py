import bpy

def bone_select_children(context):
    obj = context.active_object # TODO: check for context.active_bone only?
    active_mode = obj.mode

    if obj.type == 'ARMATURE':
        bpy.ops.object.mode_set(mode = 'EDIT')
        for bone in bpy.context.selected_editable_bones:
            if bone.children:
                for child in bone.children_recursive:
                    child.select = True
        bpy.ops.object.mode_set(mode = active_mode)

def bone_parent_offset(context):
    obj = context.active_object
    active_mode = obj.mode

    if obj.type == 'ARMATURE':
        bpy.ops.object.mode_set(mode='EDIT') # Edit bones only exist in edit mode.
        bpy.ops.armature.parent_set(type='OFFSET')
        bpy.ops.object.mode_set(mode=active_mode)

def bone_tail_to_head_parent(context):
    obj = context.active_object
    active_mode = obj.mode

    if obj.type == 'ARMATURE':
        bpy.ops.object.mode_set(mode = 'EDIT')
        for bone in bpy.context.selected_editable_bones:
            if bone.parent:
                bone.parent.tail = bone.head
        bpy.ops.object.mode_set(mode = active_mode)