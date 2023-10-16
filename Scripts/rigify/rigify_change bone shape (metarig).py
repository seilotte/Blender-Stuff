import bpy

for bone in bpy.context.selected_pose_bones:
    bone.rigify_parameters.make_widget = True
    bone.rigify_parameters.super_copy_widget_type = 'diamond'