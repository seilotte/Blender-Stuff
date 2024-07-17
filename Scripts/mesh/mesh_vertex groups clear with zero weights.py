import bpy

obj = bpy.context.active_object

''' Removes vertex groups with cero weights. Note that it does not take into
consideration groups used by modifiers, etcetera. '''

safe_vgroups = {
    obj.vertex_groups[g.group]
    for vertex in obj.data.vertices
    for g in vertex.groups
    if g.weight > 0.0
}

for vgroup in obj.vertex_groups:
    if vgroup in safe_vgroups:
        continue
    elif vgroup.lock_weight:
        continue

    obj.vertex_groups.remove(vgroup)