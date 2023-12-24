# No vertices selected in edit mode and object mode are required.
import bpy
import bmesh

context = bpy.context

for obj in context.selected_objects:
    if obj.type != 'MESH': continue

    vcol_layer = obj.data.vertex_colors[0] # First layer.

    for face in obj.data.polygons:
        for loop_index in face.loop_indices:

            vertex_index = obj.data.loops[loop_index].vertex_index
            vcol_channel = vcol_layer.data[loop_index].color[2] # Blue channel.

            if vcol_channel <= 0.0: # Threshold(s) check.
                obj.data.vertices[vertex_index].select = True

    active_mode = obj.mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.mark_freestyle_face(clear=False)
    bpy.ops.object.mode_set(mode=active_mode)