import bpy

def fk_cursor_handler(scene, depsgraph):

    ik_bone_list = {
#        'controller_bone': ['lowarm_bone', 'uparm_bone', 'pole_target'],
#        'controller_bone': ['elbow_bone', 'shoulder_bone', 'pole_target'],
        'G_hand_ik_L': ['ORG-G_uparm_L', 'ORG-G_lowarm_L', 'G_uparm_ik_target_L'],
        'G_hand_ik_R': ['ORG-G_uparm_R', 'ORG-G_lowarm_R', 'G_uparm_ik_target_R'],
        'G_foot_ik_L': ['ORG-G_thigh_L', 'ORG-G_calf_L', 'G_thigh_ik_target_L'],
        'G_foot_ik_R': ['ORG-G_thigh_R', 'ORG-G_calf_R', 'G_thigh_ik_target_R'],
    }

    context = bpy.context

    if context.mode == 'POSE' and context.active_bone:
        obj = context.active_object

        for controller, pivots in ik_bone_list.items():
            if not context.active_bone.name in pivots[:2]:
#                context.scene.transform_orientation_slots[0].type = 'NORMAL'
                context.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
                context.scene.cursor.location = (0.0, 0.0, 0.0)
#                break
            else:
#                context.scene.transform_orientation_slots[0].type = 'CURSOR'
                context.tool_settings.transform_pivot_point = 'CURSOR'
                context.scene.cursor.location = context.active_pose_bone.head

                if context.active_bone.name == pivots[0]:   # If uparm/shoulder,
                    obj.data.bones[pivots[2]].select = True # select pole_target.
                context.active_bone.select = False
                obj.data.bones.active = context.active_object.data.bones[controller]
                break

# Unregister the handler if it exists.
if bpy.app.handlers.depsgraph_update_pre:
    for i in bpy.app.handlers.depsgraph_update_pre: # TODO: Don't remove all of them.
        bpy.app.handlers.depsgraph_update_pre.remove(i)
        print(f'Removed {i}')
else:
    bpy.app.handlers.depsgraph_update_pre.append(fk_cursor_handler)
    print(f'Added handler.')