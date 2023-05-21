import bpy

for obj in bpy.context.selected_objects:
    obj.data.name = obj.name