import bpy
from array import array

# I don't know, probably the one inside AswTools is better.

#sei_vars = bpy.context.scene.sei_variables
#sei_vars.to_armature
a = bpy.context.active_object # a = armature

def change_bone_group(bone_names, group_name):
    if a.type == 'ARMATURE':
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
    if a.type == 'ARMATURE':
        for b in a.data.bones:
            if b.name in bone_names:
                if b is not None:
                    b.layers[tolayer] = True
                    b.layers = [layer == tolayer for layer in range(32)] # Disable if you want it to add a bone_layer.

def add_bone_layer(bone_names, tolayer):
    if a.type == 'ARMATURE':
        for b in a.data.bones:
            if b.name in bone_names:
                if b is not None:
                    b.layers[tolayer] = True

# ===========================

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

## Add twist bones.
#def set_twist_bones(list_tbones, rig, bone_target, space_bone_target):

#    def twist_rotation_constraint(rig, influ, bone_target, space_bone_target):
#        rct = b.constraints.new('COPY_ROTATION') # rct = rotation constraint
#        rct.target = bpy.data.objects.get(rig)
#        rct.subtarget = bone_target
#        rct.use_x = False
#        rct.use_z = False
#        rct.target_space = 'CUSTOM'
#        rct.owner_space = 'LOCAL'
#        rct.space_object = bpy.data.objects.get(rig)
#        rct.space_subtarget = space_bone_target
#        rct.influence = influ

#    if a.type == 'ARMATURE':
#        for i in range(len(list_tbones)):
#            org_list_tbones = "ORG-"+list_tbones[i][0]
#            move_bone_layer(org_list_tbones, 28) # 29 is DEF layer.

#            # Enable deform on bones.
#            for c in a.data.bones:
#                if c.name in org_list_tbones:
#                    c.use_deform = True

#            for b in a.pose.bones:
#                if b.name in org_list_tbones:
#                    # Enable rotation.
#                    b.rotation_mode = 'XYZ'
##                    for n in range(3):
##                        b.lock_location[n] = False
##                        b.lock_rotation[n] = False
##                        b.lock_scale[n] = False
##                    b.lock_rotation[1] = False
#                    twist_rotation_constraint(rig, list_tbones[i][1], bone_target, space_bone_target)
#                    # Rename from "ORG-" to "DEF-".
#                    b.name = b.name[4:]
#                    b.name = "DEF-"+b.name

## bt = bones_twist
#bt_list_armL = [["G_wrist_L", 0.9], ["G_lowarmlow_L", 0.8], ["G_lowarmmid_L", 0.5], ["G_lowarmup_L", 0.25]]
#set_twist_bones(bt_list_armL, "RIG-jko", "G_hand_tweak_L", "MCH-G_lowarm_tweak_L")

#bt_list_armR = [["G_wrist_R", 0.9], ["G_lowarmlow_R", 0.8], ["G_lowarmmid_R", 0.5], ["G_lowarmup_R", 0.25]]
#set_twist_bones(bt_list_armR, "RIG-jko", "G_hand_tweak_R", "MCH-G_lowarm_tweak_R")

#bt_list_legL = [["G_calflow_L", 0.8], ["G_calfmid_L", 0.4], ["G_calfup_L", 0.2]]
#set_twist_bones(bt_list_legL, "RIG-jko", "G_foot_tweak_L", "MCH-G_calf_tweak_L")

#bt_list_legR = [["G_calflow_R", 0.8], ["G_calfmid_R", 0.4], ["G_calfup_R", 0.2]]
#set_twist_bones(bt_list_legR, "RIG-jko", "G_foot_tweak_R", "MCH-G_calf_tweak_R")

# ===========================

# Super_copy alternative, using original bones.
def remove_locks(rig, list):
    a = bpy.data.objects.get(rig)
    if a.type == 'ARMATURE':
        for b in a.pose.bones:
            if b.name in list:
                b.rotation_mode = 'XYZ'
                for n in range(3):
                    b.lock_location[n] = False
                    b.lock_rotation[n] = False
                    b.lock_scale[n] = False

def swap_to_ORG(metarig, rig, mesh, layer):
    a = bpy.data.objects.get(metarig)
    deflist = []
    orglist = []

    # Append bone names based on the layer.
    if a.type == 'ARMATURE':
        for b in a.data.bones:
            if b.layers[layer]:
                deflist.append("DEF-"+b.name)
                orglist.append("ORG-"+b.name)

    # Add "ORG-" instead of "DEF-" to vertex groups mesh.
    c = bpy.data.objects.get(mesh)
    if c.type == 'MESH':
        for i in c.vertex_groups:
            if i.name in deflist:
                str = i.name[4:]
                i.name = "ORG-"+str

    # Enable use deform on ORG-bones.
    a2 = bpy.data.objects.get(rig)
    if a2.type == 'ARMATURE':
        for d in a2.data.bones:
            if d.name in orglist:
                d.use_deform = True
    
#    move_bone_layer(orglist, layer)
#    remove_locks(rig, orglist)
                

swap_to_ORG("jko_body", "RIG-jko", "jko_body.001", 0) # Head
#swap_to_ORG("jko_body", "RIG-jko", "jko_body.001", 23) # Clothes
#swap_to_ORG("jko_body", "RIG-jko", "jko_body.001", 24) # Clothes [Secondary]
#swap_to_ORG("jko_body", "RIG-jko", "jko_body.001", 26) # Extra
#swap_to_ORG("jko_body", "RIG-jko", "jko_body.001", 27) # Extreme Deform