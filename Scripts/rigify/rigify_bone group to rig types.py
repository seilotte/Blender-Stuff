import bpy

obj = bpy.context.view_layer.objects.active

group_name = 'Rig_Type'

for bone in obj.pose.bones:
    if bone.rigify_type:
        # Assign the bone group.
        if bone.rigify_type != 'basic.super_copy':
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