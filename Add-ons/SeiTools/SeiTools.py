import bpy
import blf

from bpy.props import EnumProperty, PointerProperty, IntProperty
from bpy.types import Operator, Header, Panel, PropertyGroup

bl_info = {
    "name": "SeiTools",
    "author": "Seilotte",
    "version": (1, 3, 7),
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
    is_running: IntProperty(name='Display Weight', default=0)

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

################## OT Armature Tools

class SEI_OT_armature_infront_wire(SeiOperator, Operator):
    bl_idname = 'sei.armature_infront_wire'
    bl_label = 'In Front | Wire'
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

# Numerical Vertex Weight Visualizer
#
# Bartius Crouch, CoDEmanX, hikariztw
# https://github.com/theoldben/NumericalVertexWeightVisualizer
#
# Slightly modified.
def draw_callback_px(self, context):
    '''
    Calculate locations and store them as ID property in the mesh.
    '''
    # polling
#    if context.mode != 'EDIT_MESH' and context.mode != 'PAINT_WEIGHT':
#        return

    # Get screen information.
    region = context.region
    mid_x = region.width / 2
    mid_y = region.height / 2
    width = region.width
    height = region.height

    # Get matrices.
    # total_mattrix = view_mattrix @ obj_matrix
    obj = context.active_object
    total_mat = context.space_data.region_3d.perspective_matrix @ obj.matrix_world

    blf.size(0, 10)

    def draw_index(r, g, b, index, center):

        vec = total_mat @ center # order is important

        # dehomogenise
        vec = (vec[0] / vec[3], vec[1] / vec[3], vec[2] / vec[3])
        x = int(mid_x + vec[0] * width / 2)
        y = int(mid_y + vec[1] * height / 2)

        # bgl.glColorMask(1, 1, 1, 1)
        blf.position(0, x, y, 0)

        if isinstance(index, float):
            blf.draw(0, '{:.2f}'.format(index))
        else:
            blf.draw(0, str(index))

#    if vars.live_mode:
#        obj.data.update()

#    if vars.display_weight:
    vgroup = obj.vertex_groups.active

    for v in obj.data.vertices:
        try:
            draw_index(
                1.0, 1.0, 1.0,
                vgroup.weight(v.index),
                v.co.to_4d()
            )
        except Exception as e:
            continue

class SEI_OT_view3d_weight_visualizer(SeiOperator, Operator):
    bl_idname = 'sei.view3d_weight_visualizer'
    bl_label = 'Visualize Weights'
    bl_description = 'Toggle the visualization of numerical weights'

    _handle = None

    @classmethod
    def poll(cls, context):
        return context.mode == 'PAINT_WEIGHT'

    def modal(self, context, event):
        vars = context.scene.sei_variables

        if context.area:
            context.area.tag_redraw()

        # Removal of callbacks when the operator is called again.
        if vars.is_running == -1:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            vars.is_running = 0
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        vars = context.scene.sei_variables

        if context.area.type != "VIEW_3D":
            self.report({'WARNING'}, 'View3D not found, cannot run operator')
            return {'CANCELLED'}

        elif vars.is_running != 1:
            # Operator is called for the first time, start everything.
            vars.is_running = 1

            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_px,
                (self, context),
                'WINDOW',
                'POST_PIXEL'
            )
            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}

        else:
            # Operator is called again, stop displaying.
            vars.is_running = -1
            return {'RUNNING_MODAL'}

######### OT Bone Tools

def bone_parent_or_unparent(context, parent):

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

class SEI_RIG_OT_bone_select_children_recursive(SeiOperator, Operator):
    bl_idname = 'sei.bone_select_children_recursive'
    bl_label = 'Select Children Recursive'
    bl_description = 'Select child bones recursively on the active bone'

    def execute(self, context):

        for bone in context.active_bone.children_recursive:
            bone.select = True

            if context.mode == 'EDIT_ARMATURE':
                bone.select_head = bone.select_tail = True

        return {'FINISHED'}

class SEI_RIG_OT_bone_tail_to_head_parent(SeiOperator, Operator):
    bl_idname = 'sei.bone_tail_to_head_parent'
    bl_label = 'Tail (Parent) to Head'
    bl_description = 'Move parent tail to child head on the selected bones'

    def execute(self, context):

        active_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        bones = context.selected_editable_bones

        for bone in bones:
            if bone.parent in bones:
                bone.parent.tail = bone.head

        bpy.ops.object.mode_set(mode=active_mode)

        return {'FINISHED'}

################## OT Scene Tools

class SEI_OT_scene_assign_view_layer_name(SeiOperator, Operator):
    bl_idname = 'sei.scene_assign_view_layer_name'
    bl_label = 'Rename'
    bl_description = 'Assign the mesh data name to the selected objects'

    def execute(self, context):

        for obj in context.scene.objects:
            if obj.type in ['MESH', 'ARMATURE', 'LIGHT', 'CAMERA']:
                obj.data.name = obj.name

        return {'FINISHED'}

########################### PT Tools

class SEI_PT_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_tools'
    bl_label = 'Tools'

    def draw(self, context):
        layout = self.layout

        vars = context.scene.sei_variables 
        obj = context.active_object

        # Armature Tools
        header, panel = layout.panel('SEI_PT_armature_tools')
        header.label(text='Armature Tools', icon='ARMATURE_DATA')

        if panel:
            panel.operator('sei.armature_infront_wire')

            row = panel.row(align=True)
            row.prop(vars, 'armature', text='', icon='MOD_ARMATURE')
            row.operator('sei.armature_assign', text='Assign')

            if obj and obj.type == 'ARMATURE':
                panel.prop(obj.data, 'display_type')
            else:
                panel.label()

            panel.operator(
                'sei.view3d_weight_visualizer',
                icon='PAUSE' if vars.is_running == 1 else 'WPAINT_HLT'
            )

            # Armature Tools > Bone Tools
            header, subpanel = panel.panel('SEI_PT_bone_tools')
            header.label(text='Bone Tools', icon='BONE_DATA')

            if subpanel:
                bone = context.active_bone

                if bone is None:
                    subpanel.label(text='No Active Bone', icon='INFO')

                elif context.mode not in ['EDIT_ARMATURE', 'POSE']:
                    subpanel.label(text='Not Pose/Edit Mode', icon='INFO')

                else:
                    subpanel.operator(
                        'sei.bone_select_children_recursive',
                        text='Select Children [All]'
                    ) # GROUP_BONE

                    subpanel.separator()

                    row = subpanel.row(align=True)
                    row.operator('sei.bone_parent', text='Parent')
                    row.operator('sei.bone_unparent', text='Unparent')

                    subpanel.operator('sei.bone_tail_to_head_parent') # BONE_DATA

                    subpanel.separator()

                    col = subpanel.column_flow(columns=2)
                    col.prop(bone, 'use_connect')
                    col.prop(bone, 'use_deform')
                    col.prop(obj.data, 'show_axes', text='Axes')
                    col.prop(obj.data, 'show_names', text='Name')

        # Scene Tools
        header, panel = layout.panel('SEI_PT_scene_tools')
        header.label(text='Scene Tools', icon='SCENE_DATA')

        if panel:
            panel.operator('sei.scene_assign_view_layer_name', icon='FILE_TEXT')

            if obj and obj.type == 'MESH':
                panel.prop(obj, 'show_wire', text='Wireframe', icon='MOD_WIREFRAME')
            else:
                panel.label()

            # Scene Tools > Simplify
            header, subpanel = panel.panel('SEI_PT_simplify')
            header.prop(context.scene.render, 'use_simplify', text='')
            header.label(text='Simplify')

            if subpanel:
                col = subpanel.column()
                col.use_property_split = True
                col.use_property_decorate = False # No animation.

                col.prop(context.scene.render, "simplify_subdivision", text='Max Subsurf')
                col.prop(context.preferences.system, "viewport_aa", text='Viewport Anti-Aliasing')
                col.prop(context.preferences.system, "gl_texture_limit", text='Texture Size Limit')
                col.prop(context.scene.render, "use_simplify_normals", text='Normals')

            # Scene Tools > Modifiers
            header, subpanel = panel.panel('SEI_PT_modifiers', default_closed=True)
            header.label(text='Modifiers', icon='MODIFIER')

            if subpanel:
                all_modifiers = [(obj.name, mod) for obj in context.selected_objects if obj.type == 'MESH' for mod in obj.modifiers]
                sort_modifiers = sorted(all_modifiers, key=lambda x: (x[1].type, x[1].name)) # x[1] = mod
                del all_modifiers

                col = subpanel.column()

                if not sort_modifiers:
                    col.label(text='No Modifiers', icon='INFO')
                else:
                    for obj_name, mod in sort_modifiers:
                        row = col.row(align=True)
                        row.label(text=f'{mod.name} | {obj_name}', icon_value=layout.icon(mod))

#                        for prop in mod.bl_rna.properties: print(prop)
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

########################### Properties Header Mod

# Restart blender after disabling the addon to restore the class.
class PROPERTIES_HT_header(Header):
    bl_space_type = 'PROPERTIES'

    def draw(self, context):
        layout = self.layout

        layout.template_header()

        layout.operator('wm.console_toggle', text='', icon='CONSOLE')
        layout.operator('outliner.orphans_purge', text=' ', icon='TRASH') # Purge

        layout.separator_spacer()

        layout.prop(context.space_data, "search_filter", icon='VIEWZOOM', text="")
        layout.popover(panel="PROPERTIES_PT_options", text="")

#===========================

classes = [
    SEI_variables,

    # Tools > Armature Tools
    SEI_OT_armature_infront_wire,
    SEI_OT_armature_assign,
    # Numerical Vertex Weight Visualizer (Bartius Crouch, CoDEmanX, hikariztw)
    SEI_OT_view3d_weight_visualizer,

    # Tools > Armature Tools > Bone Tools
    SEI_OT_bone_parent,
    SEI_OT_bone_unparent,
    SEI_RIG_OT_bone_select_children_recursive,
    SEI_RIG_OT_bone_tail_to_head_parent,

    # Tools > Scene Tools > Simplify > Modifiers
    SEI_OT_scene_assign_view_layer_name,

    SEI_PT_tools,

    # Node Tools
    SEI_OT_nodes_hide_sockets_from_group_inputs,
    SEI_OT_nodes_assign_image_space,
    SEI_PT_node_tools,

    # Modifier Profiling (Simon Thommes)
    SEI_PT_modifier_profiling,

    # Properties Header Mod
    PROPERTIES_HT_header,
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