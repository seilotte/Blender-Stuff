#https://blender.stackexchange.com/questions/77600/selecting-vertices-by-weight

import bpy

minWeight = .6
maxWeight = .7
vertexGroupIndex = 1

bpy.ops.object.mode_set(mode = 'EDIT') 
bpy.ops.mesh.select_mode(type="VERT")
bpy.ops.mesh.select_all(action = 'DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT') # Switch to Object to get selection
obj = bpy.context.active_object 
verts = [v for v in obj.data.vertices]
for v in verts:
  weight = v.groups[vertexGroupIndex].weight
  if weight <= maxWeight and weight >= minWeight:
    v.select = True
bpy.ops.object.mode_set(mode = 'EDIT')  