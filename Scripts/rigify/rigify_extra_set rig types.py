import bpy

# There's a better way inside the AswTools addon.

bones = bpy.context.selected_pose_bones
sei_bvars = "head"

def removeRigifyLayers():
    # Disable all bone fk_layers.
    abones.rigify_parameters.fk_layers[0] = False
    abones.rigify_parameters.tweak_layers[0] = False
    for i in range(31):
        i += 1
        abones.rigify_parameters.fk_layers[i] = False
        abones.rigify_parameters.tweak_layers[i] = False

def assignRigifyLayer(bone_fklayer, bone_tklayer):
    abones.rigify_parameters.fk_layers[bone_fklayer] = True
    abones.rigify_parameters.tweak_layers[bone_tklayer] = True

for bone in bones:
    type = bpy.context.object.pose.bones[bone.name].rigify_type
    print(len(bpy.context.object.pose.bones[bone.name].rigify_type))
            
    abones = bpy.context.object.pose.bones[bone.name]
            
if len(abones.rigify_type)>0:
    print("Rigify Type already assinged as: "+type)
elif sei_bvars == "arm":
    abones.rigify_type = "limbs.super_limb"
    abones.rigify_parameters.make_ik_wrist_pivot = True
    abones.rigify_parameters.limb_type = "arm"
    removeRigifyLayers()
    assignRigifyLayer(9, 10)
    print("arm")

elif sei_bvars == "leg":
    abones.rigify_type = "limbs.super_limb"
    abones.rigify_parameters.limb_type = "leg"
    removeRigifyLayers()
    assignRigifyLayer(18, 19)
    print("leg")

elif sei_bvars == "spine":
    abones.rigify_type = "spines.basic_spine"
    removeRigifyLayers()
    assignRigifyLayer(7, 6)

elif sei_bvars == "head":
    abones.rigify_type = "spines.super_head"
    abones.rigify_parameters.connect_chain = True
    removeRigifyLayers()
    assignRigifyLayer(0, 7)