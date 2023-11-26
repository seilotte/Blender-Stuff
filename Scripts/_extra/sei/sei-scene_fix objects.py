import bpy

'''
Objects names.
Objects rotation -> "XYZ".
Armature -> Wire, in-front, stick.
Bones rotation -> "XYZ".
Materials -> Viewport display fix.
'''
for obj in bpy.data.objects:
    obj.name = obj.data.name
    obj.rotation_mode = 'XYZ'

    if obj.type == 'ARMATURE':
        obj.display_type = 'WIRE'
        obj.data.display_type = 'STICK'
        obj.show_in_front = True

        for bone in obj.pose.bones:
            bone.rotation_mode = 'XYZ'

for mat in bpy.data.materials:
    if mat.name == 'Dots Stroke': continue
    mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)
    mat.metallic = 0.0
    mat.roughness = 0.5