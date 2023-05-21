import bpy
import bmesh
# README; This program assumes you have only selected and duplicated the desired bones.
# Bones, need to be aligned(head = tail) and parented like a rigify tail.
# All bones need to have a parent and be named ".001", ".002", etc..
# After running the script you need to parent the new mesh to the respective main bone.
# Extrude the vertices of the new mesh if you want collisions.
# Based on this video. https://www.youtube.com/watch?v=XHlyZdAmufk

new_mesh_name = 'Hair_sim'
pin_vertex_group_name = '_pin'
prefix_name = 'PHY-'

obj = bpy.context.active_object

# Create the mesh and bmesh.
new_mesh = bpy.data.meshes.get(new_mesh_name)
new_obj = bpy.data.objects.get(new_mesh_name)

if not new_mesh:
    new_mesh = bpy.data.meshes.new(new_mesh_name)
    new_obj = bpy.data.objects.new(new_mesh_name, new_mesh)
    bpy.context.scene.collection.objects.link(new_obj)

bm = bmesh.new()
#bm.from_mesh(new_mesh) # If you want to add to the existing mesh.


bpy.ops.object.mode_set(mode = 'EDIT')

# Create vertices on the bones.
for bone in bpy.context.selected_editable_bones:
    if bone.head.xyz == bone.parent.tail.xyz:
        vertex = bm.verts.new(bone.tail.xyz)
    else: # Starting bone.
        vertex_start_head = bm.verts.new(bone.head.xyz)
        vertex_start_tail = bm.verts.new(bone.tail.xyz)

# Connect edges.
previous_vertex = None
for vertex in bm.verts:
    if previous_vertex:
        if (previous_vertex.co.z - vertex.co.z) >= 0.015: # Less than with tolerance x.
            bm.edges.new([previous_vertex, vertex])
    previous_vertex = vertex


# Update the mesh with the changes made in the bmesh.
#bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
bm.to_mesh(new_mesh)
new_mesh.update()


# TODO: Find a cleaner solution for assigning the vertex groups.
# Bmesh vertices indexes are different than the mesh vertices indexes.
vertex_group_pin = new_obj.vertex_groups.new(name = pin_vertex_group_name)

for bone in bpy.context.selected_editable_bones:
    vertex_group_name = prefix_name + bone.name[:-4]

    for v in new_obj.data.vertices:
        # Starting bone.
        if v.co == bone.head.xyz and bone.head.xyz != bone.parent.tail.xyz:
            vertex_group_pin.add([v.index], 1.0, 'ADD')

        if v.co == bone.tail.xyz: # Bone tail vertices.
            vertex_group = new_obj.vertex_groups.new(name = vertex_group_name)
            vertex_group.add([v.index], 1.0, 'ADD')


    # Set bone parents.
    bone.use_connect = False
    org_bone = obj.data.edit_bones[bone.name[:-4]]
    bone.parent = org_bone.parent
    org_bone.parent = bone
    # Change name; Keep as in line 58
    bone.name = prefix_name + bone.name[:-4]

# Add damped track constraint.
# TODO: Find a better solution for when changing the bone name, it removes
# the constraint, and in order to update the new name in the pose bones I need
# change to pose mode.
bpy.ops.object.mode_set(mode = 'POSE')
for bone in bpy.context.selected_pose_bones:
    damped_track_mod = bone.constraints.new(type='DAMPED_TRACK')
    damped_track_mod.target = new_obj
    damped_track_mod.subtarget = bone.name

# Add cloth physics and "_pin" group.
cloth_mod = new_obj.modifiers.new(name='', type='CLOTH')
cloth_mod.settings.vertex_group_mass = pin_vertex_group_name
cloth_mod.point_cache.frame_start = bpy.context.scene.frame_start
cloth_mod.point_cache.frame_end = bpy.context.scene.frame_end
cloth_mod.collision_settings.collision_quality = 3
cloth_mod.collision_settings.distance_min = 0.001


bpy.ops.object.mode_set(mode = 'OBJECT')