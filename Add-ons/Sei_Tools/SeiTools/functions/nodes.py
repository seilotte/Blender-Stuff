def nodes_hide_sockets_from_group_inputs(context):
    tree = context.space_data.node_tree
    if tree.nodes.active: # Check recursively until we find the tree.
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

            for node in tree.nodes:
                if node.type != 'GROUP_INPUT': continue
                if node.mute: continue

                for socket in node.outputs:
                    socket.hide = True

def nodes_assign_image_space(context):
    sei_vars = context.scene.sei_variables
    color_space = sei_vars.image_color_space

    for node in context.selected_nodes:
        if node.type == 'TEX_IMAGE':
            if node.image.alpha_mode != 'CHANNEL_PACKED':
                node.image.alpha_mode = 'CHANNEL_PACKED'

            node.image.colorspace_settings.name = color_space