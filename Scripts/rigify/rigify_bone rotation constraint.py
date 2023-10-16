import bpy

arm = bpy.context.view_layer.objects.active

bone1 = 'G_foot_tweak_R'
bone2 = 'G_calf_tweak_R'

for bone in bpy.context.selected_pose_bones:
    c = bone.constraints.new('COPY_ROTATION')
    c.target = arm
    c.use_x = False
    c.use_y = True
    c.invert_y = True # Bone roll dependant.
    c.use_z = False
    c.target_space = 'CUSTOM'
    c.owner_space = 'LOCAL'
    c.space_object = arm
    
    c.subtarget = bone1
    c.space_subtarget = bone2