import bpy
from mathutils import Vector

ob = bpy.context.active_object

ob.data.calc_normals_split()
new_uv  = ob.data.uv_layers.new(name = "Normals")

for face in ob.data.polygons:
    for loop in face.loop_indices:
        normalVector = Vector((ob.data.loops[loop].normal.x,ob.data.loops[loop].normal.y))
        new_uv.data[loop].uv = normalVector