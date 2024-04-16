# I belive the one inside AswTools is a better version.
import bpy

oname = bpy.context.active_object.name

#Duplicate mesh
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.duplicate()

#Merge by distance
bool = False
if bool == True:
    bpy.ops.mesh.remove_doubles(use_sharp_edge_from_normals=True)
else:
    bpy.ops.mesh.remove_doubles()

bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.editmode_toggle()

if bpy.context.selected_objects != []:
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            str = obj.name
            if str > oname:
                str = obj.name[:4]
                obj.name = str+"_outline"
                
                #Add material
                obj.data.materials.clear()
                mat_out = bpy.data.materials.get("vOutline") or bpy.data.materials.new(name = "vOutline")
                mat_out.use_nodes = True
                mat_out.use_backface_culling = True
                mat_out.shadow_method = 'NONE'

                obj.active_material = mat_out

                material_output = mat_out.node_tree.nodes.get('Material Output')
                value_node = mat_out.node_tree.nodes.new('ShaderNodeValue')
                value_node.outputs[0].default_value = (0.021)

                mat_out.node_tree.links.new(value_node.outputs[0], material_output.inputs[0])
                    
                #Add Solidify
                sol = obj.modifiers.new("Solidify", 'SOLIDIFY')

                sol.offset = 0.0
                #sol.vertex_group = 'a'
                sol.thickness_vertex_group = .05
                sol.use_flip_normals = True
                sol.material_offset = 6
                sol.material_offset_rim = 6
                sol.thickness_clamp = 1.0