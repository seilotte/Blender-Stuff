def armature_stick_infront_wire(context):
    for obj in context.selected_objects:
        if obj.type == 'ARMATURE':
            obj.data.display_type = 'STICK'
            obj.show_in_front = True
            obj.display_type = 'WIRE'

def armature_assign(context):
    sei_vars = context.scene.sei_variables
    armature = sei_vars.armature

    is_rigify_rig = False
    if armature and armature.type == 'ARMATURE':
        for bone in armature.data.bones:
            if bone.layers[31] and bone.name.startswith('ORG-'):
                is_rigify_rig = True
                break

    mod_exists = False
    for obj in context.selected_objects:
        if obj.type != 'MESH': continue

        for mod in obj.modifiers: # Check for modifier.
            if mod.type == 'ARMATURE':
                mod_exists = True
                arm_mod = mod
                break
        if not mod_exists:
            arm_mod = obj.modifiers.new('Armature', 'ARMATURE')
        arm_mod.object = armature # Assign it.

        for vgroup in obj.vertex_groups:
            if not i.name.startswith('DEF-'): # Add prefix.
                if '---' in i.name: break
                i.name = 'DEF-' + i.name
            else:
                if i.name.startswith('DEF-'): # Remove prefix.
                    i.name = i.name.replace('DEF-', '')