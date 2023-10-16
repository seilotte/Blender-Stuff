import bpy

armature = bpy.context.view_layer.objects['targegt_armature_name']
new_armature_name = 'Test'

# Create a new armature.
new_armature = bpy.data.armatures.new(name=new_armature_name)
new_armature = bpy.data.objects.new(name=new_armature_name, object_data=new_armature)
bpy.context.scene.collection.objects.link(new_armature)

new_armature.show_in_front = True
new_armature.data.display_type = 'STICK'

active_mode = armature.mode
new_armature.select_set(True)
bpy.ops.object.mode_set(mode = 'EDIT')

bone_dict = {}
# Copy the bones from the armature.
for bone in armature.data.edit_bones:
    new_bone = new_armature.data.edit_bones.new(bone.name)
    new_bone.head = bone.head
    new_bone.tail = bone.tail
    new_bone.roll = bone.roll
    new_bone.use_connect = bone.use_connect
    new_bone.layers = bone.layers
#    new_bone.parent = bone.parent

    bone_dict[bone.name] = new_bone

# Set parent relationships
for bone in armature.data.edit_bones:
    if bone.parent is not None:
        parent_name = bone.parent.name
        if parent_name in bone_dict:
            new_bone = bone_dict[bone.name]
            new_parent = bone_dict[parent_name]
            new_bone.parent = new_parent

bpy.ops.object.mode_set(mode = active_mode)