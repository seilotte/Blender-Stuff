import bpy

context = bpy.context

obj = context.active_object # Select the target object.
armature = bpy.data.objects.get("MTA-ANL_body") # Input the armature name.

# Get weights.
# https://blender.stackexchange.com/questions/46834/how-can-i-get-the-weight-for-all-vertices-in-a-vertex-group
def get_weights(obj, vertex_group):
    for index, vertex in enumerate(obj.data.vertices):
        for g in vertex.groups:
            if g.group == vertex_group.index:
                yield (index, g.weight)
                break

if obj and obj.type == 'MESH' and armature and armature.type == 'ARMATURE':
    empty_vertex_groups = {vgroup.name for vgroup in obj.vertex_groups if not any(weight != 0.0 for _, weight in get_weights(obj, vgroup))}

    if empty_vertex_groups:
#        print(f'Empty vertex groups: {", ".join(empty_vertex_groups)}')
        context.view_layer.objects.active = armature
        active_mode = context.mode
        bpy.ops.object.mode_set(mode='EDIT')

        for bone in armature.data.edit_bones:
            if bone.name in set(empty_vertex_groups):
                print(f'Removed bone: "{bone.name}"')
                armature.data.edit_bones.remove(bone)

        bpy.ops.object.mode_set(mode=active_mode)

#        # Remove vertex groups. TODO: Do it before for perfomance.
#        for v in obj.vertex_groups:
#            if v.name in set(empty_vertex_groups):
#                print(f'Removed vertex group: "{v.name}"')
#                obj.vertex_groups.remove(v)