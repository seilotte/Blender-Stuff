import bpy

# I don't know, probably the one inside AswTools is better.

#sei_vars = bpy.context.scene.sei_variables
#sei_vars.to_armature
#aaa = bpy.data.objects["jko_body"]
a = bpy.context.active_object # a = armature

# Make all bones euler rotation.
for bone in a.pose.bones:
    bone.rotation_mode = 'XYZ'

def change_bone_group(bone_names, group_name):
    for b in a.data.bones:
        if b.name in bone_names:
            if group_name in a.pose.bone_groups:
                group = a.pose.bone_groups[group_name]
            else:
                group = a.pose.bone_groups.new(name=group_name)
                group.color_set = 'CUSTOM'
                group.colors.normal = (0.97, 0.26, 0.57)
                group.colors.select = (0.596, .898, 1.0)
                group.colors.active = (.769, 1.0, 1.0)
            a.pose.bones[b.name].bone_group = group

def move_bone_layer(bone_names, tolayer):
    for b in a.data.bones:
        if b.name in bone_names:
            if b is not None:
                b.layers[tolayer] = True
                b.layers = [layer == tolayer for layer in range(32)] # Disable if you want it to add a bone_layer.

def add_bone_layer(bone_names, tolayer):
    for b in a.data.bones:
        if b.name in bone_names:
            if b is not None:
                b.layers[tolayer] = True

# bl = bone_list
# Bone groups (colours).
bl = ["chest","G_chest", "hips", "G_hand_ik_wrist_L", "G_hand_ik_wrist_R", "G_foot_heel_ik_L", "G_foot_heel_ik_R"]
change_bone_group(bl, "Tweak2")

bl2 = ["G_chest_ik_end", "G_chest_ik", "G_stomach_ik", "G_waist_ik"]
change_bone_group(bl2, "Tweak")

bl3 = ["G_shoulder_L", "G_shoulder_R"]
change_bone_group(bl3, "Special")
bl6 = ["G_toe_L", "G_toe_R", "G_clavicle_L", "G_clavicle_R"]
change_bone_group(bl6, "Special")

bl7 = ["VIS_G_thigh_ik_pole_L", "VIS_G_thigh_ik_pole_R",  "VIS_G_uparm_ik_pole_L", "VIS_G_uparm_ik_pole_R"]
change_bone_group(bl7, "Extreme Deform")


# Bone layers.
move_bone_layer(bl3, 5) # 5 is torso ik.
add_bone_layer(bl3, 6) # 6 is torso fk.

bl4 = ["head", "neck"]
add_bone_layer(bl4, 6)

bl5 = ["G_clavicle_L", "G_clavicle_R", "G_uparm_ik_L", "G_uparm_parent_L", "G_uparm_ik_R", "G_uparm_parent_R", "G_foot_spin_ik_L", "G_foot_spin_ik_R", "G_thigh_ik_L", "G_thigh_ik_R", "G_thigh_parent_L", "G_thigh_parent_R"]
move_bone_layer(bl5, 27) # 26 is extra, 27 is extreme deform, 28 is root.

bl_GB_torso = [
"torso", "hips", "neck", "head",
"chest", "G_chest",
"G_shoulder_L", "G_shoulder_R",
]
add_bone_layer(bl_GB_torso, 26)

# ===========================

# Enable pole_vectors.
bl_vector = ["G_uparm_parent_L", "G_uparm_parent_R", "G_thigh_parent_L", "G_thigh_parent_R"]
for i in bl_vector:
    bpy.context.object.pose.bones[i]["pole_vector"] = 1

# ===========================

# Add twist bones.
def set_twist_bones(list, rig, bone_target, space_bone_target):

    for c in range(len(list)):
        def_list = "DEF-"+list[c][0]
        for bone in a.pose.bones:
            if bone.name in def_list:
                rct = bone.contraints.new('COPY_ROTATION')
                # Rotation bone constraint settings.
                rct.target = bpy.data.objects.get(rig)
                rct.subtarget = bone_target
                rct.use_x = False
                rct.use_z = False
                rct.target_space = 'CUSTOM'
                rct.owner_space = 'LOCAL'
                rct.space_object = bpy.data.objects.get(rig)
                rct.space_subtarget = space_bone_target
                rct.influence = list[c][1]
                

# bt = bones_twist
bt_list_armL = [["G_wrist_L", 0.9], ["G_lowarmlow_L", 0.8], ["G_lowarmmid_L", 0.5], ["G_lowarmup_L", 0.25]]
set_twist_bones(bt_list_armL, "RIG-jko", "G_hand_tweak_L", "MCH-G_lowarm_tweak_L")

bt_list_armR = [["G_wrist_R", 0.9], ["G_lowarmlow_R", 0.8], ["G_lowarmmid_R", 0.5], ["G_lowarmup_R", 0.25]]
set_twist_bones(bt_list_armR, "RIG-jko", "G_hand_tweak_R", "MCH-G_lowarm_tweak_R")

bt_list_legL = [["G_calflow_L", 0.8], ["G_calfmid_L", 0.4], ["G_calfup_L", 0.2]]
set_twist_bones(bt_list_legL, "RIG-jko", "G_foot_tweak_L", "MCH-G_calf_tweak_L")

bt_list_legR = [["G_calflow_R", 0.8], ["G_calfmid_R", 0.4], ["G_calfup_R", 0.2]]
set_twist_bones(bt_list_legR, "RIG-jko", "G_foot_tweak_R", "MCH-G_calf_tweak_R")

# ===========================


def super_copy_fix(layer, group_name):
    list = []
    # Append bone names based on the layer.
    for bone in a.data.bones:
        if bone.layers[layer]:
            list.append(bone.name)
    
    for b in a.pose.bones:
        if b.name in list:
#            group = a.pose.bone_groups[group_name]
#            a.pose.bones[b.name].bone_group = group
            a.pose.bones[b.name].bone_group = None
shape = bpy.data.objects["WGT-RIG-jko_G_shoulder_L"]
            a.pose.bones[b.name].custom_shape = None

super_copy_fix(0, "Special")