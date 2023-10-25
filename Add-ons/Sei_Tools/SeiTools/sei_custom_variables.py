import bpy
#from bpy.props import EnumProperty, IntProperty, FloatProperty, PointerProperty, BoolProperty, StringProperty
from bpy.props import PointerProperty, IntProperty, EnumProperty, BoolProperty

# Create custom variables.
class Sei_Variables(bpy.types.PropertyGroup):

    # Rig Tools
    armature: PointerProperty(name="Armature", type=bpy.types.Object)
    
    # Bone Properties
    rig_types: EnumProperty(
        name = 'Rig Types',
        description = 'Bone rig types',
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

    # Mesh Tools
    # Modifiers
    subsurf_viewport: IntProperty(name="Subsurf Viewport Level", default=0, min=0, max=3)
    subsurf_render: IntProperty(name="Subsurf Render Level", default=2, min=0, max=9)
    
    # Data Tools
    # Nodes Data
    all_images: BoolProperty(name='All?', description='Assign to all images')
    image_spaces: EnumProperty(
        name = 'Image Space',
        description = 'Image colour space',
        items = [ # Leave first with those names, we use them to set the colour space.
            ('sRGB', 'sRGB', ''),
            ('Linear', 'Linear', ''),
            ('Non-Color', 'Non-Color', ''),
        ]
    )

# ===========================

def register():
    bpy.utils.register_class(Sei_Variables)
    bpy.types.Scene.sei_variables = bpy.props.PointerProperty(type=Sei_Variables)

def unregister():
    bpy.utils.unregister_class(Sei_Variables)
    del bpy.types.Scene.sei_variables