import bpy

class SEI_PT_object_type_visibility(bpy.types.Panel):
    bl_idname = 'SEI_PT_object_type_visibility'
    bl_label = "View Object Types"

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

    def draw(self, context):
        layout = self.layout

        object_types = [
            ('ARMATURE', 'Armature', 'ARMATURE_DATA'),
            ('EMPTY', 'Empty', 'EMPTY_DATA'),
            ('LIGHT', 'Light', 'LIGHT'),
            ('MESH', 'Mesh', 'MESH_DATA'),
        ]

        col = layout.column()

        for obj_type, name, icon in object_types:
            any_visible = any(obj.hide_viewport == False for obj in context.scene.objects if obj.type == obj_type)

            row = col.split(factor=0.5, align=True)
            row.label(text=name, icon=icon)

            row.operator(
                "sei.toggle_visibility",
                text = '',
                icon = 'RESTRICT_VIEW_OFF' if any_visible else 'RESTRICT_VIEW_ON',
            ).object_type = obj_type


class SEI_OT_toggle_visibility(bpy.types.Operator):
    bl_idname = "sei.toggle_visibility"
    bl_label = "Toggle visibility based on the objects type"
    bl_options = {'REGISTER', 'UNDO'}

    object_type: bpy.props.StringProperty(default='MESH')

    def execute(self, context):

        for obj in context.scene.objects:
            if obj.type == self.object_type:
                obj.hide_viewport = not obj.hide_viewport

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SEI_PT_object_type_visibility)
    bpy.utils.register_class(SEI_OT_toggle_visibility)

def unregister():
    bpy.utils.unregister_class(SEI_PT_object_type_visibility)
    bpy.utils.unregister_class(SEI_OT_toggle_visibility)

if __name__ == "__main__":
    register()