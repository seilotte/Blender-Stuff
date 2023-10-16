import bpy
from mathutils import Vector

obj = bpy.context.active_object

obj.data.calc_normals_split()
new_vcol = obj.data.vertex_colors.new(name='Normals')

for face in obj.data.polygons:
    for loop in face.loop_indices:
        normal_vector = Vector((obj.data.loops[loop].normal.x,
                                obj.data.loops[loop].normal.y,
                                obj.data.loops[loop].normal.z,
                                0.0))
        new_vcol.data[loop].color = normal_vector