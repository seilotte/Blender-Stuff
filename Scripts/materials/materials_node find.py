def find_node(node, node_type):
    if node.type == node_type:
        return node

    for input in node.inputs:
        if input.is_linked:
            for link in input.links:
                if (n := find_node(link.from_node, node_type)):
                    return n

    return None

def find_node_label(node_label, start_tree):
    for node in start_tree.nodes:
        if node.type != 'FRAME' and node.label == node_label:
            return node

        if hasattr(node, 'node_tree'):
            if (node := find_node_label(node_label, node.node_tree)):
                return node

    return None