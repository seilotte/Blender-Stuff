import bpy
    
#Panel UI
class seiPANEL_UI(bpy.types.Panel):
    bl_label = "Juice"
    bl_idname = "sei_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UwU"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        
        layout = self.layout
        
        #create simple row
        row = layout.row()
        row.label(text = "Create Buttons:")
        
        #add custom buttons
        row = layout.row()
        row.scale_y = 2
        row.operator("render.render", text = "Button1")
        row.operator("render.render", text = "Button2")
        
class seiPANEL_UI2(bpy.types.Panel):
    bl_label = "Rigify_Tools"
    bl_idname = "sei_Panel2"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UwU"
    bl_parent_id = 'sei_Panel'
    
    def draw(self, context):
        
        layout = self.layout
        
        row = layout.row()
        row.label(text = "Create Buttons:")
        row.operator("render.render", text = "Button3")

        
#Register
def register():
    bpy.utils.register_class(seiPANEL_UI)
    bpy.utils.register_class(seiPANEL_UI2)
    
def unregister():
    bpy.utils.unregister_class(seiPANEL_UI)
    bpy.utils.register_class(seiPANEL_UI2)

if __name__ == "__main__":
    register()