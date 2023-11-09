'''
WIP.
Its impossible to get the value of a socket.
Use "ShaderNodeCustomGroup", which are node groups with a fancy UI.
'''

import bpy
import nodeitems_builtins
import nodeitems_utils

from nodeitems_utils import NodeCategory, NodeItem
from bpy.types import Node, ShaderNodeCustomGroup, NodeSocket

# Category menu.
sei_shader_category = NodeCategory(
    "SEI_SHADER_CATEGORY",
    "Sei Nodes",
    items=[
        NodeItem("SeiShaderNodeLerp")
    ]
)


class SEI_NODE_lerp(Node):
#    https://docs.blender.org/api/current/bpy.types.Node.html
#    https://docs.blender.org/api/current/bpy.types.ShaderNodeCustomGroup.html
    bl_idname = 'SeiShaderNodeLerp'
    bl_label = "Lerp"

    def init(self, context):
#        https://docs.blender.org/api/current/bpy.types.NodeSocketStandard.html
#        https://docs.blender.org/api/current/bpy.types.NodeSocket.html
#        https://docs.blender.org/api/master/bpy.types.NodeTreeInterfaceSocket.html#bpy.types.NodeTreeInterfaceSocket
        self.inputs.new('NodeSocketBool', 'Clamp Result').default_value = False
        self.inputs.new('NodeSocketBool', 'Clamp Factor').default_value = False
        self.inputs.new('NodeSocketFloatFactor', 'Factor').default_value = 0.5
        self.inputs.new('NodeSocketFloat', 'A')
        self.inputs.new('NodeSocketFloat', 'B')

        self.outputs.new('NodeSocketFloat', 'Result')

    def update(self):
        # Sockets
        clamp_result = self.inputs['Clamp Result']
        clamp_factor = self.inputs['Clamp Factor']
        fac = self.inputs['Factor']
        a = self.inputs['A']
        b = self.inputs['B']

        r = self.outputs['Result']

        # Check for socket inputs.
        fac = fac.links[0].from_socket if fac.is_linked else fac.default_value
        a = a.links[0].from_socket if a.is_linked else a.default_value
        b = b.links[0].from_socket if b.is_linked else b.default_value

        # Function
        if clamp_factor.default_value:
            fac = max(0.0, min(fac, 1.0))

        result = a + (b - a) * fac

        if clamp_result.default_value:
#            result = max(a, min(result, b))
            result = max(0.0, min(result, 1.0))

        self.outputs['Result'].default_value = result

    # Free function to clean up on removal.
    def free(self):
#        print(f'Removing node {self}.')
        pass

#=========

def register():
    bpy.utils.register_class(SEI_NODE_lerp)

    if "SEI_SHADERS" in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SEI_SHADERS")
    # ...insert(category_name, items[], label=category_label)
#    https://github.com/blender/blender/blob/main/scripts/templates_py/custom_nodes.py
    nodeitems_utils.register_node_categories("SEI_SHADERS", [sei_shader_category])

def unregister():
    bpy.utils.unregister_class(SEI_NODE_lerp)

    nodeitems_utils.unregister_node_categories("SEI_SHADERS")

if __name__ == "__main__":
    register()