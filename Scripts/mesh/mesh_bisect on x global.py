import bpy
#import bmesh

# Needs "edit mode" and select the desired vertices.
bpy.ops.mesh.bisect(
    plane_co=(0, 0, 0),
    plane_no=(1, 0, 0),
    use_fill=True,
    clear_inner=True
)

#context = bpy.context
#obj = context.active_object
##mesh = obj.data

#bm = bmesh.new()
#bm.from_mesh(obj.data)

#for v in bm.verts:
#    if v.co.x > 0:
#        v.co.x *= -1

#bm.to_mesh(obj.data)
#bm.free()
#mesh.update()