import bpy

vars = bpy.context.scene.sei_variables
all = bpy.context.selected_objects

color_space = vars.image_spaces

for obj in all:
    if obj.type != 'MESH':
        continue
    
    for mat in obj.data.materials:
        if mat.use_nodes == True:
            for node in mat.node_tree.nodes:
                if node.bl_idname == 'ShaderNodeTexImage':
                    if node.image.alpha_mode != 'CHANNEL_PACKED':
                        node.image.alpha_mode = 'CHANNEL_PACKED'
                    
                    if vars.all_images:
                        node.image.colorspace_settings.name = color_space
                    elif node.select:
                        node.image.colorspace_settings.name = color_space