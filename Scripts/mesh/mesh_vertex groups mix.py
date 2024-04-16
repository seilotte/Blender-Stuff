import bpy

obj = bpy.context.active_object

A = obj.vertex_groups.get('G_lowerHead') # Target.
B = obj.vertex_groups.get('G_pupil_R')
mix_mode = 'ADD' # REPLACE, ADD, SUBTRACT, etc.

# Get weights.
# https://blender.stackexchange.com/questions/46834/how-can-i-get-the-weight-for-all-vertices-in-a-vertex-group
def get_weights(obj, vertex_group):
    for index, vertex in enumerate(obj.data.vertices):
        for g in vertex.groups:
            if g.group == vertex_group.index:
                yield (index, g.weight)
                break

if obj.type == 'MESH' and A and B:

    # Iterate over index, weights.
    for index, weights in get_weights(obj, B):
        A.add([index], weights, mix_mode)