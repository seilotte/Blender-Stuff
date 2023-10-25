import bpy

vars = bpy.context.scene.sei_variables
obj = bpy.context.view_layer.objects.active # Pose mode check in operator.

def find_bone_layer(bone): # We use it in rig_type_settings().
    bone = obj.data.bones[bone.name]
    
    for i, layer in enumerate(bone.layers):
        if layer:
            return i
    return None

def rig_type_settings(
        rig_type,
        lmb_type = 'arm',
):
    # Disable layers and assign layer.
    bone_layer = find_bone_layer(bone)
    
    bone.rigify_parameters.fk_layers = [i == (bone_layer+1) for i in range(32)]
    bone.rigify_parameters.tweak_layers = [i == 7 for i in range(32)] # 7 = tweak_layer.
    bone.rigify_parameters.extra_ik_layers = [i == (bone_layer+2) for i in range(32)]
    
    bone.rigify_type = rig_type

    # Head
    bone.rigify_parameters.connect_chain = True if rig_type == 'spines.super_head' else False

    # Arms/Legs
    bone.rigify_parameters.limb_type = lmb_type
    bone.rigify_parameters.make_ik_wrist_pivot = True if lmb_type == 'arm' else False
    # Arms/Legs ik
    if rig_type == 'body_ik.arm' or rig_type == 'body_ik.leg':
        bone.rigify_parameters.ik_mid_layers_extra = True
        bone.rigify_parameters.ik_mid_layers = [i == (bone_layer+2) for i in range(32)]

    # Fingers
    if rig_type == 'limbs.super_finger':
        bone.rigify_parameters.make_extra_ik_control = True
        bone.rigify_parameters.tweak_layers = [i == (bone_layer+2) for i in range(32)]
        bone.rigify_parameters.extra_ik_layers_extra = True
        bone.rigify_parameters.extra_ik_layers = [i == (bone_layer+1) for i in range(32)]
    else:
        bone.rigify_parameters.make_extra_ik_control = False
        bone.rigify_parameters.extra_ik_layers_extra = False

    # Stretchy_chain.
    sch_bool = True if rig_type == 'skin.stretchy_chain' else False # sch = skin_stretchy_chain
    bone.rigify_parameters.skin_chain_pivot_pos = 2
    bone.rigify_parameters.skin_primary_layers_extra = sch_bool
    bone.rigify_parameters.skin_primary_layers = [i == (bone_layer-2) for i in range(32)]
    bone.rigify_parameters.skin_secondary_layers_extra = sch_bool
    bone.rigify_parameters.skin_secondary_layers = [i == (bone_layer-1) for i in range(32)]
    bone.rigify_parameters.skin_chain_falloff_twist = sch_bool
    bone.rigify_parameters.skin_chain_falloff_scale = sch_bool
    for i in range(4):
        bone.rigify_parameters.skin_chain_use_scale[i] = sch_bool

    # Basic tail.
    tail_bool = True if rig_type == 'spines.basic_tail' else False
    if tail_bool:
        bone.rigify_parameters.tweak_layers = [i == (bone_layer+1) for i in range(32)]
    for i in range(3):
        bone.rigify_parameters.copy_rotation_axes[i] = tail_bool

    # Super_copy
    if rig_type == 'basic.super_copy':
        if not bone.rigify_type or bone.rigify_type == 'basic.super_copy':
            bone.rigify_type = rig_type
            bone.rigify_parameters.make_widget = False
            
            if bone.parent is None or bone.parent.name == 'root':
                bone.rigify_parameters.relink_constraints = False
            else:
                bone.rigify_parameters.relink_constraints = True
                
                p = 'DEF-' + bone.parent.name
                bone.rigify_parameters.parent_bone = p



rigify_map = { # Used in assign_rigtype().
#    'armL': ('limbs.super_limb',),
#    'armR': ('limbs.super_limb',),
#    'legL': ('limbs.super_limb', 'leg',),
#    'legR': ('limbs.super_limb', 'leg',
    'armL': ('body_ik.arm',),
    'armR': ('body_ik.arm',),
    'legL': ('body_ik.leg',),
    'legR': ('body_ik.leg',),
    'spine': ('body_ik.blenrig_spine',),
    'head': ('spines.super_head',),
    'finger': ('limbs.super_finger',),
    'super_copy': ('basic.super_copy',),
    'chain': ('skin.stretchy_chain',),
    'tail': ('spines.basic_tail',),
#    '': (),
}

rig_type = vars.rig_types
if rig_type == ' ':
    rig_type = None
group_name = 'Rig_Type' # Bone group name.

if obj.type == 'ARMATURE':
    bones = bpy.context.selected_pose_bones

    for bone in bones:
        # Assign rig type.
        if rig_type is not None:
            rig_type_settings(* rigify_map.get(rig_type))

            # Assign the bone group.
            if rig_type != 'super_copy':
                if group_name in obj.pose.bone_groups:
                    group = obj.pose.bone_groups[group_name]
                else:
                    print(f'{obj.name}: Created {group_name} bone group.')
                    group = obj.pose.bone_groups.new(name=group_name)
                    group.color_set = 'CUSTOM'
                    group.colors.normal = (0.97, 0.26, 0.57)
                    group.colors.select = (0.6, 0.9, 1.0)
                    group.colors.active = (0.769, 1.0, 1.0)
                bone.bone_group = group