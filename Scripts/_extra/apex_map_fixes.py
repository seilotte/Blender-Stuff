import bpy

#1 Dedup materials.
for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    
    for mat_slot in obj.material_slots:
        split_mat_name = mat_slot.name.split('.')
        if len(split_mat_name) > 1:

            # Check for orginal material.
            org_mat = bpy.data.materials.get(split_mat_name[0])
            if org_mat is None:
                print(f"Error: Material '{split_mat_name[0]}' not found.")
                continue

            # Replace dupped material.
            dupped_mat_name = mat_slot.name
            mat_slot.material = org_mat

for material in bpy.data.materials: # Remove dupped materials.
    split_mat_name = mat_slot.name.split(',')
    if len(split_mat_name) > 1:
        print(f'Removed: "{material.name}"')
        bpy.data.material.remove(material, do_unlink=True)


#1.1 Make selected object have all materials.
obj = bpy.context.active_object
if obj.type == 'MESH':
    for mat in bpy.data.materials:
        if mat.name == 'Dots Stroke': continue
        obj.data.materials.append(mat)


#1.2 Change "Specular BSDF" -> Group node.
for material in bpy.data.materials:
    if material.use_nodes:
        mat_tree = material.node_tree

        for node in mat_tree.nodes:
            if node.bl_idname == 'ShaderNodeEeveeSpecular':
                # Add new node.
                new_node = mat_tree.nodes.new('ShaderNodeGroup')
                new_node.node_tree = bpy.data.node_groups['ASMinus']

                # Reconnect links.
                for link in mat_tree.links:
#                    print(link.from_node)
#                    print(link.from_socket)
#                    print(link.to_node)
#                    print(link.to_socket)
                    if link.to_socket == node.inputs['Base Color']:
                        mat_tree.links.new(link.from_socket, new_node.inputs['Albedo'])
                    elif link.to_socket == node.inputs['Specular']:
                        mat_tree.links.new(link.from_socket, new_node.inputs['Specular'])
                    elif link.to_socket == node.inputs['Roughness']:
                        mat_tree.links.new(link.from_socket, new_node.inputs['Glossiness'])
                        link.from_node.image.colorspace_settings.name = 'Non-Color'
                    elif link.to_socket == node.inputs['Transparency']:
                        mat_tree.links.new(link.from_socket, new_node.inputs['Alpha'])
                    elif link.to_socket == node.inputs['Normal']:
                        mat_tree.links.new(link.from_socket, new_node.inputs['Normal Map'])
                        link.from_node.image.colorspace_settings.name = 'Non-Color'

                mat_tree.nodes.remove(node)
                break

#1.2.1 Find desired group node and print material.
for material in bpy.data.materials:
    if material.use_nodes:
        mat_tree = material.node_tree
        
        for node in mat_tree.nodes:
            if node.bl_idname == 'ShaderNodeGroup':
                if node.node_tree.name == 'Apex Shader+.003':
                    print(material.name)



#1.3 Fix materials.
# Enable alpha hashed and backface culling,
# connect group node to ouput,
# change group node.

desired_group_name = "ASMinus"

for material in bpy.data.materials:
    material.use_backface_culling = True
    material.blend_method = "HASHED"
    material.shadow_method = "HASHED"

    if material.use_nodes:
        mat_tree = material.node_tree

        mat_out = None # Get material output.
        for node in mat_tree.nodes:
            if node.bl_idname == 'ShaderNodeOutputMaterial':
                mat_out = node
                break

        if mat_out:
            mat_out.target = 'ALL'
            if hasattr(mat_out.inputs, "items"): # Has inputs?
                for input_socket in mat_out.inputs:
                    if input_socket.is_linked: # Is connected?
                        for link in input_socket.links:
                            mat_tree.links.remove(link) # Remove.

            for node in mat_tree.nodes: # Connect to material output.
                if node.bl_idname == 'ShaderNodeGroup':
                    mat_tree.links.new(node.outputs[0], mat_out.inputs[0])
                    # Change to the desired node group.
                    node.node_tree = bpy.data.node_groups.get(desired_group_name)
                    break


#2 Fix "Map Meshes".
# We are taking advantage that this objects don't have modifiers,
# and that they at least have one material.
# Renames to material name.
for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    if obj.data.materials and not obj.modifiers:
        obj.name = obj.data.materials[0].name
        obj.data.name = obj.name

#2.1 Fix "Assets" collection.
for arm in bpy.data.objects:
    if arm.type != 'ARMATURE': continue
    if len(arm.name.split('.')) > 1: continue # Tmp fix.

    for child in arm.children:
        if child.type != 'MESH': continue
        # Rename
        child.name = arm.name[:-5]
        child.data.name = child.name

        # Remove modifier(s) and link to first collection.
        child.modifiers.clear()
        parent_collection = bpy.data.collections[arm.users_collection[0].name[:-5]]
        parent_collection.objects.link(child)

    # Remove armature and secondary collection.
#    print(arm.name)
    bpy.data.collections.remove(arm.users_collection[0], do_unlink=True)
    bpy.data.objects.remove(arm, do_unlink=True)