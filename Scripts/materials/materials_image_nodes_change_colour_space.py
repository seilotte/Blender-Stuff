import bpy

#count = 0
for mat in bpy.data.materials:
    if mat.use_nodes == True:
        nodes = mat.node_tree.nodes

        for node in nodes:
            if node.bl_idname == 'ShaderNodeTexImage':
#                    node.image.colorspace_settings.name = 'Non-Color'
                    node.image.alpha_mode = 'CHANNEL_PACKED'

#                    count = count + 1
#print("Total changes made:", count)