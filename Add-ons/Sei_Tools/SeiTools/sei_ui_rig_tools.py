import bpy
from bpy.types import Panel

# Global panel UI properties.
class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UmU'

# Create rigify tools UI panel.
class SEI_PT_RigTools(SeiPanel, Panel):
    bl_label = 'Rig Tools'
    bl_idname = 'SEI_PT_rigtools'

    def draw(self, context):
        vars = context.scene.sei_variables
        layout = self.layout

        row = layout.row(align=True)
        row.operator('sei.stick_in_front', text='Stick | In Front', icon='ARMATURE_DATA')
        row.operator('sei.initiate_rigify', text='init Rigify', icon_value=241)

        col = layout.column(align=True)
        col.prop(vars, 'armature', text='', icon='MOD_ARMATURE')
        col.operator('sei.assign_armature', text='Assign Armature', icon='DOT')

# Create bone properties UI subpanel
class SEI_PT_BoneProperites(SeiPanel, Panel):
    bl_label = 'Bone Properties'
    bl_parent_id = 'SEI_PT_rigtools'

    @classmethod
    def poll(cls, context):
        obj = context.object

        return obj and context.active_bone and obj.type == 'ARMATURE' \
            and obj.data.get("rig_id") is None

    def draw(self, context):
        vars = context.scene.sei_variables
        layout = self.layout

        layout.column(align=True).operator('sei.select_children', text='Select Children', icon='GROUP_BONE')
        col = layout.column(align=True)
        col.operator('sei.bone_parent', text='Parent bones', icon='BONE_DATA')
        col.operator('sei.tail_to_head', text='Tail to Head', icon='BONE_DATA')
        layout.column(align=True).operator('sei.add_rotation_constraint', text='Twist Bone', icon='CONSTRAINT_BONE')

        if context.object and context.object.type == 'ARMATURE':
            row = layout.row(align=True)
            row.prop(context.active_bone, 'use_connect', text="Connected")
            row.prop(context.active_bone,'use_deform', text="Deform")
            row.prop(context.object.data, 'show_axes', text="Axes")

        col = layout.column(align=True)
        col.prop(vars, 'rig_types', text='', icon='BONE_DATA')
        row = col.split(align=True)
        row.operator('sei.assign_rig_type', text="Assign Rig Type", icon='ADD')
        row.operator('sei.clear_rig_type', text='Clear Rig Type', icon='REMOVE')

        if context.object and context.object.type == 'ARMATURE':
            text = "Re-Generate Rig" if context.object.data.rigify_target_rig else "Generate Rig"
            layout.column().operator("pose.rigify_generate", text=text, icon='POSE_HLT')

# ===========================

classes = [
    SEI_PT_RigTools,
    SEI_PT_BoneProperites,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)