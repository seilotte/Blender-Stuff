import bpy

#for obj in bpy.data.objects:
for obj in bpy.context.selected_objects:
    if obj.type != 'MESH':
        continue
    
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            mod.use_deform_preserve_volume = True