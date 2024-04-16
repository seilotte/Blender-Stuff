'''
The program assumes you execute the script in "object mode"!
TODO:
    - Add geometry nodes modifier automatically.
    - Keep shape key(s) settings and drivers.
'''

import bpy
import bmesh

context = bpy.context

for obj in context.selected_objects:
    if obj.type != 'MESH': continue

    if obj.data.shape_keys:

        bm = bmesh.new()
        bm.from_mesh(obj.data) # object mode
#        bm.from_edit_mesh(obj.data) # edit mode

        for shape_key in obj.data.shape_keys.key_blocks[1:]:

            if shape_key.name not in obj.data.attributes:
                obj.data.attributes.new(name=shape_key.name, domain='POINT', type='FLOAT_VECTOR')
            new_attribute = obj.data.attributes[shape_key.name]

            for v_index, vertex in enumerate(bm.verts):
                new_attribute.data[v_index].vector = shape_key.data[v_index].co

#        bm.to_mesh(obj.data)
        bm.free()