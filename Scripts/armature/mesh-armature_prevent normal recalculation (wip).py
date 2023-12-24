import bpy
from mathutils import Matrix

#=========

#import bpy

## Search for word in bones and vertex groups names.
#def search_vg_bones(condition_word):
#    empty_list = []
#    word_condition = 'def'

#    for obj in bpy.data.objects:
#        if obj.type == 'ARMATURE':
#            for bone in obj.data.bones:
#                if word_condition in bone.name:
#                    empty_list.append(bone.name)
#        if obj.type == 'MESH':
#            for v in obj.vertex_groups:
#                if word_condition in v.name:
#                    empty_list.append(v.name)

#    empty_list = list(dict.fromkeys(empty_list))
#    for i in empty_list:
#        print(f"'{i}',")
#    for i in range(5):
#        print('_')

#search_vg_bones("def")

#=========

custom_bone_list = [ # Bones that will get the constraints.
    'G_pelvist', 'G_waist', 'G_stomach', 'G_chest',
    'G_neck', 'G_Head_Attatch',
    'G_shoulder_L', 'G_clavicle_L',
    'G_shoulder_R', 'G_clavicle_R',
    'G_uparm_L', 'G_lowarm_L', 'G_hand_L',
    'G_uparm_R', 'G_lowarm_R', 'G_hand_R',
    'G_thigh_L', 'G_calf_L', 'G_foot_L', 'G_toe_L',
    'G_thigh_R', 'G_calf_R', 'G_foot_R', 'G_toe_R',
    'G_fng_L_a1_', 'G_fng_L_b1_', 'G_fng_L_c1_', 'G_fng_L_d1_', 'G_fng_L_e1_',
    'G_fng_R_a1_', 'G_fng_R_b1_', 'G_fng_R_c1_', 'G_fng_R_d1_', 'G_fng_R_e1_',
    'G_Head_def', # hair bone

    'G_pelvis_def',
    'G_waist_def',
    'G_stomach_def',
    'G_clavicle_L_def',
    'G_clavicle_R_def',
    'G_shoulder_L_def',
    'G_shoulder_R_def',
    'G_chest_def',
    'G_breast_def_R',
    'G_breast_def_L',
    'G_neck_def',
    'G_Head_def',
    'G_hat_def',
]

# Create collection.
collection_name = '_Normals'
if not bpy.data.collections.get(collection_name):
    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)

# Dup armature.
for armature in bpy.context.selected_objects:
    if armature.type != 'ARMATURE': continue
    new_armature = armature.copy()
    new_collection.objects.link(new_armature)

    for bone in new_armature.pose.bones:
        bone.rotation_mode = 'XYZ'
        bone.matrix_basis = Matrix() # Reset pose.
        for i in range(3):
            bone.lock_location[i] = True
            bone.lock_rotation[i] = True
            bone.lock_scale[i] = True

        # Add constraint(s).
        if bone.name in custom_bone_list:
            rotation_constraint = bone.constraints.new('COPY_ROTATION')
            rotation_constraint.target = armature
            rotation_constraint.subtarget = bone.name


    # Dup objects -> Move to Collection -> Assign Data Transfer
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.modifiers:
            for mod in obj.modifiers:
                if mod.type != 'ARMATURE': continue
                if mod.object == armature:
                    # Create new meshes.
                    new_obj = obj.copy()
                    new_collection.objects.link(new_obj)
                    new_obj.modifiers[mod.name].object = new_armature

                    # Data transfer to meshes.
                    new_mod = obj.modifiers.new('DataTransfer', 'DATA_TRANSFER')
                    new_mod.object = new_obj
                    new_mod.use_loop_data = True
                    new_mod.data_types_loops = {'CUSTOM_NORMAL'}
                    new_mod.loop_mapping = 'TOPOLOGY'
                    break