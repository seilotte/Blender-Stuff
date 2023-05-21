import bpy

for mat in bpy.data.materials:
    if mat.use_nodes == True:
        # Remove all nodes except material output.
        for node in mat.node_tree.nodes:
            if node.type != 'OUTPUT_MATERIAL':
                mat.node_tree.nodes.remove(node)

        mat_out_node = mat.node_tree.nodes.get('Material Output')
        value_node = mat.node_tree.nodes.new('ShaderNodeValue')
        value_node.ouptuts[0].default_vale = (0.021)

        # Link
        mat.node_tree.links.new(value_node.outputs[0], mat_out_node.inputs[0])

        # Remove principled bsdf.
#        if mat.node_tree.nodes['Principled BSDF']:
#            mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BSDF'])
#            mat.node_tree.nodes.remove(mat.node_ree.nodes.get('Principled BSDF'))