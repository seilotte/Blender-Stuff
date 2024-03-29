import bpy
from mathutils import Vector

exists = False

for obj in bpy.context.selected_objects:
    if obj.type != 'MESH': continue

    for attribute in obj.data.attributes:
        if attribute.name == 'Normals':
            exists = True
            break

    if not exists:
        obj.data.calc_normals_split()
        new_attribute = obj.data.attributes.new(name='Normals', domain='CORNER', type='FLOAT_VECTOR')

        for face in obj.data.polygons:
            for loop in face.loop_indices:
                normal_vector = Vector((obj.data.loops[loop].normal.x,
                                        obj.data.loops[loop].normal.y,
                                        obj.data.loops[loop].normal.z,
                                        ))
                new_attribute.data[loop].vector = normal_vector
        exists = False