import bpy

obj = bpy.context.view_layer.objects.active
active_mode = obj.mode

if obj.type == 'ARMATURE':
    bpy.ops.object.mode_set(mode = 'POSE')

    bones = bpy.context.selected_pose_bones
    for bone in bones:
        if not 'Copy Rotation' in bone.constraints:
            constraint = bone.constraints.new('COPY_ROTATION')
            constraint.target = obj
#            constraint.subtarget = hand_tweak
            constraint.use_x = False
            constraint.use_y = True
            constraint.invert_y = True # Arc sys rig (fortune) gltf rolls.
            constraint.use_z = False
            constraint.target_space = 'CUSTOM'
            constraint.owner_space = 'LOCAL'
            constraint.space_object = obj
#            constraint.space_subtarget = lowarm_tweak
#            constraint.influence = infl

    bpy.ops.object.mode_set(mode = active_mode)