import bpy

# From Aerthas Veras.

#Startuprigify
if bpy.context.view_layer.objects.active.type == 'ARMATURE':
    bpy.ops.pose.rigify_layer_init('INVOKE_DEFAULT', )
    bpy.ops.armature.rigify_add_bone_groups('INVOKE_DEFAULT', )
    if (len(bpy.context.view_layer.objects.active.data.rigify_colors) < 7):
        bpy.ops.armature.rigify_bone_group_add('INVOKE_DEFAULT', )
    bpy.context.view_layer.objects.active.data.rigify_colors[6].normal = (0.5, 0.5, 0.5)
    bpy.context.view_layer.objects.active.data.rigify_colors[6].name = 'Extreme Deform'
    
    #Apply_Layers
    layers = None
    layers = [
            ["Hair",1,2],
            ["Hair [Tweaks]",1,4],
            ["Face",2,3],
            ["Face [Primary]",2,2],
            ["Face [Secondary]",2,4],
            ["Torso [IK]",3,2],
            ["Torso [FK]",3,5],
            ["Torso [Tweak]",3,4],
            ["Arm.R [IK]",4,2],
            ["Arm.R [FK]",5,5],
            ["Arm.R [Tweak]",6,4],
            ["Arm.L [IK]",4,2],
            ["Arm.L [FK]",5,5],
            ["Arm.L [Tweak]",6,4],
            ["Leg.R [IK]",7,2],
            ["Leg.R [FK]",8,5],
            ["Leg.R [Tweak]",9,4],
            ["Leg.L [IK]",7,2],
            ["Leg.L [FK]",8,5],
            ["Leg.L [Tweak]",9,4],
            ["Fingers",10,3],
            ["Fingers [IK]",10,2],
            ["Fingers [Tweak]",10,4],
            ["Clothes",11,6],
            ["Clothes [Secondary]",11,4],
            ["G_B",12,4],
            ["Extra",12,6],
            ["Extreme Deform",13,7],
        ]
    for i in range(len(layers)):
        bpy.context.view_layer.objects.active.data.rigify_layers[i].name = layers[i][0]
        bpy.context.view_layer.objects.active.data.rigify_layers[i].row = layers[i][1]
        bpy.context.view_layer.objects.active.data.rigify_layers[i].group = layers[i][2]