import bpy
#from bpy.props import EnumProperty, IntProperty, FloatProperty, PointerProperty, BoolProperty, StringProperty
from bpy.props import PointerProperty, IntProperty, EnumProperty, BoolProperty

class SEI_variables(bpy.types.PropertyGroup):

    # Rig Tools
    armature: PointerProperty(name="Armature", type=bpy.types.Object)

    # Bone Properties
    rig_types: EnumProperty(
        name = 'Rig Types',
        items = [
            ('spine', 'Spine_Blenrig.ik', ''),
            ('head', 'Head', ''),
            ('armL', 'Arm_L.ik', ''),
            ('armR', 'Arm_R.ik', ''),
            ('legL', 'Leg_L.ik', ''),
            ('legR', 'Leg_R.ik', ''),
            ('finger', 'Finger', ''),
            (' ', '--- --- ---', ''),
            ('super_copy', 'Super_Copy', ''),
            ('chain', 'Stretchy_Chain', ''),
            ('tail', 'Tail', ''),
#            ('', '', ''),
        ]
    )

    # Scene Tools
    simplify_v_subsurf: BoolProperty(name='Simplify subsurf in Viewport', default=True)
    simplify_r_subsurf: BoolProperty(name='Simplify subsurf in Render', default=True)
    simplify_v_nodes: BoolProperty(name='Simplify geonodes in Viewport')
    simplify_r_nodes: BoolProperty(name='Simplify geonodes in Render', default=True)
    simplify_v_mask: BoolProperty(name='Simplify mask in Viewport')
    simplify_r_mask: BoolProperty(name='Simplify mask in Render', default=True)
    simplify_v_armature: BoolProperty(name='Simplify armature in Viewport')
    simplify_r_armature: BoolProperty(name='Simplify armature in Render', default=True)
    simplify_v_dtransfer: BoolProperty(name='Simplify dtransfer in Viewport')
    simplify_r_dtransfer: BoolProperty(name='Simplify dtransfer in Render', default=True)
    simplify_v_csmooth: BoolProperty(name='Simplify csmooth in Viewport')
    simplify_r_csmooth: BoolProperty(name='Simplify csmooth in Render', default=True)
    simplify_v_shrinkwrap: BoolProperty(name='Simplify shrinkwrap in Viewport')
    simplify_r_shrinkwrap: BoolProperty(name='Simplify shrinkwrap in Render', default=True)

#=========

def register():
    bpy.utils.register_class(SEI_variables)
    bpy.types.Scene.sei_variables = bpy.props.PointerProperty(type=SEI_variables)

def unregister():
    bpy.utils.unregister_class(SEI_variables)
    del bpy.types.Scene.sei_variables