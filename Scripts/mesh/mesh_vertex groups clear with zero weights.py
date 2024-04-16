import bpy

obj = bpy.context.active_object

''' Removes vertex groups with cero weights. Note that it does not take into
consideration locked groups, groups used by modifiers, etcetera. '''

for vgroup in obj.vertex_groups:
    has_weight = False # Resets every iteration.

    for vertex in obj.data.vertices:
        if has_weight: break

        for g in vertex.groups: # It can be assigned to multiple vertex groups.
            if g.group == vgroup.index and g.weight > 0.0:
                has_weight = True
                break

    if not has_weight: # Is false.
        obj.vertex_groups.remove(vgroup)