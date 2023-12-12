import bpy

from bpy.types import Operator, Panel
from .functions.armatures import *
from .functions.bones import *
from .functions.nodes import *
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

#========= Rig Tools

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
        row.operator('sei.stick_infront_wire', text='Stick | In Front | Wire', icon='ARMATURE_DATA')

        col = layout.column(align=True)
        col.prop(sei_vars, 'armature', text='', icon='MOD_ARMATURE')
        col.operator('sei.assign_armature', text='Assign Armature', icon='DOT')

#=== Bone Properites

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


class SEI_PT_bone_properties(SeiPanel, Panel):
    bl_idname = 'SEI_PT_bone_properties'
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

#========= Node Tools

class SEI_OT_hide_socket_from_group_inputs(SeiOperator, Operator):
    bl_idname = 'sei.hide_sockets_group_inputs'
    bl_label = 'Fix Group Inputs'
    bl_description = 'Toggle unused node socket from group input nodes'

    def execute(self, context):
        nodes_hide_sockets_from_group_inputs(context)
#        self.report({'INFO'}, "Fixed group inputs.")
        return {'FINISHED'}

class SEI_OT_assign_image_space(SeiOperator, Operator):
    bl_idname = 'sei.assign_image_space'
    bl_label = 'Assign Image Space'
    bl_description = 'Assign the desired image space to the selected image nodes'

    def execute(self, context):
        nodes_assign_image_space(context)
        return {'FINISHED'}


class SEI_PT_node_tools(Panel):
    bl_idname = 'SEI_PT_node_tools'
    bl_label = 'Node Tools'

    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Group"

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree

    def draw(self, context):
        sei_vars = context.scene.sei_variables
        layout = self.layout
        
        col = layout.column()
        col.operator('sei.hide_sockets_group_inputs', text='Fix Group Inputs', icon='NODE')

        layout.separator()

        col = layout.column(align=True)
        col.prop(sei_vars, 'image_color_space', text='', icon='IMAGE_RGB')
        col.operator('sei.assign_image_space', text='Assign Image Spaces', icon='NODE_SEL')

#========= Scene Tools

class SEI_OT_assign_view_layer_name(SeiOperator, Operator):
    bl_idname = 'sei.assign_view_layer_name'
    bl_label = 'Assign View Layer Name'

    def execute(self, context):
        scene_assign_view_layer_name()
        return {'FINISHED'}

class SEI_OT_toggle_object_wireframe(SeiOperator, Operator):
    bl_idname = 'sei.toggle_object_wireframe'
    bl_label = 'Toggle Object Wireframe'

    def execute(self, context):
        scene_toggle_object_wireframe(context)
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

        col = layout.column()
        col.operator("sei.assign_view_layer_name", text="Rename", icon='FILE_TEXT')
        col.operator("sei.toggle_object_wireframe", text="Wireframe", icon='MOD_WIREFRAME')

#=== Simplify

class SEI_PT_simplify(SeiPanel, Panel):
    bl_idname = 'SEI_PT_simpify'
    bl_label = 'Simplify'
    bl_parent_id = 'SEI_PT_scene_tools'

    def draw_header(self, context):
        self.layout.prop(context.scene.render, "use_simplify", text="")

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.split(align=True)
        row.label(text='Max Subsurf')
        row.prop(context.scene.render, "simplify_subdivision", text='')

        row = col.split(align=True)
        row.label(text='Texture Size Limit')
        row.prop(context.preferences.system, "gl_texture_limit", text='')

#=== Modifiers

class SEI_PT_modifiers(SeiPanel, Panel):
    bl_idname = 'SEI_PT_modifiers'
    bl_label = 'Modifiers'
    bl_parent_id = 'SEI_PT_scene_tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        all_modifiers = [(obj.name, mod) for obj in bpy.context.selected_objects if obj.type == 'MESH' for mod in obj.modifiers]
        sort_modifiers = set(sorted(all_modifiers, key=lambda x: (x[1].type, x[1].name))) # x[1] = mod
        del all_modifiers

        for obj_name, mod in sort_modifiers:
            row = col.row(align=True)
            row.label(text=f'{mod.name} | {obj_name}', icon_value=layout.icon(mod))

#            for prop in mod.bl_rna.properties: print(prop)
            row.prop(mod, 'show_viewport', icon_only=True)
            row.prop(mod, 'show_render', icon_only=True)

#===========================

classes = [
    # Rig Tools.
    SEI_OT_stick_infront_wire,
    SEI_OT_assign_armature,
    SEI_PT_rig_tools,
    # Rig Tools -> Bone Properties.
    SEI_OT_select_children,
    SEI_OT_bone_parent_offset,
    SEI_OT_tail_to_head_parent,
    SEI_PT_bone_properties,
    # Node Tools.
    SEI_OT_hide_socket_from_group_inputs,
    SEI_OT_assign_image_space,
    SEI_PT_node_tools,
    # Scene Tools. -> Simplify. -> Modifiers.
    SEI_OT_assign_view_layer_name,
    SEI_OT_toggle_object_wireframe,
    SEI_PT_scene_tools,
    SEI_PT_simplify,
    SEI_PT_modifiers,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)