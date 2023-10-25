import bpy

def scene_assign_view_layer_name():
    for obj in bpy.data.objects:
        obj.data.name = obj.name

def scene_simplify_modifiers(self, context):
    sei_vars = context.scene.sei_variables

    for obj in context.selected_objects:
        if obj.type != 'MESH': continue
        for mod in obj.modifiers:
            if mod.type in self.modifier_properties:
                viewport_property, render_property , icon_name = self.modifier_properties[mod.type]
                mod.show_viewport = getattr(sei_vars, viewport_property)
                mod.show_render = getattr(sei_vars, render_property)