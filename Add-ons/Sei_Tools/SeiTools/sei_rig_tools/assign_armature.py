import bpy

vars = bpy.context.scene.sei_variables
all = bpy.context.selected_objects


armature = vars.armature
x = 0 # Is rig rigify?

if armature and armature.type == 'ARMATURE':
    for bone in armature.data.bones:
        if bone.layers[31]:
            if bone.name.startswith('ORG-'):
                x = 1
                break


for obj in all:
    if obj.type != 'MESH':
        continue

    # Add/Assign armature modifier.
    if 'Armature' not in obj.modifiers:
        obj.modifiers.new('Armature', 'ARMATURE')
    obj.modifiers['Armature'].object = armature

    for i in obj.vertex_groups:
        if x > 0:
            # Add "DEF-".
            if not i.name.startswith('DEF-'):
                if '---' in i.name:
                    break
                i.name = 'DEF-' + i.name
        else:
            # Remove "DEF-".
            if i.name.startswith('DEF-'):
                i.name = i.name.replace('DEF-', '')