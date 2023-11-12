import bpy

obj_types_list = ['MESH', 'ARMATURE', 'LIGHT', 'CAMERA',]

def scene_assign_view_layer_name():
    for obj in bpy.data.objects:
        if obj.type in obj_types_list:
            obj.data.name = obj.name


modifier_properties_list = (
# modifier_type, ui_text, ui_icon, boolean_custom, boolean_custom.
('ARMATURE', 'Armature', 'MOD_ARMATURE', 'simplify_v_armature', 'simplify_r_armature'),
('SUBSURF', 'Subsurf', 'MOD_SUBSURF', 'simplify_v_subsurf', 'simplify_r_subsurf'),
('MASK', 'Mask', 'MOD_MASK', 'simplify_v_mask', 'simplify_r_mask'),
('NODES', 'Geometry Nodes', 'GEOMETRY_NODES', 'simplify_v_nodes', 'simplify_r_nodes'),
('SOLIDIFY', 'Solidify', 'MOD_SOLIDIFY', 'simplify_v_solidify', 'simplify_r_solidify'),
('DATA_TRANSFER', 'Data Transfer', 'MOD_DATA_TRANSFER', 'simplify_v_dtransfer', 'simplify_r_dtransfer'),
('CORRECTIVE_SMOOTH', 'Smooth Corrective', 'MOD_SMOOTH', 'simplify_v_csmooth', 'simplify_r_csmooth'),
('SHRINKWRAP', 'Shrinkwrap', 'MOD_SHRINKWRAP', 'simplify_v_shrinkwrap', 'simplify_r_shrinkwrap'),
)

def scene_simplify_modifiers(self, context):
    sei_vars = context.scene.sei_variables

    for obj in (obj for obj in context.selected_objects if obj.type == 'MESH'):
        for mod in obj.modifiers:
            list_items = next((m for m in modifier_properties_list if m[0] == mod.type), None)
            if list_items:
                mod.show_viewport, mod.show_render = getattr(sei_vars, list_items[3]), getattr(sei_vars, list_items[4])