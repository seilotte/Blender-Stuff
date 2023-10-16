import bpy

#for obj in bpy.context.scene.objects:
for obj in bpy.data.objects:
    if obj.type != 'ARMATURE': continue
    obj.data.display_type = 'STICK'
    obj.show_in_front = True
    obj.display_type = 'WIRE'