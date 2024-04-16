import bpy

''' Align bone_shape_transforms of bone(x) to bone(y).
    Assumes the bone shape is at (0, 0, 0) and it is aligned to the Y world axis'''

context = bpy.context
obj = context.object

x = obj.pose.bones[0] if context.mode == 'POSE' else obj.data.edit_bones[0]
y = obj.pose.bones[1] if context.mode == 'POSE' else obj.data.edit_bones[1]

s, t, r = (1,1,1), (0,0,0), (0,0,0)

# [POSE MODE] Version.
if context.mode == 'POSE':

    xx = x.bone
    yy = y.bone

    #t = x.matrix.inverted() @ y.bone.head_local # Same as below.
    t = xx.matrix_local.inverted() @ yy.head_local
    r = (xx.matrix_local.inverted() @ yy.matrix_local).to_euler()
    s = tuple(yy.vector.length / xx.vector.length for _ in range(3))

    x.custom_shape_scale_xyz      = s # (s, s, s)
    x.custom_shape_translation    = t
    x.custom_shape_rotation_euler = r

# [EDIT MODE] Version.
else:

    t = x.matrix.inverted() @ y.head
    r = (x.matrix.inverted() @ y.matrix).to_euler()
    s = tuple(y.length / x.length for _ in range(3))

#    t = x.matrix.inverted() @ (y.head + (y.vector * 0.5)) # Add in bone dir..

    bpy.ops.object.mode_set(mode='POSE')

    x = obj.pose.bones[0]

    x.custom_shape_scale_xyz      = s
    x.custom_shape_translation    = t
    x.custom_shape_rotation_euler = r