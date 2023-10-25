import bpy

obj = bpy.context.view_layer.objects.active # ARMATURE check in metarig operator.

if obj.type == 'ARMATURE':
    # Start rigify bone groups.
    bpy.ops.armature.rigify_bone_group_remove_all()
    bpy.ops.pose.rigify_layer_init('INVOKE_DEFAULT', )
    bpy.ops.armature.rigify_add_bone_groups('INVOKE_DEFAULT', )
    if (len(obj.data.rigify_colors) < 7):
        bpy.ops.armature.rigify_bone_group_add('INVOKE_DEFAULT', )
        bpy.ops.armature.rigify_bone_group_add('INVOKE_DEFAULT', )
    obj.data.rigify_colors[1].normal = (1.0, 0.06, 0.1) # IK
    obj.data.rigify_colors[2].normal = (1.0, 0.79, 0.1) # Special
    obj.data.rigify_colors[3].normal = (0.07, 0.5, 0.7) # Tweak
    obj.data.rigify_colors[4].normal = (0.1, 0.6, 0.1) # FK
    
    #obj.data.rigify_colors[6].normal = (0.5, 0.5, 0.5)
#    obj.data.rigify_colors[6].normal = (1.0, 0.6, 0.0)
    obj.data.rigify_colors[6].normal = (0.7, 0.5, 0.6)
    obj.data.rigify_colors[6].name = 'Extreme Deform'
    obj.data.rigify_colors[7].normal = (0.97, 0.26, 0.57)
    obj.data.rigify_colors[7].name = 'Tweak2'

    layers = None
    layers = [
            ["",1,0],
            ["",1,0],
            ["",1,0],
            ["",1,0],
            ["",1,0],
            ["Torso [IK]",4,3],
            ["Torso [FK]",4,5],
            ["Torso [Tweak]",4,4],
            ["Arm.L [IK]",5,2],
            ["Arm.L [FK]",6,5],
            ["Arm.L [Elbow]",7,3],
            ["Arm.R [IK]",5,2],
            ["Arm.R [FK]",6,5],
            ["Arm.R [Elbow]",7,3],
            ["Leg.L [IK]",8,2],
            ["Leg.L [FK]",9,5],
            ["Leg.L [Knee]",10,3],
            ["Leg.R [IK]",8,2],
            ["Leg.R [FK]",9,5],
            ["Leg.R [Knee]",10,3],
            ["Fingers",11,4],
            ["Fingers [IK]",11,2],
            ["Fingers [Tweak]",11,3],
            ["",1,0],
            ["",1,0],
            ["",1,0],
            ["Extra",13,7],
            ["Extreme Deform",13,7],
            ["Root", 14, 1],
        ]
    for i in range(len(layers)):
        obj.data.rigify_layers[i].name = layers[i][0]
        obj.data.rigify_layers[i].row = layers[i][1]
        obj.data.rigify_layers[i].group = layers[i][2]