import bpy
import blf
import gpu

from gpu_extras.batch import batch_for_shader
from bpy.types import Operator, Panel, PropertyGroup

bl_info = {
    "name": "SeiTools",
    "author": "Seilotte",
    "version": (1, 3, 9),
    "blender": (4, 3, 2),
    "location": "3D View > Properties > Sei",
    "description": "Random collection of tools for my personal use",
    "doc_url": "seilotte.github.io",
    "tracker_url": "seilotte.github.io",
    "category": "Workflow", # 3D View
}

########################### Global PT/OT Properties

class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

class SeiOperator:
    bl_options = {'REGISTER', 'UNDO'}

################## OT Armature Tools

class SEI_OT_armature_infront_wire(SeiOperator, Operator):
    bl_idname = 'sei.armature_infront_wire'
    bl_label = 'In Front | Wire'
    bl_description = 'Make the selected armatures display as "In-Front" and "Wire"'

    def execute(self, context):

        for obj in context.selected_objects:
            if obj.type != 'ARMATURE':
                continue

            obj.show_in_front = True
            obj.display_type = 'WIRE'
#            obj.data.display_type = 'OCTAHEDRAL'

        return {'FINISHED'}

class SEI_OT_armature_assign(SeiOperator, Operator):
    bl_idname = 'sei.armature_assign'
    bl_label = 'Assign Armature'
    bl_description = 'Assign the indicated armature to the selected meshes'

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):

        armature = context.active_object

        for obj in context.selected_objects:
            if obj == armature:
                continue
            elif obj.type != 'MESH':
                continue

            armature_modifier = None

            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE':
                    armature_modifier = modifier
                    break

            if not armature_modifier:
                armature_modifier = obj.modifiers.new('Armature', 'ARMATURE')

            armature_modifier.object = armature

            # Rigify; Rename vertex groups.
            if not armature.data.get('rig_id'):
                continue

            for vgroup in obj.vertex_groups:
                if vgroup.name.startswith('DEF-'):
                    vgroup.name = vgroup.name[4:]
                elif v.group.name == '---':
                    break
                else:
                    vgroup.name = f'DEF-{vgroup.name}'

        return{'FINISHED'}

# Numerical Vertex Weight Visualizer
#
# Bartius Crouch, CoDEmanX, hikariztw
# https://github.com/theoldben/NumericalVertexWeightVisualizer
#
# Modified.
class SEI_OT_view3d_weights_visualizer(SeiOperator, Operator):
    bl_idname = 'sei.view3d_weights_visualizer'
    bl_label = 'Visualize Weights'
    bl_description = 'Toggle the visibility of numerical weights'

    bl_options = {'REGISTER', 'UNDO'}

    _handle = None

    def draw_weights(self, context):
        if context.mode != 'PAINT_WEIGHT':
            return

        obj = context.active_object.evaluated_get(context.evaluated_depsgraph_get())
        vgroup = obj.vertex_groups.active
        matrix_total = context.region_data.perspective_matrix @ obj.matrix_world

        _, _, mid_x, mid_y = gpu.state.viewport_get()
        mid_x /= 2
        mid_y /= 2

        blf.size(0, 12.0)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 6, 0.0, 0.0, 0.0, 1.0)

        for v in obj.data.vertices:
            try:
                weight = vgroup.weight(v.index)

                vec = matrix_total @ v.co.to_4d()
                vec = (vec[0] / vec[3], vec[1] / vec[3]) # dehomogenize

                x = int(mid_x + vec[0] * mid_x)
                y = int(mid_y + vec[1] * mid_y)

                blf.position(0, x, y, 0)

                if isinstance(weight, float):
                    blf.draw(0, '{:.3f}'.format(weight))
                else:
                    blf.draw(0, str(weight))

            except Exception as e:
                continue

    @classmethod
    def poll(cls, context):
        return \
        context.area \
        and context.area.type == 'VIEW_3D' \
        and context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        if SEI_OT_view3d_weights_visualizer._handle:
            bpy.types.SpaceView3D.draw_handler_remove(
                SEI_OT_view3d_weights_visualizer._handle,
                'WINDOW'
            )
            SEI_OT_view3d_weights_visualizer._handle = None

        else:
            SEI_OT_view3d_weights_visualizer._handle = \
            bpy.types.SpaceView3D.draw_handler_add(
                self.draw_weights,
                (context,),
                'WINDOW',
                'POST_PIXEL'
            )

        context.area.tag_redraw()

        return {'FINISHED'}

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

class SEI_RIG_OT_bone_parent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_parent'
    bl_label = 'Assign Parent'
    bl_description = 'Assign parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=True)

class SEI_RIG_OT_bone_unparent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_unparent'
    bl_label = 'Remove Parent'
    bl_description = 'Remove parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=False)

class SEI_RIG_OT_bone_select_children_recursive(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_select_children_recursive'
    bl_label = 'Select Children Recursive'
    bl_description = 'Select child bones recursively on the active bone'

    def execute(self, context):

        for bone in context.active_bone.children_recursive:
            bone.select = True

            if context.mode == 'EDIT_ARMATURE':
                bone.select_head = bone.select_tail = True

        return {'FINISHED'}

class SEI_RIG_OT_bone_tail_to_head_parent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_tail_to_head_parent'
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

class SEI_OT_clean_blend(SeiOperator, Operator):
    bl_idname = 'sei.clean_blend'
    bl_label = 'Clean Blend'
    bl_description = 'Clean the blend file with blender operators'

    clear_props: bpy.props.BoolProperty(name='Properties', default=False)

    def execute(self, context):

        bpy.ops.screen.spacedata_cleanup()
        bpy.ops.wm.operator_presets_cleanup()
        bpy.ops.wm.clear_recent_files()
        bpy.ops.wm.previews_clear()

        if not self.clear_props:
            return {'FINISHED'}

        blend_data = [
            # https://docs.blender.org/api/current/bpy.types.BlendData.html#bpy.types.BlendData
            'armatures',
            'meshes',
            'objects',
            'scenes',
            'screens'
        ]

        for x in blend_data:
            bdata = getattr(bpy.data, x, None)

            if bdata is None:
                continue

            # Scene > ViewLayers
            elif x == 'scenes':
                for scene in bdata:
                    scene.id_properties_clear()

                    for view_layer in scene.view_layers:
                        view_layer.id_properties_clear()

            else:
                for i in bdata:
                    i.id_properties_clear()

        return {'FINISHED'}

class SEI_OT_scene_assign_object_name(SeiOperator, Operator):
    bl_idname = 'sei.scene_assign_object_name'
    bl_label = 'Rename'
    bl_description = 'Assign the object name to the data of the selected objects'

    def execute(self, context):

        for obj in context.scene.objects:
            if hasattr(obj, 'data') and hasattr(obj.data, 'name'):
                obj.data.name = obj.name

        return {'FINISHED'}

class SEI_OT_view3d_pixels_visualizer(SeiOperator, Operator):
    bl_idname = 'sei.view3d_pixels_visualizer'
    bl_label = 'Visualize Pixels'
    bl_description = 'Toggle the visibility of pixels for the active camera'

    bl_options = {'REGISTER', 'UNDO'}

    _handle = None

    def _setup_shader(self):
        vsh = \
        '''
        in vec4 position; // zeros
        in vec2 coord;

        out vec2 uv;

        uniform mat4 offsets; // vertex_positions
        uniform mat4 matrix_custom;

        void main()
        {
            gl_Position = matrix_custom * (position + offsets[gl_VertexID]);
            uv = coord;
        }
        '''
        
        fsh = \
        '''
        in vec2 uv;

        out vec4 col0;

        uniform sampler2D image0;

        void main()
        {
            col0 = texelFetch(image0, ivec2(uv * textureSize(image0, 0).xy), 0);
            // col0 = vec4(uv, 0.0, 1.0);
        }
        '''

        return gpu.types.GPUShader(vertexcode = vsh, fragcode = fsh)

    def _setup_batch(self, shader):
        return batch_for_shader(
            shader,
            'TRI_FAN',
            {
                'position': (0, 0, 0, 0),
                'coord': ((0, 0), (1, 0), (1, 1), (0, 1))
            }
        )

    def _setup_offscreen(self, context):
        render = context.scene.render
        scale = render.resolution_percentage / 100

        return gpu.types.GPUOffScreen(
            round(render.resolution_x * scale),
            round(render.resolution_y * scale),
            format = 'RGBA8'
        )

    def draw_pixels(self, context, offscreen, shader, batch):
        scene = context.scene
        camera = scene.camera

        if camera is None:
            return

        offscreen.draw_view3d(
            scene,
            context.view_layer,
            context.space_data,
            context.region,
            camera.matrix_world.inverted(), # view_matrix
            camera.calc_matrix_camera( # projection_matrix
                context.evaluated_depsgraph_get(),
                x = offscreen.width,
                y = offscreen.height
            ),
            do_color_management = False
        )

        gpu.state.depth_mask_set(False)
        gpu.state.blend_set('NONE')

        frame = camera.data.view_frame(scene = scene)
        frame = (
            frame[2].x, frame[2].y, frame[2].z, 0.0,
            frame[1].x, frame[1].y, frame[1].z, 0.0,
            frame[0].x, frame[0].y, frame[0].z, 0.0,
            frame[3].x, frame[3].y, frame[3].z, 0.0
        )

        shader.uniform_float('offsets', frame) # mat4
        shader.uniform_float('matrix_custom', context.region_data.perspective_matrix @ camera.matrix_world)
        shader.uniform_sampler('image0', offscreen.texture_color)

        batch.draw(shader)

    @classmethod
    def poll(cls, context):
        return \
        context.area \
        and context.area.type == 'VIEW_3D' \
        and not(context.scene.camera is None)

    def execute(self, context):
        if SEI_OT_view3d_pixels_visualizer._handle:
            bpy.types.SpaceView3D.draw_handler_remove(
                SEI_OT_view3d_pixels_visualizer._handle,
                'WINDOW'
            )
            SEI_OT_view3d_pixels_visualizer._handle = None

        else:
            offscreen = self._setup_offscreen(context)
            shader = self._setup_shader()
            batch = self._setup_batch(shader)

            SEI_OT_view3d_pixels_visualizer._handle = \
            bpy.types.SpaceView3D.draw_handler_add(
                self.draw_pixels,
                (context, offscreen, shader, batch),
                'WINDOW',
                'POST_PIXEL'
            )

        context.area.tag_redraw()

        return {'FINISHED'}

########################### PT Tools

class SEI_PT_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_tools'
    bl_label = 'Tools'

    def draw(self, context):
        layout = self.layout

        obj = context.active_object

        # Armature Tools
        header, panel = layout.panel('SEI_PT_armature_tools')
        header.label(text='Armature Tools', icon='ARMATURE_DATA')

        if panel:
            panel.operator('sei.armature_infront_wire')
            panel.operator('sei.armature_assign')

            panel.prop(obj.data, 'display_type') \
            if obj and obj.type == 'ARMATURE' else panel.label()

            panel.operator(
                'sei.view3d_weights_visualizer',
                icon = 'PAUSE' if SEI_OT_view3d_weights_visualizer._handle else 'WPAINT_HLT'
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
                        'sei_rig.bone_select_children_recursive',
                        text='Select Children [All]'
                    ) # GROUP_BONE

                    subpanel.separator()

                    row = subpanel.row(align=True)
                    row.operator('sei_rig.bone_parent', text='Parent')
                    row.operator('sei_rig.bone_unparent', text='Unparent')

                    subpanel.operator('sei_rig.bone_tail_to_head_parent') # BONE_DATA

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
            panel.operator('sei.clean_blend', icon='FILE_BLEND')
            panel.operator('sei.scene_assign_object_name', icon='FILE_TEXT')

            panel.prop(obj, 'show_wire', text='Wireframe', icon='MOD_WIREFRAME') \
            if obj and obj.type == 'MESH' else panel.label()

            panel.operator(
                'sei.view3d_pixels_visualizer',
                icon = 'PAUSE' if SEI_OT_view3d_pixels_visualizer._handle else 'TEXTURE_DATA'
            )

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
                sort_modifiers = [
                    (obj.name, mod)
                    for obj in context.selected_objects
                    if obj.type in ['MESH', 'GREASEPENCIL']
                    for mod in list(obj.modifiers)
                ]
                sort_modifiers = sorted(sort_modifiers, key=lambda x: (x[1].type, x[1].name)) # x[1] = mod

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

########################### UI Mods

# Restart blender after disabling the addon to restore the class.
def SEI_PROPERTIES_HT_header(self, context):
    layout = self.layout

    layout.template_header()

#    layout.operator('wm.console_toggle', text='', icon='CONSOLE') # Windows.
    layout.operator('outliner.orphans_purge', text=' ', icon='TRASH') # Purge

    layout.separator_spacer()

    layout.prop(context.space_data, "search_filter", icon='VIEWZOOM', text="")
    layout.popover(panel="PROPERTIES_PT_options", text="")

def SEI_VIEW3D_HT_header(self, context):
    self.layout.operator(
        'sei.view3d_pixels_visualizer',
        text = ' ',
        icon = 'PAUSE' if SEI_OT_view3d_pixels_visualizer._handle else 'TEXTURE_DATA'
    )

def SEI_NODE_MT_node_tree_interface_context_menu(self, context):
    self.layout.operator('sei.nodes_hide_sockets_group_inputs', icon='NODE')

#===========================

classes = [
    # Tools > Armature Tools
    SEI_OT_armature_infront_wire,
    SEI_OT_armature_assign,
    # Numerical Vertex Weight Visualizer (Bartius Crouch, CoDEmanX, hikariztw)
    SEI_OT_view3d_weights_visualizer,

    # Tools > Armature Tools > Bone Tools
    SEI_RIG_OT_bone_parent,
    SEI_RIG_OT_bone_unparent,
    SEI_RIG_OT_bone_select_children_recursive,
    SEI_RIG_OT_bone_tail_to_head_parent,

    # Tools > Scene Tools > Simplify > Modifiers
    SEI_OT_clean_blend,
    SEI_OT_scene_assign_object_name,
    SEI_OT_view3d_pixels_visualizer,

    SEI_PT_tools,

    # Node Tools
    SEI_OT_nodes_hide_sockets_from_group_inputs,

    # Modifier Profiling (Simon Thommes)
    SEI_PT_modifier_profiling,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.PROPERTIES_HT_header.draw = SEI_PROPERTIES_HT_header # Restart blender after disabling the addon to restore the class.
    bpy.types.VIEW3D_HT_header.append(SEI_VIEW3D_HT_header)
    bpy.types.NODE_MT_node_tree_interface_context_menu.append(SEI_NODE_MT_node_tree_interface_context_menu)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_HT_header.remove(SEI_VIEW3D_HT_header)
    bpy.types.NODE_MT_node_tree_interface_context_menu.remove(SEI_NODE_MT_node_tree_interface_context_menu)

if __name__ == "__main__": # debug; live edit
    register()
