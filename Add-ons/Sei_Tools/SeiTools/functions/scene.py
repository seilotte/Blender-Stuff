def scene_hide_sockets_from_group_inputs(context):
    tree = context.space_data.node_tree
    if tree.nodes.active: # Check recursively until we find the tree.
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

            for node in tree.nodes:
                if node.type != 'GROUP_INPUT': continue
                if node.mute: continue

                for socket in node.outputs:
                    socket.hide = True

def scene_simplify_modifiers(self, context):
    sei_vars = context.scene.sei_variables

    for obj in context.selected_objects:
        if obj.type != 'MESH': continue
        for mod in obj.modifiers:
            if mod.type in self.modifier_properties:
                viewport_property, render_property , icon_name = self.modifier_properties[mod.type]
                mod.show_viewport = getattr(sei_vars, viewport_property)
                mod.show_render = getattr(sei_vars, render_property)