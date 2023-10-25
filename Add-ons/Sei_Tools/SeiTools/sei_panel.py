import bpy
from bpy.types import Panel

# Global panel UI properties.
class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UmU'

# Create omo test UI panel.
class SEI_PT_omo(SeiPanel, Panel):
    bl_label = 'aheago'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        pass

# ===========================

def register():
    bpy.utils.register_class(SEI_PT_omo)

def unregister():
    bpy.utils.unregister_class(SEI_PT_omo)