import bpy

class Sei_OT_FixGroupInputs(bpy.types.Operator):
    bl_label = "Fix Group Inputs"
    bl_idname = "sei.fix_group_inputs"
    bl_description = 'Toggle unused node sockets from "Group Inputs"'

    def execute(self, context):
        tree = context.space_data.node_tree
        if tree.nodes.active: # Check recursively until we find the tree.
            while tree.nodes.active != context.active_node:
                tree = tree.nodes.active.node_tree

                for node in tree.nodes:
                    if node.type != 'GROUP_INPUT': continue
#                    print(f'{node.name} + {node.type}')
                    if node.mute: continue

                    for socket in node.outputs:
                        socket.hide = True

#        self.report({'INFO'}, "Fixed group inputs.")
        return {'FINISHED'}

def draw_operator_button(self, context):
    layout = self.layout
    layout.operator("sei.fix_group_inputs", text="Fix Group Inputs")

def register():
    bpy.utils.register_class(Sei_OT_FixGroupInputs)
    bpy.types.NODE_PT_node_tree_interface_inputs.append(draw_operator_button)

def unregister():
    bpy.utils.unregister_class(Sei_OT_FixGroupInputs)
    bpy.types.NODE_PT_node_tree_interface_inputs.remove(draw_operator_button)

if __name__ == "__main__":
    register()