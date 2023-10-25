import bpy

from bpy.types import Operator, Panel
from .functions.armatures import *
from .functions.bones import *
from .functions.scene import *

# Global panel UI properties.
class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

# Global OT properties.
class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

###===Rig Tools===

class SEI_OT_stick_infront_wire(SeiOperator, Operator):
    bl_idname = 'sei.stick_infront_wire'
    bl_label = "Armatures Stick, In Front, Wire"
    bl_description = 'Make the selected armatures display as "Stick", "In-Front" and "Wire"'

#    @classmethod
#    def poll(cls, context):
#        return context.object

    def execute(self, context):
        armature_stick_infront_wire(context)
        return {'FINISHED'}

class SEI_OT_iniatie_rigify_layers(SeiOperator, Operator):
    bl_idname = 'sei.initiate_rigify_layers'
    bl_label = "Initiate Rigify Layers"
    bl_description = "Set-up rigify layers in the selected armatures"

    def execute(self, context):
        armature_initiate_rigify_layers(context)
        return {'FINISHED'}

# Assign armature.
class SEI_OT_assign_armature(SeiOperator, Operator):
    bl_idname = 'sei.assign_armature'
    bl_label = 'Assign Armature'
    bl_description = 'Assign the indicated armature to the selected meshes'

    def execute(self, context):
        armature_assign(context)
        return{'FINISHED'}


class SEI_PT_rig_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_rig_tools'
    bl_label = 'Rig Tools'

    def draw(self, context):
        sei_vars = context.scene.sei_variables
        layout = self.layout

        row = layout.row(align=True)
        row.operator('sei.stick_infront_wire', text='Stick|In Front|Wire', icon='ARMATURE_DATA')
        row.operator('sei.initiate_rigify_layers', text='Init Rigify', icon_value=241)

        col = layout.column(align=True)
        col.prop(sei_vars, 'armature', text='', icon='MOD_ARMATURE')
        col.operator('sei.assign_armature', text='Assign Armature', icon='DOT')

#===Bone Properites===

class SEI_OT_select_children(SeiOperator, Operator):
    bl_idname = 'sei.select_children'
    bl_label = 'Select Children'
    bl_description = 'Select child bones'

    def execute(self, context):
        bone_select_children(context)
        return{'FINISHED'}

class SEI_OT_bone_parent_offset(SeiOperator, Operator):
    bl_idname = 'sei.bone_parent_offset'
    bl_label = 'Assign Parent - Offset'
    bl_description = 'Assign parent with offset'

    def execute(self, context):
        bone_parent_offset(context)
        return{'FINISHED'}

class SEI_OT_tail_to_head_parent(SeiOperator, Operator):
    bl_idname = 'sei.tail_to_head_parent'
    bl_label = 'Tail to Head - Parent'
    bl_description = 'Move parent tail to child head'

    def execute(self, context):
        bone_tail_to_head_parent(context)
        return{'FINISHED'}

class SEI_OT_assign_rig_type(SeiOperator, Operator):
    bl_idname = 'sei.assign_rig_type'
    bl_label = 'Assign Rig Type'

    @classmethod # If it is not an armature or in pose mode, disable.
    def poll(self, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE' \
            and context.active_object.mode == 'POSE'

    def execute(self, context):
        bone_assign_rig_type(context)
        return {'FINISHED'}

class SEI_OT_remove_rig_type(SeiOperator, Operator):
    bl_idname = 'sei.remove_rig_type'
    bl_label = 'Remove Rig Type'

    @classmethod # If it is not an armature or in pose mode, disable.
    def poll(self, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE' \
            and context.active_object.mode == 'POSE'

    def execute(self, context):
        bone_remove_rig_type(context)
        return {'FINISHED'}


class SEI_PT_bone_properties(SeiPanel, Panel):
    bl_label = 'Bone Properties'
    bl_parent_id = 'SEI_PT_rig_tools'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and context.active_bone and obj.type == 'ARMATURE'

    def draw(self, context):
        sei_vars = context.scene.sei_variables
        layout = self.layout

        layout.column(align=True).operator('sei.select_children', text='Select Children', icon='GROUP_BONE')
        col = layout.column(align=True)
        col.operator('sei.bone_parent_offset', text='Parent bone', icon='BONE_DATA')
        col.operator('sei.tail_to_head_parent', text='Tail to Head', icon='BONE_DATA')

        row = layout.row(align=True)
        row.prop(context.active_bone, 'use_connect', text="Connected")
        row.prop(context.active_bone,'use_deform', text="Deform")
        row.prop(context.object.data, 'show_axes', text="Axes")

        col = layout.column(align=True)
        col.prop(sei_vars, 'rig_types', icon='BONE_DATA', icon_only=True)
        row = col.split(align=True)
        row.operator('sei.assign_rig_type', text="Assign Rig Type", icon='ADD')
        row.operator('sei.remove_rig_type', text='Clear Rig Type', icon='REMOVE')

###===Scene Tools===

class SEI_OT_hide_socket_from_group_inputs(SeiOperator, Operator):
    bl_idname = 'sei.hide_sockets_group_inputs'
    bl_label = 'Fix Group Inputs'
    bl_description = 'Toggle unused node socket from group input nodes'


    def execute(self, context):
        scene_hide_sockets_from_group_inputs(context)
#        self.report({'INFO'}, "Fixed group inputs.")
        return {'FINISHED'}

def sei_button_hide_socket_from_group_inputs(self, context):
    layout = self.layout
    layout.operator('sei.hide_sockets_group_inputs', text='Fix Group Inputs', icon='NODE')

# Original code, therefore the same license applies.
# https://github.com/Lateasusual/blender-collection-simplify
class SEI_OT_simplify_modifiers(SeiOperator, Operator):
    bl_idname = 'sei.simplify_modifiers'
    bl_label = 'Simplify Modifiers'
    bl_descriptions = 'Show/Hide all modifiers of objects.'

    @classmethod
    def poll(cls, context):
        return context.scene

    modifier_properties = {
        'SUBSURF': ('simplify_v_subsurf', 'simplify_r_subsurf', 'MOD_SUBSURF'),
        'NODES': ('simplify_v_nodes', 'simplify_r_nodes', 'GEOMETRY_NODES'),
        'MASK': ('simplify_v_mask', 'simplify_r_mask', 'MOD_MASK'),
        'ARMATURE': ('simplify_v_armature', 'simplify_r_armature', 'MOD_ARMATURE'),
        'DATA_TRANSFER': ('simplify_v_dtransfer', 'simplify_r_dtransfer', 'MOD_DATA_TRANSFER'),
        'CORRECTIVE_SMOOTH': ('simplify_v_csmooth', 'simplify_r_csmooth', 'MOD_SMOOTH'),
        'SHRINKWRAP': ('simplify_v_shrinkwrap', 'simplify_r_shrinkwrap', 'MOD_SHRINKWRAP'),
    }

    def execute(self, context):
        scene_simplify_modifiers(self, context)
        return {'FINISHED'}


class SEI_PT_scene_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_scene_tools'
    bl_label = 'Scene Tools'

    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
        'BLENDER_WORKBENCH_NEXT'}

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        sei_vars = context.scene.sei_variables
        layout = self.layout

        col = layout.column(align=True)
        col.prop(context.scene.render, "use_simplify", text="Simplify")
        row = col.split(factor=0.4, align=True)
        row.label(text='Max Subsurf')
        row.prop(context.scene.render, "simplify_subdivision", icon='RESTRICT_VIEW_OFF', icon_only=True)

        layout.separator()

        col = layout.column()
        for mod_type, (viewport_prop, render_prop, icon_name) in SEI_OT_simplify_modifiers.modifier_properties.items():
            row = col.split(factor=0.4, align=True)
            row.label(text=mod_type, icon=icon_name)
            row.prop(sei_vars, viewport_prop, icon='RESTRICT_VIEW_OFF', icon_only=True)
            row.prop(sei_vars, render_prop, icon='RESTRICT_RENDER_OFF', icon_only=True)

        layout.separator()

        op = layout.operator("sei.simplify_modifiers", text="Reload", icon='FILE_REFRESH')

#===========================

classes = [
    # Rig Tools.
    SEI_OT_stick_infront_wire,
    SEI_OT_iniatie_rigify_layers,
    SEI_OT_assign_armature,
    SEI_PT_rig_tools,
    # Rig Tools -> Bone Properties.
    SEI_OT_select_children,
    SEI_OT_bone_parent_offset,
    SEI_OT_tail_to_head_parent,
    SEI_OT_assign_rig_type,
    SEI_OT_remove_rig_type,
    SEI_PT_bone_properties,
    # Scene Tools.
    SEI_OT_hide_socket_from_group_inputs,
    SEI_OT_simplify_modifiers,
    SEI_PT_scene_tools,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.NODE_PT_node_tree_interface_inputs.append(sei_button_hide_socket_from_group_inputs)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.NODE_PT_node_tree_interface_inputs.remove(sei_button_hide_socket_from_group_inputs)