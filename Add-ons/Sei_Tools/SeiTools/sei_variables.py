import bpy
from bpy.props import PointerProperty, EnumProperty, BoolProperty # https://docs.blender.org/api/current/bpy.props.html

class SEI_variables(bpy.types.PropertyGroup):

    # Rig Tools
    armature: PointerProperty(name="Armature", type=bpy.types.Object)

    # Node Tools
    image_color_space: EnumProperty(
        name = 'Colour Space',
        description = 'Image colour space to use on the node(s)',
        items = [ # (identifier, name, description)
            ('sRGB', 'sRGB', ''),
#            ('Linear', 'Linear', ''),
            ('Non-Color', 'Non-Color', ''),
        ]
    )

#=========

def register():
    bpy.utils.register_class(SEI_variables)
    bpy.types.Scene.sei_variables = bpy.props.PointerProperty(type=SEI_variables)

def unregister():
    bpy.utils.unregister_class(SEI_variables)
    del bpy.types.Scene.sei_variables