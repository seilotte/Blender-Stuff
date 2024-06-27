import bpy

blend_data = [
    # https://docs.blender.org/api/current/bpy.types.BlendData.html#bpy.types.BlendData
    'armatures',
    'meshes',
    'objects',
    'scenes',
    'screens'
]

for x in blend_data:
    bdata = getattr(bpy.data, x, None)

    if bdata is None:
        continue
    
#    # Armature > Bones & EditBones
#    if x == 'armatures':
#        for armature in bdata:
#            armature.id_properties_clear()

#            for bone in armature.bones:
#                bone.id_properties_clear()

##                bone = armature.edit_bones[bone.name] # EditBones; Needs edit mode.
##                bone.id_properties_clear()

#    # Object > PoseBones
#    elif x == 'objects':
#        for object in bdata:
#            object.id_properties_clear()

#            if object.type != 'ARMATURE':
#                continue

#            for bone in object.pose.bones:
#                bone.id_properties_clear()

    # Scene > ViewLayers
    elif x == 'scenes':
        for scene in bdata:
            scene.id_properties_clear()

            for view_layer in scene.view_layers:
                view_layer.id_properties_clear()

    else:
        for i in bdata:
            i.id_properties_clear()