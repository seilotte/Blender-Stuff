import bpy
#from bpy.props import EnumProperty, IntProperty, FloatProperty, PointerProperty, BoolProperty, StringProperty
from bpy.props import PointerProperty, EnumProperty, BoolProperty
from .functions.scene import *

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

    # Scene Tools
    simplify_v_armature: BoolProperty(name='Simplify armature in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_armature: BoolProperty(name='Simplify armature in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_subsurf: BoolProperty(name='Simplify subsurf in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_subsurf: BoolProperty(name='Simplify subsurf in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_mask: BoolProperty(name='Simplify mask in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_mask: BoolProperty(name='Simplify mask in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_nodes: BoolProperty(name='Simplify geonodes in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_nodes: BoolProperty(name='Simplify geonodes in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_solidify: BoolProperty(name='Simplify solidify in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_solidify: BoolProperty(name='Simplify solidify in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_dtransfer: BoolProperty(name='Simplify dtransfer in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_dtransfer: BoolProperty(name='Simplify dtransfer in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_csmooth: BoolProperty(name='Simplify csmooth in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_csmooth: BoolProperty(name='Simplify csmooth in Render', default=True, update=scene_simplify_modifiers_render)
    simplify_v_shrinkwrap: BoolProperty(name='Simplify shrinkwrap in Viewport', default=True, update=scene_simplify_modifiers_viewport)
    simplify_r_shrinkwrap: BoolProperty(name='Simplify shrinkwrap in Render', default=True, update=scene_simplify_modifiers_render)

#=========

def register():
    bpy.utils.register_class(SEI_variables)
    bpy.types.Scene.sei_variables = bpy.props.PointerProperty(type=SEI_variables)

def unregister():
    bpy.utils.unregister_class(SEI_variables)
    del bpy.types.Scene.sei_variables