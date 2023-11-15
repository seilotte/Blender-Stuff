def find_active_node_tree(context):
    tree = context.space_data.node_tree
    # Check recursively until we find the tree.
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree
    return tree


def nodes_hide_sockets_from_group_inputs(context):
    tree = find_active_node_tree(context)

    for node in tree.nodes:
        if node.type != 'GROUP_INPUT': continue
        if node.mute: continue

        for socket in node.outputs:
            socket.hide = True

def nodes_copy_active_socket(context):
    tree = find_active_node_tree(context)

    active_socket = tree.interface.active
    tree.interface.copy(active_socket)

def nodes_assign_image_space(context):
    sei_vars = context.scene.sei_variables
    color_space = sei_vars.image_color_space

    for node in context.selected_nodes:
        if node.type == 'TEX_IMAGE':
            if node.image.alpha_mode != 'CHANNEL_PACKED':
                node.image.alpha_mode = 'CHANNEL_PACKED'

            node.image.colorspace_settings.name = color_space