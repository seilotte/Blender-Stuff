import bpy

obj = bpy.context.view_layer.objects.active

# TODO: Use bmesh instead of ops.
if obj.type == "MESH":
    active_mode = obj.mode
    for i, mSlot in enumerate(obj.material_slots):
        if "outline" in mSlot.name.lower() or "shadow" in mSlot.name.lower():
            
            # Unselect everything.
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            
            # Select the material.
            obj.active_material_index = i
            bpy.ops.object.material_slot_select()
            bpy.ops.mesh.delete(type='VERT')
            
            bpy.ops.object.mode_set(mode=active_mode)