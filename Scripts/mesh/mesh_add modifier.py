import bpy

bpy.context.active_object.modifiers.new("mask",'MASK')

#---
#https://blender.stackexchange.com/questions/58676/add-modifier-to-selected-and-another-to-active-object

# Why I did this!
o = bpy.context.active_object
o.location.z += 0.15

# Add a solidify modifier on the active object.
sol_mod = o.modifiers.new('Solidify', 'SOLIDIFY') # (name, type)
sol_mod.thickness = 0.3

# I can't recall why I did this.
for obj in bpy.context.selected_objects:
    if obj == o:
        continue

    # Check if "SelectedSolidify" exists.
    selected_sol_mod = obj.modifiers.get('SelectedSolidify')
    if selected_sol_mod is None:
        selected_sol_mod = obj.modifiers.new('SelectedSolidify', 'SOLIDIFY')

    # Set paramters.
    selected_sol_mod.thickness = 0.1
    obj.location.z = 0.5 # Yes.

    # Add a boolean modifier.
    bool_mod = obj.modifiers.new('Bool', 'BOOLEAN')
    bool_mod.object = obj
    bool_mod.solver = 'CARVE'
    bool_mod.operation = 'DIFFERENCE'