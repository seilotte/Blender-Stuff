import bpy
from bpy.types import Panel

# Global panel UI properties.
class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UmU'

# Create data tools UI panel.
class SEI_PT_DataTools(SeiPanel, Panel):
    bl_label = 'Data Tools'
    bl_idname = 'SEI_PT_datatools'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        pass

# Create nodes data UI subpanel.
class SEI_PT_NodesData(SeiPanel, Panel):
    bl_label = 'Nodes Data'
#    bl_idname = 'SEI_PT_nodesdata'
    bl_parent_id = 'SEI_PT_datatools'
#    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        vars = context.scene.sei_variables
        layout = self.layout
        
        col = layout.column(align=True)
        row = col.split(factor=0.7)
        
        row.prop(vars, 'image_spaces', text='Space')
        row.prop(vars, 'all_images')
        col.operator('sei.assign_image_space', text='Assign Image Spaces', icon='DOT')

# ===========================

classes = [
    SEI_PT_DataTools,
    SEI_PT_NodesData,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()