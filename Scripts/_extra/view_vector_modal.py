import bpy
import mathutils

class ViewDirectionUpdater(bpy.types.Operator):
    """Update the combine xyz node with the current view direction"""
    bl_idname = "view_direction_updater.modal_operator"
    bl_label = "View Direction Updater"

    _timer = None

    def modal(self, context, event):
        
        if event.type == 'ESC':
            print("Stopped vv.")
            return {'CANCELLED'}

        if event.type == 'TIMER':

            # Get the 3D Viewport area and space
            area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
            space = area.spaces.active

            # Get the view matrix of the 3D viewport
            view_matrix = space.region_3d.view_matrix

            # Get the View_3d vector from the view matrix
            view_vector = mathutils.Vector((view_matrix[2][0], view_matrix[2][1], view_matrix[2][2]))

            # Print the View_3d vector
            print("View_3d vector:", view_vector)

#            if bpy.context.active_object.active_material is not None:
#                # Create viewing vector node.
#                if "vv" not in bpy.context.active_object.active_material.node_tree.nodes:
#                    xyz_node = bpy.context.active_object.active_material.node_tree.nodes.new(type='ShaderNodeCombineXYZ')
#                    xyz_node.name = "vv"
#                    xyz_node.label = "View Vector"
#                else:
#                    xyz_node = bpy.context.active_object.active_material.node_tree.nodes.get("vv")
#                    # Get the combine xyz node and set its XYZ values.
#                    if xyz_node is not None:
#                        xyz_node.inputs[0].default_value = view_vector.x
#                        xyz_node.inputs[1].default_value = view_vector.y
#                        xyz_node.inputs[2].default_value = view_vector.z


            obj = bpy.context.active_object
#            xyz_node = obj.active_material.node_tree.nodes.get("vv")
            xyz_node = obj.modifiers["GeometryNodes"].node_group.nodes.get("vv")

            if xyz_node is not None:
                xyz_node.inputs[0].default_value = view_vector.x
                xyz_node.inputs[1].default_value = view_vector.y
                xyz_node.inputs[2].default_value = view_vector.z

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def register():
    bpy.utils.register_class(ViewDirectionUpdater)

def unregister():
    bpy.utils.unregister_class(ViewDirectionUpdater)

if __name__ == "__main__":
    register()
