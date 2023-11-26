import bpy

#class SEI_OT_move_sockets(bpy.types.Operator):
#    bl_idname = 'sei.move_sockets'
#    bl_label = 'Assign Image Space'
#    bl_description = 'Move sockets up or down.'

#    bl_region_type = 'UI'
#    bl_options = {'REGISTER', 'UNDO'}

#    direction = "UP"

#    def execute(self, context):

#        tree = context.space_data.node_tree
#        if tree.nodes.active: # Check recursively until we find the tree.
#            while tree.nodes.active != context.active_node:
#                tree = tree.nodes.active_node_tree

#                active_socket_index = tree.interface.active_index
#                active_socket = tree.interface.items_tree[active_socket_index]

#                # Direction.
#                index = active_socket_index - 1
#                a_index = active_socket_index - 1
#                if self.direction != 'UP':
#                    index = active_socket_index + 2 # Why 2, bug?
#                    a_index = active_socket_index + 1

#                target_socket = tree.interface.items_tree[index]

#                # Check that the sockets are the same and move them.
#                if active_socket.item_type == target_socket.item_type:
#                    if active_socket.item_type == 'UP':
#                        tree.interface.move(active_socket, index)
#                        tree.interface.active_index = a_index
#                    elif active_socket.in_out == target_socket.in_out: # Inputs/Outpus.
#                        tree.interface.move(active_socket, index)
#                        tree.interface.active_index = a_index

#        return {'FINISHED'}

obj = bpy.context.active_object
mat = obj.active_material

direction = "DOWN"

tree = mat.node_tree.nodes['Group']
tree = tree.node_tree


active_socket_index = tree.interface.active_index
active_socket = tree.interface.items_tree[active_socket_index]

index = active_socket_index - 1
a_index = active_socket_index - 1
if direction != 'UP':
    index = active_socket_index + 2 # Why +2?
    a_index = active_socket_index + 1

target_socket = tree.interface.items_tree[index]

if active_socket.item_type == target_socket.item_type:
    if active_socket.item_type == 'PANEL':
        tree.interface.move(active_socket, index)
        tree.interface.active_index = a_index
    elif active_socket.in_out == target_socket.in_out:
        tree.interface.move(active_socket, index)
        tree.interface.active_index = a_index