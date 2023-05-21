import bpy

arm = bpy.context.view_layer.objects.active

b1 = 'G_foot_tweak_R'
b2 = 'G_calf_tweak_R'

for b in bpy.context.selected_pose_bones:
    c = b.constraints.new('COPY_ROTATION')
    c.target = arm
    c.use_x = False
    c.use_y = True
    c.invert_y = True
    c.use_z = False
    c.target_space = 'CUSTOM'
    c.owner_space = 'LOCAL'
    c.space_object = arm
    
    c.subtarget = b1
    c.space_subtarget = b2