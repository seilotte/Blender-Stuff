'''
Create bbone with tweak bones.

Assumes:
    - Edit mode.
    - The desired bones are selected.
'''

import bpy

context = bpy.context

obj = context.object
mesh = obj.data

bone_names = [b.name for b in context.selected_editable_bones]

# Settings:
make_end = True
bbone_segments = 8
shape_tweak = bpy.data.objects.get('WGT-Diamond')
shape_bbone = bpy.data.objects.get('WGT-Arrow')

def ebone_create(ebone, prefix, length_percentage, parent, use_tail):
    new_ebone = mesh.edit_bones.new(f'{prefix}{ebone.name}')

    new_ebone.head = ebone.head
    new_ebone.tail = ebone.tail
    new_ebone.roll = ebone.roll

    if use_tail:
        new_ebone.head = ebone.tail
        new_ebone.tail = ebone.tail + ebone.vector

    new_ebone.use_connect = \
    new_ebone.use_deform = False

    new_ebone.parent = parent
    new_ebone.length = new_ebone.length * length_percentage

    return new_ebone

for bone_name in bone_names:
    ebone = mesh.edit_bones[bone_name]

    tweak     = ebone_create(ebone, 'T-', 0.25, ebone.parent, False)
    bbone     = ebone_create(ebone, 'BB-', 0.125, tweak, False)
    tweak_end = ebone_create(ebone, 'T_end-', 0.25, ebone.parent, True) if make_end else None
    bbone_end = ebone_create(ebone, 'BB_end-', 0.125, tweak_end, True) if make_end else None

    ebone.parent = tweak
    ebone.bbone_segments = bbone_segments
    ebone.bbone_handle_type_start = \
    ebone.bbone_handle_type_end = 'TANGENT'
    ebone.bbone_custom_handle_start = bbone
    ebone.bbone_custom_handle_end = bbone_end
    ebone.bbone_handle_use_ease_start = \
    ebone.bbone_handle_use_ease_end = True

bpy.ops.object.mode_set(mode='POSE')

for bone_name in bone_names:
    pbone = obj.pose.bones[bone_name]

    tweak = obj.pose.bones[f'T-{bone_name}']
    bbone = obj.pose.bones[f'BB-{bone_name}']
    tweak_end = obj.pose.bones.get(f'T_end-{bone_name}')
    bbone_end = obj.pose.bones.get(f'BB_end-{bone_name}')

    if make_end:
        constraint = pbone.constraints.new(type='STRETCH_TO')
        constraint.target = obj
        constraint.subtarget = tweak_end.name

    for index, pbone in enumerate([tweak, tweak_end, bbone, bbone_end]):
        if pbone is None: continue

        if index < 2: # Tweaks.
            bone_colour = (0.3, 0.5, 0.9) # blue
            shape = shape_tweak
        else: # Bbones.
            bone_colour = (0.3, 0.9, 0.9) # blue2
            shape = shape_bbone

            pbone.lock_location = \
            pbone.lock_rotation = (True, True, True)
            pbone.lock_rotation_w = True
            pbone.lock_scale = (True, False, True)

        pbone.custom_shape = shape

        pbone.color.palette = 'CUSTOM'
        pbone.color.custom.normal = bone_colour
        pbone.color.custom.select = (0.6, 0.9, 1.0)
        pbone.color.custom.active = (0.7, 1.0, 1.0)