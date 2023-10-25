import bpy
from bpy.types import Panel

# Global panel UI properties.
class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UmU'

#Create mesh tools UI panel.
class SEI_PT_MeshTools(SeiPanel, Panel):
    bl_label = 'Mesh Tools'
    bl_idname = 'SEI_PT_meshtools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass

# Create modifiers UI subpanel.
class SEI_PT_Modifiers(SeiPanel, Panel):
    bl_label = 'Modifiers'
    bl_idname = 'SEI_PT_modifiers'
    bl_parent_id = 'SEI_PT_meshtools'
#    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.operator('sei.add_armature_modifier', text='Armature', icon='MOD_ARMATURE')
        row.operator('sei.remove_armature_modifier', text='', icon='REMOVE')

        row = layout.row()
        row.operator('sei.add_mask_modifier', text='Mask', icon='MOD_MASK')
        row.operator('sei.remove_mask_modifier', text='', icon='REMOVE')
        
        row = layout.row()
        row.operator('sei.add_smoothc_modifier', text='Smooth Corrective', icon='MOD_SMOOTH')
        row.operator('sei.remove_smoothc_modifier', text='', icon='REMOVE')


# Create subdivision UI subpanel.
class SEI_PT_Subdivision(SeiPanel, Panel):
    bl_label = 'Subdivision'
    bl_parent_id = 'SEI_PT_modifiers'
#    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        vars = context.scene.sei_variables
        
        row = self.layout.row()
        row.operator('sei.add_subsurf_modifier', text='Subdivision', icon='MOD_SUBSURF')
        row.operator('sei.remove_subsurf_modifier', text='', icon='REMOVE')
        col = self.layout.column(align=True)
        col.prop(vars, 'subsurf_viewport', text='Viewport')
        col.prop(vars, 'subsurf_render', text='Render')

# ===========================

classes = [
    SEI_PT_MeshTools,
    SEI_PT_Modifiers,
    SEI_PT_Subdivision,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)