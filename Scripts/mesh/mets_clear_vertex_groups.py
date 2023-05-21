# NOT MINE -> https://github.com/Mets3D/mets_tools
import bpy

def flip_name(from_name):
    # based on BLI_string_flip_side_name in https://developer.blender.org/diffusion/B/browse/master/source/blender/blenlib/intern/string_utils.c
    
    l = len(from_name)	# Number of characters from left to right, that we still care about. At first we care about all of them.
    
    # Handling .### cases
    if("." in from_name):
        # Make sure there are only digits after the last period
        after_last_period = from_name.split(".")[-1]
        before_last_period = from_name.replace("."+after_last_period, "")
        all_digits = True
        for c in after_last_period:
            if( c not in "0123456789" ):
                all_digits = False
                break
        # If that is so, then we don't care about the characters after this last period.
        if(all_digits):
            l = len(before_last_period)
    
    # Case: Suffix or prefix R r L l separated by . - _
    name = from_name[:l]
    new_name = name
    separators = ".-_"
    for s in separators:
        # Suffixes
        if(s+"L" == name[-2:]):
            new_name = name[:-1] + 'R'
            break
        if(s+"R" == name[-2:]):
            new_name = name[:-1] + 'L'
            break
            
        if(s+"l" == name[-2:]):
            new_name = name[:-1] + 'r'
            break
        if(s+"r" == name[-2:]):
            new_name = name[:-1] + 'l'
            break
        
        # Prefixes
        if("L"+s == name[:2]):
            new_name = "R" + name[1:]
            break
        if("R"+s == name[:2]):
            new_name = "L" + name[1:]
            break
        
        if("l"+s == name[:2]):
            new_name = "r" + name[1:]
            break
        if("r"+s == name[:2]):
            new_name = "l" + name[1:]
            break
    
    if(new_name != name):
        return new_name + from_name[l:]
    
    # Case: "left" or "right" with any case found anywhere in the string.
    
    left = ['left', 'Left', 'LEFT']
    right = ['right', 'Right', 'RIGHT']
    
    lists = [left, right, left]	# To get the opposite side, we just get lists[i-1]. No duplicate code, yay!
    
    # Trying to find any left/right string.
    for list_idx in range(1, 3):
        for side_idx, side in enumerate(lists[list_idx]):
            if(side in name):
                # If it occurs more than once, only replace the last occurrence.
                before_last_side = "".join(name.split(side)[:-1])
                after_last_side = name.split(side)[-1]
                opp_side = lists[list_idx-1][side_idx]
                return before_last_side + opp_side + after_last_side + from_name[l:]
    
    # If nothing was found, return the original string.
    return from_name

#===========================

org_active = bpy.context.object

opt_save_modifier_vgroups = True # opt = optional
opt_save_bone_vgroups = True
opt_save_nonzero_vgroups = True

objs = [bpy.context.object] # Single object.
#objs = bpy.data.objects # All objects.

for obj in objs:
    if(len(obj.vertex_groups) == 0): continue
    
    bpy.context.view_layer.objects.active = obj

    # Clean 0 weights
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0)

    # Saving vertex groups that are used by modifiers and therefore should not be removed
    safe_groups = []
    def save_groups_by_attributes(owner):
        # Look through an object's attributes. If its value is a string, try to find a vertex group with the same name. If found, make sure we don't delete it.
        for attr in dir(owner):
            value = getattr(owner, attr)
            if(type(value)==str):
                vg = obj.vertex_groups.get(value)
                if(vg):
                    safe_groups.append(vg)

    # Save any vertex groups used by modifier parameters.
#    if(self.opt_save_modifier_vgroups):
    if opt_save_modifier_vgroups:
        for m in obj.modifiers:
            save_groups_by_attributes(m)
            if(hasattr(m, 'settings')):	#Physics modifiers
                save_groups_by_attributes(m.settings)

    # Getting a list of bone names from all armature modifiers.
    bone_names = []
    for m in obj.modifiers:
        if(m.type == 'ARMATURE'):
            armature = m.object
            if armature is None:
                continue
            if(bone_names is None):
                bone_names = list(map(lambda x: x.name, armature.pose.bones))
            else:
                bone_names.extend(list(map(lambda x: x.name, armature.pose.bones)))
    
    # Saving any vertex groups that correspond to a bone name
#    if(self.opt_save_bone_vgroups):
    if opt_save_bone_vgroups:
        for bn in bone_names:
            vg = obj.vertex_groups.get(bn)
            if(vg):
                safe_groups.append(vg)
        
    # Saving vertex groups that have any weights assigned to them, also considering mirror modifiers
#    if(self.opt_save_nonzero_vgroups):
    if opt_save_nonzero_vgroups:
        for vg in obj.vertex_groups:	# For each vertex group
            for i in range(0, len(obj.data.vertices)):	# For each vertex
                try:
                    vg.weight(i)							# If there's a weight assigned to this vert (else exception)
                    if(vg not in safe_groups):
                        safe_groups.append(vg)
                        
                        opp_name = flip_name(vg.name)
                        opp_group = obj.vertex_groups.get(opp_name)
                        if(opp_group):
                            safe_groups.append(opp_group)
                        break
                except RuntimeError:
                    continue
    
    # Clearing vertex groups that didn't get saved
    for vg in obj.vertex_groups:
        if(vg not in safe_groups):
            print("Unused vgroup removed: "+vg.name)
            obj.vertex_groups.remove(vg)

bpy.context.view_layer.objects.active = org_active