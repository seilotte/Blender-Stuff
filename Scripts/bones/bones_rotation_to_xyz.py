import bpy

for bone in bpy.context.selected_pose_bones:
    bone.rotation_mode = 'XYZ'