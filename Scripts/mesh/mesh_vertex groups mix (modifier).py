import bpy

obj = bpy.context.view_layer.objects.active

x = 0
for v in obj.vertex_groups:
    if '.001' in v.name:
        org_v = obj.vertex_groups.get(v.name[:-4])
        if org_v:
            # Count for name.
            if x > 0:
                value = x / 1000
                value = '{:.3f}'.format(value)
                mod_name = 'VertexWeightMix' + value[1:]
            else:
                mod_name = 'VertexWeightMix'
            x += 1

            # Add modifier.
            bpy.ops.object.modifier_add(type='VERTEX_WEIGHT_MIX')
            mod = obj.modifiers[mod_name]
            mod.mix_set = 'ALL'
            mod.mix_mode = 'ADD'
            
            # Assign vertex groups.
            mod.vertex_group_a = org_v.name
            mod.vertex_group_b = v.name
            
#            # Apply modifier and remove duplicate.
#            bpy.ops.object.modifier_apply(modifiermod_name)
#            obj.vertex_groups.remove(v)

## Remove vertex groups.
#for v in obj.vertex_groups:
#    if '.001' in v.name:
#        obj.vertex_groups.remove(v)