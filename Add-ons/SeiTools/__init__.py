import bpy

from bpy.props import EnumProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

bl_info = {
    "name": "SeiTools",
    "author": "Seilotte",
    "version": (1, 3, 6),
    "blender": (4, 1, 0),
    "location": "3D View > Properties > Sei",
    "description": "Random collection of tools for my personal use",
    "doc_url": "seilotte.github.io",
    "tracker_url": "seilotte.github.io",
    "category": "Workflow", # 3D View
}

########################### Custom Variables

# scene.sei_variables

class SEI_variables(PropertyGroup):

    # Rig Tools
    armature: PointerProperty(name='Armature', type=bpy.types.Object)

    # Node Tools
    color_space: EnumProperty(
        name = 'Colour Space',
        description = 'Image colour space to use on the node(s)',
        items = [
            # (identifier, name, description, icon, bumber)
            ('sRGB', 'sRGB', ''),
            ('Non-Color', 'Non-Color', '')
        ]
    )

########################### Global PT/OT Properties

class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

########################### Rig Tools

class SEI_OT_armature_infront_wire(SeiOperator, Operator):
    bl_idname = 'sei.armature_infront_wire'
    bl_label = 'Armature In Front, Wire'
    bl_description = 'Make the selected armatures display as "In-Front" and "Wire"'

    def execute(self, context):

        vars = context.scene.sei_variables

        for obj in context.selected_objects:
            if obj.type != 'ARMATURE':
                continue

#            obj.data.display_type = 'OCTAHEDRAL'
            obj.show_in_front = True
            obj.display_type = 'WIRE'

        return {'FINISHED'}

class SEI_OT_armature_assign(SeiOperator, Operator):
    bl_idname = 'sei.armature_assign'
    bl_label = 'Assign Armature'
    bl_description = 'Assign the indicated armature to the selected meshes'

    def execute(self, context):

        vars = context.scene.sei_variables

        for obj in context.selected_objects:
            if obj.type != 'MESH': continue

            armature_modifier = None

            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE':
                    armature_modifier = modifier
                    break

            if not armature_modifier:
                armature_modifier = obj.modifiers.new('Armature', 'ARMATURE')

            armature_modifier.object = vars.armature

            # Rename vertex groups (rigify).
            if not vars.armature.data.get('rig_id'): continue

            for vgroup in obj.vertex_groups:
                if vgroup.name.startswith('DEF-'):
                    vgroup.name = vgroup.name[4:]
                else:
                    if vgroup.name == '---': break

                    vgroup.name = f'DEF-{vgroup.name}'

        return{'FINISHED'}


class SEI_PT_rig_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_rig_tools'
    bl_label = 'Rig Tools'

    def draw(self, context):
        layout = self.layout
        vars = context.scene.sei_variables

        layout.operator('sei.armature_infront_wire', text='In Front | Wire', icon='ARMATURE_DATA')

        row = layout.row(align=True)
        row.prop(vars, 'armature', text='', icon='MOD_ARMATURE')
        row.operator('sei.armature_assign', text='Assign')

        if context.object and context.object.type == 'ARMATURE':
            layout.prop(context.object.data, 'display_type')
        else:
            layout.label(text='')

######### Bone Tools

def bone_parent_or_unparent(context, parent):
    vars = context.scene.sei_variables

    active_mode = context.object.mode
    bpy.ops.object.mode_set(mode='EDIT') # ".parent" only in edit_bones.

    active_bone = context.active_bone

    if active_bone.parent in context.selected_editable_bones:
        active_bone.parent = None

    for bone in context.selected_editable_bones:
        # "Bone".parent = "Bone" does not produce an error.
        bone.parent = active_bone if parent else None

    bpy.ops.object.mode_set(mode=active_mode)

    return {'FINISHED'}

class SEI_OT_bone_parent(SeiOperator, Operator):
    bl_idname = 'sei.bone_parent'
    bl_label = 'Assign Parent'
    bl_description = 'Assign parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=True)

class SEI_OT_bone_unparent(SeiOperator, Operator):
    bl_idname = 'sei.bone_unparent'
    bl_label = 'Remove Parent'
    bl_description = 'Remove parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=False)

class SEI_OT_bone_select_children(SeiOperator, Operator):
    bl_idname = 'sei.bone_select_children'
    bl_label = 'Select Children'
    bl_description = 'Select child bones'

    def execute(self, context):

        vars = context.scene.sei_variables

        for bone in context.active_bone.children_recursive:
            bone.select = True

            if context.mode == 'EDIT_ARMATURE':
                bone.select_head = bone.select_tail = True

        return {'FINISHED'}

class SEI_OT_bone_tail_to_head_parent(SeiOperator, Operator):
    bl_idname = 'sei.bone_tail_to_head_parent'
    bl_label = 'Tail (Parent) to Head'
    bl_description = 'Move parent tail to child head'

    def execute(self, context):

        vars = context.scene.sei_variables

        active_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        bones = context.selected_editable_bones

        for bone in bones:
            if bone.parent in bones:
                bone.parent.tail = bone.head

        bpy.ops.object.mode_set(mode=active_mode)

        return {'FINISHED'}


class SEI_PT_bone_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_bone_tools'
    bl_label = 'Bone Tools'
    bl_parent_id = 'SEI_PT_rig_tools'

    @classmethod
    def poll(cls, context):
        return context.mode in ['EDIT_ARMATURE', 'POSE'] and context.active_bone

    def draw(self, context):
        layout = self.layout
        vars = context.scene.sei_variables

        row = layout.row(align=True)
        row.operator('sei.bone_parent', text='Parent')
        row.operator('sei.bone_unparent', text='Unparent')

        layout.operator('sei.bone_select_children', icon='GROUP_BONE')
        layout.operator('sei.bone_tail_to_head_parent', icon='BONE_DATA')

        layout.separator()

        col = layout.column_flow(columns=2)
        col.prop(context.active_bone, 'use_connect')
        col.prop(context.active_bone, 'use_deform')
        col.prop(context.object.data, 'show_axes', text='Axes')
        col.prop(context.object.data, 'show_names', text='Name')

########################### Scene Tools

class SEI_OT_scene_assign_view_layer_name(SeiOperator, Operator):
    bl_idname = 'sei.scene_assign_view_layer_name'
    bl_label = 'Assign View Layer Name'

    def execute(self, context):

        for obj in context.scene.objects:
            if obj.type in ['MESH', 'ARMATURE', 'LIGHT', 'CAMERA']:
                obj.data.name = obj.name

        return {'FINISHED'}


class SEI_PT_scene_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_scene_tools'
    bl_label = 'Scene Tools'

    @classmethod
    def poll(cls, context):
        return (context.engine in {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'BLENDER_WORKBENCH_NEXT'})

    def draw(self, context):
        layout = self.layout
        vars = context.scene.sei_variables

        col = layout.column()
        col.operator("sei.scene_assign_view_layer_name", text="Rename", icon='FILE_TEXT')

        if context.object and context.object.type == 'MESH':
            col.prop(context.object, 'show_wire', text='Wireframe', icon='MOD_WIREFRAME')
        else:
            col.label(text='')

######### Simplify

class SEI_PT_simplify(SeiPanel, Panel):
    bl_idname = 'SEI_PT_simpify'
    bl_label = 'Simplify'
    bl_parent_id = 'SEI_PT_scene_tools'

    def draw_header(self, context):
        self.layout.prop(context.scene.render, "use_simplify", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False # No animation.

        col = layout.column()

        col.prop(context.scene.render, "simplify_subdivision", text='Max Subsurf')
        col.prop(context.preferences.system, "viewport_aa", text='Viewport Anti-Aliasing')
        col.prop(context.preferences.system, "gl_texture_limit", text='Texture Size Limit')
        col.prop(context.scene.render, "use_simplify_normals", text='Normals')

######### Modifiers

class SEI_PT_modifiers(SeiPanel, Panel):
    bl_idname = 'SEI_PT_modifiers'
    bl_label = 'Modifiers'
    bl_parent_id = 'SEI_PT_scene_tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        all_modifiers = [(obj.name, mod) for obj in context.selected_objects if obj.type == 'MESH' for mod in obj.modifiers]
        sort_modifiers = sorted(all_modifiers, key=lambda x: (x[1].type, x[1].name)) # x[1] = mod
        del all_modifiers

        for obj_name, mod in sort_modifiers:
            row = col.row(align=True)
            row.label(text=f'{mod.name} | {obj_name}', icon_value=layout.icon(mod))

#            for prop in mod.bl_rna.properties: print(prop)
            row.prop(mod, 'show_viewport', icon_only=True)
            row.prop(mod, 'show_render', icon_only=True)

########################### Node Tools

def find_active_node_tree(context):
    tree = context.space_data.node_tree

    # Check recursively until we find the tree.
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree

class SEI_OT_nodes_hide_sockets_from_group_inputs(SeiOperator, Operator):
    bl_idname = 'sei.nodes_hide_sockets_group_inputs'
    bl_label = 'Fix Group Inputs'
    bl_description = 'Toggle unused node sockets from group input nodes'

    def execute(self, context):

        tree = find_active_node_tree(context)

        for node in tree.nodes:
            if node.type != 'GROUP_INPUT' or node.mute: continue

            for socket in node.outputs:
                socket.hide = True

#        self.report({'INFO'}, "Fixed group inputs.")

        return {'FINISHED'}

class SEI_OT_nodes_assign_image_space(SeiOperator, Operator):
    bl_idname = 'sei.nodes_assign_image_space'
    bl_label = 'Assign Image Space'
    bl_description = 'Assign the desired image space to the selected image nodes'

    def execute(self, context):

        vars = context.scene.sei_variables

        for node in context.selected_nodes:
            if node.type != 'TEX_IMAGE' or not node.image: continue

            node.image.colorspace_settings.name = vars.color_space
            node.image.alpha_mode = 'CHANNEL_PACKED'

        return {'FINISHED'}


class SEI_PT_node_tools(Panel):
    bl_idname = 'SEI_PT_node_tools'
    bl_label = 'Node Tools'

    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Group'

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree

    def draw(self, context):
        layout = self.layout
        vars = context.scene.sei_variables

        layout.operator('sei.nodes_hide_sockets_group_inputs', icon='NODE')

        row = layout.row(align=True)
        row.prop(vars, 'color_space', text='', icon='IMAGE_RGB')
        row.operator('sei.nodes_assign_image_space', text='Assign')

########################### Modifier Profiling

# Simon Thommes
# https://gitlab.com/simonthommes/random-blender-scripts/-/tree/master/addons/profiling_buddy
#
# Slightly modified.
def time_to_string(t):
    ''' Format time in second to the nearest sensible unit.
    '''
    units = {3600.: 'h', 60.: 'm', 1.: 's', .001: 'ms'}

    for factor in units.keys():
        if t >= factor:
            return f'{t/factor:.3g} {units[factor]}'

    if t >= 1e-4:
        return f'{t/factor:.3g} {units[factor]}'
    else:
        return f'<0.1 ms'

class SEI_PT_modifier_profiling(Panel):
    bl_idname = 'SEI_PT_modifier_profiling'
    bl_label = '   Modifier Profiling'

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'modifier'

    def draw_header(self, context):
        self.layout.label(icon='MODIFIER')

    def draw(self, context):

        depsgraph = context.view_layer.depsgraph
        obj_eval = context.object.evaluated_get(depsgraph)

        times = [me.execution_time for me in obj_eval.modifiers]

        box = self.layout.box()
        col = box.column(align=True)

        for index, time in enumerate(times):
            mod_eval = obj_eval.modifiers[index]

            row = col.row()
            row.enabled = mod_eval.show_viewport
            row.alert = time >= 0.8 * max(times)

            row.label(text=f'{mod_eval.name}:')
            row.label(text=time_to_string(time))

#        # With icons.
#        for index, time in enumerate(times):
#            mod_eval = obj_eval.modifiers[index]

#            row = col.split(factor=0.07)
#            row.enabled = mod_eval.show_viewport
#            row.label(icon_value=self.layout.icon(mod_eval))

#            row = row.column().split(factor=0.6)
#            row.enabled = mod_eval.show_viewport
#            row.alert = time >= 0.8 * max(times)

#            row.label(text=f'{mod_eval.name}:')
#            row.label(text=time_to_string(time))

        row = box.row()
        row.label(text='TOTAL:')
        row.label(text=time_to_string(sum(times)))

#===========================

classes = [
    SEI_variables,

    # Rig Tools
    SEI_OT_armature_infront_wire,
    SEI_OT_armature_assign,
    SEI_PT_rig_tools,

    # Rig Tools -> Bone Tools
    SEI_OT_bone_parent,
    SEI_OT_bone_unparent,
    SEI_OT_bone_select_children,
    SEI_OT_bone_tail_to_head_parent,
    SEI_PT_bone_tools,

    # Scene Tools -> Simplify -> Modifiers
    SEI_OT_scene_assign_view_layer_name,
    SEI_PT_scene_tools,
    SEI_PT_simplify,
    SEI_PT_modifiers,

    # Node Tools
    SEI_OT_nodes_hide_sockets_from_group_inputs,
    SEI_OT_nodes_assign_image_space,
    SEI_PT_node_tools,

    # Modifier Profiling (Simon Thommes)
    SEI_PT_modifier_profiling,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.sei_variables = PointerProperty(type=SEI_variables)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.sei_variables

if __name__ == "__main__": # debug; live edit
    register()