import bpy

obj = bpy.context.active_object

''' Get vertex position, just like the node geometry -> position. '''
## Create attributes for A, B, and C positions.
#attribute_a = obj.data.attributes.new(name='Position_A', type='FLOAT_VECTOR', domain='POINT')
#attribute_b = obj.data.attributes.new(name='Position_B', type='FLOAT_VECTOR', domain='POINT')
#attribute_c = obj.data.attributes.new(name='Position_C', type='FLOAT_VECTOR', domain='POINT')

#for face in obj.data.polygons:
#    for loop_index in face.loop_indices:
#        vertex_index = obj.data.loops[loop_index].vertex_index
#        
#        world_position = obj.matrix_world @ obj.data.vertices[vertex_index].co

#        attribute_a.data[vertex_index].vector = world_position

#=========

''' Calculate barycentric coordinates. '''
from mathutils.geometry import barycentric_transform

# Create attributes for U, V, and W.
attribute_u = obj.data.attributes.new(name='bar_u', type='FLOAT_VECTOR', domain='POINT')
attribute_v = obj.data.attributes.new(name='bar_v', type='FLOAT_VECTOR', domain='POINT')
attribute_w = obj.data.attributes.new(name='bar_w', type='FLOAT_VECTOR', domain='POINT')

for face in obj.data.polygons:
    # Get world positoins of vertices, A, B and C.
    A = obj.matrix_world @ obj.data.vertices[face.vertices[0]].co
    B = obj.matrix_world @ obj.data.vertices[face.vertices[1]].co
    C = obj.matrix_world @ obj.data.vertices[face.vertices[2]].co

    # Iterate over the vertices of the face.
    for loop_index in face.loop_indices:
        vertex_index = obj.data.loops[loop_index].vertex_index
        
        world_position = obj.matrix_world @ obj.data.vertices[vertex_index].co
        # barycentric_transform(point, source_traingle_vertex_1, ... target_traingle_vertex_1, ...)
        u, v, w = barycentric_transform(world_position, A, B, C, A, B, C)

        attribute_u.data[vertex_index].vector = (u, v, w)
        attribute_v.data[vertex_index].vector = (v, w, u)
        attribute_w.data[vertex_index].vector = (v, u, v)