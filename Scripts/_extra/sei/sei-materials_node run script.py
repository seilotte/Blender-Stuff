'''
WIP
Its impossible to get the value of a socket.
Use "ShaderNodeCustomGroup", which are node groups with a fancy UI.
'''

import bpy
import os
import nodeitems_builtins
import nodeitems_utils

from nodeitems_utils import NodeCategory, NodeItem
from bpy.types import Node, ShaderNodeCustomGroup, NodeSocket

# Category menu.
sei_shader_category = NodeCategory(
    "SEI_SHADER_CATEGORY",
    "Sei Nodes",
    items=[
        NodeItem("SeiShaderNodeScript")
    ]
)


class SEI_OT_node_run_script(bpy.types.Operator):
    bl_idname = 'sei.node_run_script'
    bl_label = 'Run Node Script'
    bl_description = 'Run active script'

    @classmethod
    def poll(cls, context):
        node = context.active_node
        if not node:
            return False
        if hasattr(node, 'type_prop'):
            if node.type_prop == 'Internal':
                return hasattr(node, 'internal_prop') and bool(node.internal_prop)
            else:
                return hasattr(node, 'external_prop') and bool(node.external_prop)
        return False


    def execute(self, context):
        node = context.active_node

        try:
            if node.type_prop == 'Internal':
                script = node.internal_prop
                glsl_file = bpy.path.abspath(script.filepath)

                if script.is_in_memory or script.is_dirty or script.is_modified or not os.path.exists(glsl_file):
                    glsl_file = script.as_string()
                    exec(glsl_file)
            else:
                script_path = bpy.path.abspath(node.external_prop)
    #            script_path_noext, script_ext = os.path.splitext(script_path)

    #            if script_ext == '.glsl' or script_ext == '.py':
                with open(script_path, 'r') as file:
                    script = file.read()
                exec(script)
        except Exception as e:
            self.report({'ERROR'}, f'Failed to run script; *{str(e)}*')

        return {'FINISHED'}


class SEI_NODE_script(Node):
    bl_idname = 'SeiShaderNodeScript'
    bl_label = "Script OwO"

    # Node properties.
    type_prop: bpy.props.EnumProperty(
        name = 'Sei Script Type',
        items = [('Internal', 'Internal', 'Use internal text data-block.'), # (identifier, name, description)
                ('External', 'External', 'Use external .glsl file.')],
    )

    internal_prop: bpy.props.PointerProperty(
    type = bpy.types.Text,
    name = 'Script',
    description = 'Internal shader script to define the shader.',
    )

    external_prop: bpy.props.StringProperty(
    subtype = 'FILE_PATH',
    name = 'File Path',
    description = 'Shader Script Path',
#    default = '//'
    )


    def draw_buttons(self, context, layout):
        layout.prop(self, 'type_prop', text='.', expand=True)

        row = layout.row(align=True)
        if self.type_prop == 'Internal':
            row.prop(self, 'internal_prop', text='')
        else:
            row.prop(self, 'external_prop', text='')
        row.operator('sei.node_run_script', text='', icon='PLAY')


#    def init(self, context):

#    def update(self):
        # Sockets
        # Check for socket inputs.
        # Function

    # Free function to clean up on removal.
    def free(self):
#        print(f'Removing node {self}.')
        pass

#=========

def register():
    bpy.utils.register_class(SEI_NODE_script)
    bpy.utils.register_class(SEI_OT_node_run_script)

    if "SEI_SHADERS" in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SEI_SHADERS")
    nodeitems_utils.register_node_categories("SEI_SHADERS", [sei_shader_category])

def unregister():
    bpy.utils.unregister_class(SEI_NODE_script)
    bpy.utils.unregister_class(SEI_OT_node_run_script)

    nodeitems_utils.unregister_node_categories("SEI_SHADERS")

if __name__ == "__main__":
    register()