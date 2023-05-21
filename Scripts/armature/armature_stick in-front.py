import bpy

for obj in bpy.context.scene.objects:
    if obj.type == "ARMATURE":
        obj.data.display_type = 'STICK'
        obj.show_in_front = True