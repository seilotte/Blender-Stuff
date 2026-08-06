import bpy
import gpu

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Color

bl_info = {
    "name": "Sei BBoneNet",
    "author": "Seilotte",
    "version": (0, 1, 1),
    "blender": (5, 2, 0),
    "location": "3D View > Toolbar > Pose Mode",
    "description": "Construct bendy bones as a net",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/sei_curve",
    "doc_url": "https://github.com/seilotte/Blender-Stuff/issues",
    "category": "Rigging",
}

DEBUG_MODE = False

def print_message(message: str = "") -> None:
    if DEBUG_MODE is True:
        print(f'Sei BboneNet: {message}')

class SEI_OT_bbonenet(bpy.types.Operator):
    bl_idname = 'sei.bbonenet'
    bl_label = 'Bbonenet'
    bl_description = 'Construct bendy bones as a net'
    bl_options = {'REGISTER', 'UNDO'}

    _handle = None

    SIZE_PX: bpy.props.IntProperty(
        name = 'Size',
        description = 'Pixel radius for nearest vertex detection',
        default = 12,
        min = 1,
        max = 1000,
        soft_max = 100,
        subtype = 'PIXEL'
    )

    SIZE_BB: bpy.props.FloatProperty(
        name = 'Scale',
        description = 'Global scale of the new bones',
        default = 0.01,
        min = 1e-6,
        subtype = 'DISTANCE'
    )

    EPSILON: bpy.props.FloatProperty(
        name = 'Merge Distance',
        description = 'Maximum distance between elements to merge',
        default = 1e-3,
        min = 1e-6, # NOTE: Limit is defined by bone envelopes.
        subtype = 'DISTANCE'
    )

    #########
    # Utils.

    def _cancel(self, context):

        cls = type(self)

        if cls._handle:
            bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW')

        cls._handle = None

        self.point_current = None
        self.point_last = None

        if area := context.area:
            area.header_text_set(None)

    @staticmethod
    def _setup_shader_point_uniform() -> gpu.types.GPUShader:

        vsh = '''
        void main()
        {
            gl_PointSize = 11.0; // vulkan
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
        }
        '''

        fsh = '''
        void main()
        {
            vec2 delta = gl_PointCoord - vec2(0.5);

            if (dot(delta, delta) > 0.25) { discard; return; }

            // TODO: anti-alias?
            // frag_colour.a = linearstep(0.2, 0.25, dist);

            frag_colour = colour;
        }
        '''

        shader_info = gpu.types.GPUShaderCreateInfo()

        shader_info.vertex_source(vsh)
        shader_info.fragment_source(fsh)

        # vsh attributes
        shader_info.vertex_in(0, 'VEC3', 'pos')

        # uniforms
        shader_info.push_constant('MAT4', 'ModelViewProjectionMatrix')
        shader_info.push_constant('VEC4', 'colour')

        # write
        shader_info.fragment_out(0, 'VEC4', 'frag_colour')

        return gpu.shader.create_from_info(shader_info)

    def _draw_bbonenet(self, context) -> None:

        if context.mode not in ('EDIT_ARMATURE', 'POSE'):
            return

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
        gpu.state.point_size_set(11.0) # opengl; TODO: x * ui_scale

        if self.point_current: # _setup_nearest_point()

            # shader = gpu.shader.from_builtin('POINT_UNIFORM_COLOR')
            shader = self._setup_shader_point_uniform()
            shader.bind()

            # shader.uniform_float('ModelViewProjectionMatrix', gpu.matrix.)
            shader.uniform_float('colour', (0.0, 1.0, 1.0, 1.0))

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': [self.point_current[0]]})
            batch.draw(shader)

        if self.point_last:

            shader = self._setup_shader_point_uniform()
            shader.bind()

            shader.uniform_float('colour', (1.0, 1.0, 0.0, 1.0))

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': [self.point_last[0]]})
            batch.draw(shader)

        if self.point_current and self.point_last:

            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
            shader.bind()

            shader.uniform_float('color', (1.0, 1.0, 0.0, 1.0))
            shader.uniform_float('lineWidth', 2.0)
            shader.uniform_float('viewportSize', gpu.state.viewport_get()[2:])

            batch = batch_for_shader(
                shader, 'LINES', {'pos': [self.point_last[0], self.point_current[0]]})
            batch.draw(shader)

        return None

    def _setup_nearest_point(self, context, event) -> tuple:
        '''
        returns (vec3_coord, vec3_normal)

        ws = world-space
        ls = local/object-space
        ss = screen-space
        '''

        region = context.region
        rv3d = context.region_data

        mouse_ss = Vector((event.mouse_region_x, event.mouse_region_y))
        mouse_ws = view3d_utils.region_2d_to_location_3d(
            region, rv3d, mouse_ss, rv3d.view_location)

        #########
        # Get nearest bone point.

        # TODO; Loop over all armatures?

        #########
        # Get nearest mesh point.

        ro_ws = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, mouse_ss)

        rd_ws = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, mouse_ss)

        depsgraph = context.evaluated_depsgraph_get()

        _, _, _, _, hit_obj, _ = context.scene.ray_cast(
            depsgraph, ro_ws, rd_ws)

        if hit_obj is None or hit_obj.type != 'MESH':
            return (mouse_ws, None)

        obj = hit_obj.evaluated_get(depsgraph)
        obj_matrix = obj.matrix_world
        obj_matrix_inv = obj.matrix_world.inverted()

        _, _, _, face_index = obj.ray_cast(
            obj_matrix_inv @ ro_ws, obj_matrix_inv.to_3x3() @ rd_ws)

        if face_index < 0: # no hit
            return (mouse_ws, None)

        min_dist_sq = self.SIZE_PX * self.SIZE_PX
        min_vert_ws = None
        min_vert_normal = None

        for vi in obj.data.polygons[face_index].vertices:

            vert = obj.data.vertices[vi]
            vert_ws = obj_matrix @ vert.co
            vert_ss = view3d_utils.location_3d_to_region_2d(
                region, rv3d, vert_ws)

            if vert_ss is None:
                continue

            dist_sq = (vert_ss - mouse_ss).length_squared

            if dist_sq > min_dist_sq:
                continue

            min_dist_sq = dist_sq
            min_vert_ws = vert_ws
            min_vert_normal = vert.normal

        if min_vert_ws is None:
            return (mouse_ws, None)

        if min_vert_normal is not None:
            min_vert_normal = (obj_matrix.to_3x3() @ min_vert_normal).copy()

        return (min_vert_ws.copy(), min_vert_normal) # also face normal?

    def _setup_bbone(self, context) -> None:

        if context.mode != 'POSE': # SEI_bbonenet_tool() -> bl_context_mode
            return None

        #########
        # Create widgets.

        @staticmethod
        def mesh_create(name = 'Mesh', vertices = [], edges = [], faces = []):
            obj = bpy.data.objects.get(name)

            if obj is None:
                mesh = bpy.data.meshes.new(name = name)
                mesh.from_pydata(vertices, edges, faces)

                obj = bpy.data.objects.new(name, mesh)

            return obj

        @staticmethod
        def find_layer_collection(target_collection):
            stack = [context.view_layer.layer_collection]

            while stack:
                current_collection = stack.pop()

                if current_collection.collection == target_collection:
                    return current_collection

                stack.extend(current_collection.children)

            return None

        map_wgt = {
            'None': None, # .get does this
            'line': mesh_create(
                name = 'WGT-Line',
                vertices = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
                edges = [(0, 1)]
            ),
            'diamond': mesh_create(
                name = 'WGT-Diamond',
                vertices = [(-0.5, 0.0, 0.0), (0.0, 0.0, -0.5), (0.5, 0.0, 0.0), (0.0, 0.0, 0.5), (0.0, -0.5, 0.0), (0.0, 0.5, 0.0), (0.0, 0.8, 0.0)],
                edges = [[0, 4], [4, 3], [3, 0], [3, 5], [5, 0], [0, 1], [1, 4], [5, 1], [2, 3], [4, 2], [2, 5], [1, 2], [5, 6]]
            ),
        }

        coll_wgt = bpy.data.collections.get('WGT Widgets')

        if coll_wgt is None:
            coll_wgt = bpy.data.collections.new('WGT Widgets')
            context.scene.collection.children.link(coll_wgt)

        find_layer_collection(coll_wgt).exclude = True

        for widget in map_wgt.values():
            if widget and coll_wgt.objects.get(widget.name) is None:
                coll_wgt.objects.link(widget)

        #########
        # Armature.

        obj = context.object
        arm = obj.data

        bcoll_net = arm.collections_all.get('Net') \
            or arm.collections.new('Net')
        bcoll_bbones = arm.collections_all.get('Net_Bbones') \
            or arm.collections.new('Net_Bbones', parent = bcoll_net)
        bcoll_points = arm.collections_all.get('Net_Points') \
            or arm.collections.new('Net_Points', parent = bcoll_net)
        bcoll_handles = arm.collections_all.get('Net_Handles') \
            or arm.collections.new('Net_Handles', parent = bcoll_net)

        #########
        # Edit mode.

        bpy.ops.object.mode_set(mode = 'EDIT')

        @staticmethod
        def get_nearest_bone(
            armature: bpy.types.Armature,
            position: Vector,
            epsilon: float = 1e-4
        ) -> bpy.types.Bone:

            min_dist_sq = self.EPSILON * self.EPSILON
            min_bone = None

            for bone in armature.bones:

                dist_sq = (bone.head - position).length_squared

                if dist_sq > min_dist_sq:
                    continue

                min_dist_sq = dist_sq
                min_bone = bone

            return min_bone

        SUFFIX_START = '_h0'
        SUFFIX_END = '_h1'
        SUFFIX_POINT = '_pt'

        p0_co, p0_normal = self.point_last # _setup_nearest_point()
        p1_co, p1_normal = self.point_current

        p0_dir = \
        p1_dir = (p1_co - p0_co).normalized()

        if p0_normal is not None:
            p0_dir = (p0_dir - p0_normal * p0_dir.dot(p0_normal)).normalized()

        if p1_normal is not None:
            p1_dir = (p1_dir - p1_normal * p1_dir.dot(p1_normal)).normalized()

        eb = arm.edit_bones.new(name = 'Bbone')
        eb_start = arm.edit_bones.new(name = f'{eb.name}{SUFFIX_START}')
        eb_end = arm.edit_bones.new(name = f'{eb.name}{SUFFIX_END}')

        b_point_start = get_nearest_bone(arm, p0_co, self.EPSILON)
        b_point_end = get_nearest_bone(arm, p1_co, self.EPSILON)

        eb_point_start = arm.edit_bones.get(getattr(b_point_start, 'name', '')) \
            or arm.edit_bones.new(name = f'{eb.name}{SUFFIX_POINT}')
        eb_point_end = arm.edit_bones.get(getattr(b_point_end, 'name', '')) \
            or arm.edit_bones.new(name = f'{eb.name}{SUFFIX_POINT}')

        bone_names = (
            eb.name,
            eb_start.name,
            eb_end.name,
            eb_point_start.name,
            eb_point_end.name
        )

        # bcoll_bbones.assign(eb)
        # bcoll_handles.assign(eb_start)
        # bcoll_handles.assign(eb_end)
        # bcoll_points.assign(eb_point_start)
        # bcoll_points.assign(eb_point_end)

        eb.use_deform = True
        eb.parent = eb_start
        eb.head = p0_co
        eb.tail = p1_co
        eb.bbone_segments = 32
        eb.bbone_x = \
        eb.bbone_z = \
        eb.envelope_distance = \
        eb.head_radius = \
        eb.tail_radius = 0.0625 * self.SIZE_BB
        eb.bbone_handle_type_start = \
        eb.bbone_handle_type_end = 'TANGENT'
        eb.bbone_custom_handle_start = eb_start
        eb.bbone_custom_handle_end = eb_end
        eb.bbone_handle_use_ease_start = \
        eb.bbone_handle_use_ease_end = True

        eb_start.use_deform = False
        eb_start.parent = eb_point_start
        eb_start.head = eb.head
        eb_start.tail = eb.head + p0_dir
        eb_start.length = eb.length * 0.333 # 0.5 * self.SIZE_BB
        eb_start.bbone_x = \
        eb_start.bbone_z = \
        eb_start.envelope_distance = \
        eb_start.head_radius = \
        eb_start.tail_radius = 0.125 * self.SIZE_BB

        eb_end.use_deform = False
        eb_end.parent = eb_point_end
        eb_end.head = eb.tail
        eb_end.tail = eb.tail + p1_dir
        eb_end.length = eb.length * 0.333 # 0.5 * self.SIZE_BB
        eb_end.bbone_x = \
        eb_end.bbone_z = \
        eb_end.envelope_distance = \
        eb_end.head_radius = \
        eb_end.tail_radius = 0.125 * self.SIZE_BB

        if b_point_start is None:
            eb_point_start.use_deform = False
            eb_point_start.head = eb.head
            eb_point_start.tail = eb.head + Vector((0.0, 1.0, 0.0)) # world y-axis
            eb_point_start.length = 1.0 * self.SIZE_BB
            eb_point_start.bbone_x = \
            eb_point_start.bbone_z = \
            eb_point_start.envelope_distance = \
            eb_point_start.head_radius = \
            eb_point_start.tail_radius = 0.25 * self.SIZE_BB

        if b_point_end is None:
            eb_point_end.use_deform = False
            eb_point_end.head = eb.tail
            eb_point_end.tail = eb.tail + Vector((0.0, 1.0, 0.0)) # world y-axis
            eb_point_end.length = 1.0 * self.SIZE_BB
            eb_point_end.bbone_x = \
            eb_point_end.bbone_z = \
            eb_point_end.envelope_distance = \
            eb_point_end.head_radius = \
            eb_point_end.tail_radius = 0.25 * self.SIZE_BB

        #########
        # Pose mode.

        bpy.ops.object.mode_set(mode = 'POSE')

        COL_SELECT = (0.6, 0.9, 1.0)
        COL_ACTIVE = (0.7, 1.0, 1.0)

        COL_BBONE = (1.0, 1.0, 1.0)
        COL_HANDLE = (1.0, 1.0, 0.0)
        COL_POINT = (0.0, 1.0, 1.0)

        pb = obj.pose.bones[bone_names[0]]
        pb_start = obj.pose.bones[bone_names[1]]
        pb_end = obj.pose.bones[bone_names[2]]
        pb_point_start = obj.pose.bones[bone_names[3]]
        pb_point_end = obj.pose.bones[bone_names[4]]

        bcoll_bbones.assign(pb)
        bcoll_handles.assign(pb_start)
        bcoll_handles.assign(pb_end)
        bcoll_points.assign(pb_point_start)
        bcoll_points.assign(pb_point_end)

        pb.lock_location = \
        pb.lock_rotation = \
        pb.lock_scale = (True, ) * 3
        pb.lock_rotation_w = True
        pb.color.palette = 'CUSTOM'
        pb.color.custom.normal = COL_BBONE
        pb.color.custom.select = COL_SELECT
        pb.color.custom.active = COL_ACTIVE
        constraint = pb.constraints.new('STRETCH_TO')
        constraint.target = obj
        constraint.subtarget = pb_end.name

        pb_start.lock_location = (True, ) * 3
        pb_start.lock_scale = (True, False, True)
        pb_start.color.palette = 'CUSTOM'
        pb_start.color.custom.normal = COL_HANDLE
        pb_start.color.custom.select = COL_SELECT
        pb_start.color.custom.active = COL_ACTIVE
        pb_start.custom_shape = map_wgt['line']

        pb_end.lock_location = (True, ) * 3
        pb_end.lock_scale = (True, False, True)
        pb_end.color.palette = 'CUSTOM'
        pb_end.color.custom.normal = COL_HANDLE
        pb_end.color.custom.select = COL_SELECT
        pb_end.color.custom.active = COL_ACTIVE
        pb_end.custom_shape = map_wgt['line']
        pb_end.custom_shape_scale_xyz[1] *= -1.0

        pb_point_start.color.palette = 'CUSTOM'
        pb_point_start.color.custom.normal = COL_POINT
        pb_point_start.color.custom.select = COL_SELECT
        pb_point_start.color.custom.active = COL_ACTIVE
        pb_point_start.custom_shape = map_wgt['diamond']
        # constraint = pb_point_start.constraints.new('ARMATURE')
        # target = constraint.targets.new()
        # target.target = obj
        # target.subtarget = ''

        pb_point_end.color.palette = 'CUSTOM'
        pb_point_end.color.custom.normal = COL_POINT
        pb_point_end.color.custom.select = COL_SELECT
        pb_point_end.color.custom.active = COL_ACTIVE
        pb_point_end.custom_shape = map_wgt['diamond']
        # constraint = pb_point_end.constraints.new('ARMATURE')
        # target = constraint.targets.new()
        # target.target = obj
        # target.subtarget = ''

        #########
        # Finalize.

        # bpy.ops.object.mode_set(mode = 'EDIT')

        return None

    #########
    # Operator.

    @classmethod
    def poll(cls, context):
        return (
            not cls._handle
            and context.mode == 'POSE'
        )

    def invoke(self, context, event):

        if context.mode not in ('EDIT_ARMATURE', 'POSE'):
            return {'CANCELLED'}

        #########
        # Initialize

        self.point_current = None # (vec3_coord, vec3_normal)
        self.point_last = None # (vec3_coord, vec3_normal)

        cls = type(self) # self.__class__
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_bbonenet, (context, ), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self) # modal

        #########
        # Header.

        if area := context.area:
            area.header_text_set('LMB: Add Points | RMB/ESC: Exit')

        print_message('invoke')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        #########
        # Cancel.

        area = context.area
        mode = context.mode
        tool = context.workspace.tools.from_space_view3d_mode(mode)

        if area:
            area.tag_redraw() # TODO: Remove.

        if (
            area is None
            or mode not in ('EDIT_ARMATURE', 'POSE')
            or tool is None
            or tool.idname != SEI_WT_bbonenet.bl_idname
            or event.type == 'WINDOW_DEACTIVATE'
            or (event.type in ('RIGHTMOUSE', 'ESC') and event.value == 'PRESS')
        ):

            self._cancel(context)

            print_message('cancel')

            return {'CANCELLED'}

        #########
        # Modal.

        if event.type == 'MOUSEMOVE':

            # self.point_current = (event.mouse_region_x, event.mouse_region_y)
            self.point_current = self._setup_nearest_point(context, event)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            if self.point_last is None:

                self.point_last = self.point_current

                print_message('tool, start')

                return {'RUNNING_MODAL'}

            else:

                self._setup_bbone(context)
                self._cancel(context)

                print_message('tool, end')

                # NOTE: Reset the operator so undo is available.
                bpy.ops.sei.bbonenet(
                    'INVOKE_DEFAULT',
                    SIZE_PX = self.SIZE_PX,
                    SIZE_BB = self.SIZE_BB,
                    EPSILON = self.EPSILON
                )

                return {'FINISHED'}

        return {'PASS_THROUGH'}

class SEI_WT_bbonenet(bpy.types.WorkSpaceTool):
    # ./scripts/startup/bl_ui/space_toolsystem_common.py
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'POSE' # less cluttered than EDIT_ARMATURE
    bl_idname = 'sei.bbonenet_tool'
    bl_label = 'Bbonenet'
    bl_description = 'Construct bendy bones as a net'
    bl_icon = 'ops.curve.extrude_move'
    bl_widget = None
    bl_keymap = (
        ('sei.bbonenet', {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties('sei.bbonenet')

        layout.prop(props, 'SIZE_PX', text = 'Radius', slider = True)
        layout.separator()

        layout.label(text = '', icon = 'BONE_DATA')
        row = layout.row(align = True)
        row.prop(props, 'SIZE_BB', text = 'Scale')
        row.prop(props, 'EPSILON', text = 'Radius')

# ===========================

def register():

    bpy.utils.register_class(SEI_OT_bbonenet)
    bpy.utils.register_tool(SEI_WT_bbonenet, separator = True)

    # try:
    #     bpy.utils.register_tool(SEI_WT_bbonenet, separator = True)
    # except:
    #     pass

def unregister():

    bpy.utils.unregister_class(SEI_OT_bbonenet)
    bpy.utils.unregister_tool(SEI_WT_bbonenet)

if __name__ == "__main__": # debug; live edit
    register()
