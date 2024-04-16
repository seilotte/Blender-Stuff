# Credit: https://github.com/uhlik/bpy/blob/master/carbon_tools.py
'''
The program assumes the object has the following:
- You need to be in *object mode*!
- An *active* uv map.       // It will use the active/selected uv map.
                            // Line 44; Personal use, it uses the first uv.
- An *active* image node.   // It will look in the active material.
'''

import bpy
import bmesh
import numpy

context = bpy.context

for obj in context.selected_objects:
    if obj.type != 'MESH': continue

    mesh = obj.data

    if not (mat := obj.active_material) \
    or not (active_node := mat.node_tree.nodes.active) \
    or not active_node.type == 'TEX_IMAGE' \
    or not active_node.image \
    or len(mesh.uv_layers) < 1: continue

    image = active_node.image
#    image_name = image.name.split('.')[0] # Remove extension.
    image_name = "Viewport"
    image_width, image_height = image.size
    a = numpy.asarray(image.pixels)
    a = a.reshape((image_height, image_width, 4))

    # Create vertex colour.
    vcol_layer = mesh.vertex_colors.get(image_name) \
                or mesh.vertex_colors.new(name=image_name)
    mesh.vertex_colors.active = vcol_layer

    bm = bmesh.new()
    bm.from_mesh(mesh) # object mode

    vcol_layer = bm.loops.layers.color[image_name]
#    uv_layer = bm.loops.layers.uv.active
    uv_layer = bm.loops.layers.uv[0]

    for face in bm.faces:
        for loop in face.loops:
            uv_x, uv_y = loop[uv_layer].uv.to_tuple()
            xx = int(round( uv_x * (image_width - 1) )) % image_width # xx = pixel_x
            yy = int(round( uv_y * (image_height - 1) )) % image_height # yy = pixel_y
            loop[vcol_layer] = a[yy][xx]

    bm.to_mesh(mesh)
    bm.free()