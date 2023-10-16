import bpy
from mathutils import Vector

obj = bpy.context.view_layer.objects.active
#active_mode = obj.mode

rig_name = 'WGT-RIG-jko_body_'
wgt_shape = bpy.data.objects['WGT-circle']
condition = 'G'

#WGT-RIG-jko_body_tweak_G_waist // widget name
#tweak_G_waist // bone name

def swap(vector):
    # on x axis y > x
    # on y axis y > z Don't swap.
    swap = vector.y
    vector.y = vector.z
    vector.z = swap
    
    vector.x *= 0
    vector.z *= 0
    vector.y *= -1
    return vector.xyz

bpy.ops.object.mode_set(mode='EDIT')

for bone in bpy.context.selected_editable_bones:
    bone_length = bone.length

    bone = obj.pose.bones[bone.name] # pose bone
    # Change shape.
    if condition in bone.name:
        bone.custom_shape = wgt_shape

        wgt_name = rig_name + bone.name
        org_wgt = bpy.data.objects[wgt_name]

        # Calculate offset.
        center = Vector()
        for v in org_wgt.data.vertices:
            center += org_wgt.matrix_world @ v.co
        center /= len(org_wgt.data.vertices)

        offset = org_wgt.location - center
        org_wgt_offset = swap(offset)
#        org_wgt_offset = offset
        
        # Calculate scale.
#        scale_factor = offset.length / org_wgt.scale[0] # offset = distance
        scale_factor = bone_length / (sum(org_wgt.scale) / 3.0)


        # Custom shape properties.
        bone.custom_shape_scale_xyz *= bone_length / org_wgt.scale[0]
        bone.custom_shape_translation = org_wgt_offset
#        bone.custom_shape_rotation_euler = org_wgt.rotation_euler

#        if 'R' in bone.name:
#            for i in range(3):
#                bone.custom_shape_scale_xyz[i] *= -1

bpy.ops.object.mode_set(mode='POSE')