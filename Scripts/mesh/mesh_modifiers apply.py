import bpy

for obj in bpy.context.selected_objects:
    if obj.type != 'MESH':
        continue
    bpy.context.view_layer.objects.active = obj
    for mod in obj.modifiers:
        bpy.ops.object.modifier_apply(modifier=mod.name)