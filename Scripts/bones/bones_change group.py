import bpy

# Needs pose mode, and assumes the group is already created.
bone_group_name = 'Special'

bone_group = bpy.context.object.pose.bone_groups.get(bone_group_name)
if bone_group:
    for bone in bpy.context.selected_pose_bones:
        if bone.bone_group != bone_group:
            bone.bone_group = bone_group