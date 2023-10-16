import bpy
from mathutils import Matrix
from math import radians

obj = bpy.context.active_object
a = obj.mode

for b in obj.data.edit_bones:
    if b.name == "def_l_wrist":
        rotation_matrix = Matrix.Rotation(radians(-90), 4, b.z_axis)
        pivot_matrix = Matrix.Translation(b.head) # pivot point
        final_matrix = pivot_matrix @ rotation_matrix @ pivot_matrix.inverted() @ b.matrix
        b.matrix = final_matrix
        
        b.length = .05

# Force the viewport to update
bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)