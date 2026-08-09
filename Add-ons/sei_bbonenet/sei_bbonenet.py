import bpy
import gpu

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

bl_info = {
    "name": "Sei BBoneNet",
    "author": "Seilotte",
    "version": (0, 2, 0),
    "blender": (5, 2, 0),
    "location": "3D View > Toolbar > Pose Mode",
    "description": "Construct bézier or bendy bones as a net",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/sei_bbonenet",
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
        description = 'Pixel radius for nearest element detection',
        default = 12,
        min = 1,
        max = 1000,
        soft_max = 100,
        subtype = 'PIXEL'
    )

    B_SNAP: bpy.props.BoolProperty(
        name = 'Snap',
        description = 'Snap to the current armature',
        default = False
    )

    B_SNAP_TYPE: bpy.props.EnumProperty(
        name = 'Type',
        description = 'Select Vertex or Face normal',
        items = [('VERTEX', 'Vertex', '', 0), ('FACE', 'Face', '', 1)],
        default = 0
    )

    B_TYPE: bpy.props.EnumProperty(
        name = 'Type',
        description = 'Select Bézier or Bendy bone type',
        items = [('BEZIER', 'Bézier', '', 0), ('BENDY', 'B-Bone', '', 1)],
        default = 0
    )

    B_SEGMENTS: bpy.props.IntProperty(
        name = 'Bone Segments',
        description = 'Number of subdivision of bone',
        default = 24,
        min = 1,
        max = 32
    )

    B_SCALE: bpy.props.FloatProperty(
        name = 'Scale',
        description = 'Scaling of the bones',
        default = 0.01,
        min = 1e-6,
        subtype = 'DISTANCE'
    )

    B_EPSILON: bpy.props.FloatProperty(
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

        return None

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

    def _draw_bbonenet(self, context, shaders: tuple) -> None:

        if context.mode not in ('EDIT_ARMATURE', 'POSE'):
            return

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
        gpu.state.point_size_set(11.0) # opengl; TODO: x * ui_scale

        if self.point_current: # _setup_nearest_point()

            shader = shaders[0] # point
            shader.bind()

            # shader.uniform_float('ModelViewProjectionMatrix', gpu.matrix.)
            shader.uniform_float('colour', (0.0, 1.0, 1.0, 1.0))

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': [self.point_current[0]]})
            batch.draw(shader)

        if self.point_last:

            shader = shaders[0] # point
            shader.bind()

            shader.uniform_float('colour', (1.0, 1.0, 0.0, 1.0))

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': [self.point_last[0]]})
            batch.draw(shader)

        if self.point_current and self.point_last:

            shader = shaders[1] # lines
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

        if self.B_SNAP:

            # TODO; Loop over all armatures?
            obj = context.object
            arm = obj.data

            obj_matrix = obj.matrix_world

            min_dist_sq = self.SIZE_PX * self.SIZE_PX
            min_b_ws = None

            for bone in arm.bones:

                b_ws = obj_matrix @ bone.tail
                b_ss = view3d_utils.location_3d_to_region_2d(
                    region, rv3d, b_ws)

                if b_ss is not None:

                    dist_sq = (b_ss - mouse_ss).length_squared

                    if dist_sq < min_dist_sq:

                        min_dist_sq = dist_sq
                        min_b_ws = b_ws

                b_ws = obj_matrix @ bone.head
                b_ss = view3d_utils.location_3d_to_region_2d(
                    region, rv3d, b_ws)

                if b_ss is not None:

                    dist_sq = (b_ss - mouse_ss).length_squared

                    if dist_sq < min_dist_sq:

                        min_dist_sq = dist_sq
                        min_b_ws = b_ws

            if min_b_ws is not None:
                mouse_ws = min_b_ws.copy()

        #########
        # Get nearest scene mesh point.

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

        _, hit_ls, hit_face_normal, hit_face_index = obj.ray_cast(
            obj_matrix_inv @ ro_ws, obj_matrix_inv.to_3x3() @ rd_ws)

        if hit_face_index < 0: # no hit
            return (mouse_ws, None)

        mouse_ws = obj_matrix @ hit_ls

        min_dist_sq = self.SIZE_PX * self.SIZE_PX
        min_vert_ws = None
        min_vert_normal = None

        for vi in obj.data.polygons[hit_face_index].vertices:

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

        if self.B_SNAP_TYPE == 'FACE':
            min_vert_normal = (obj_matrix.to_3x3() @ hit_face_normal).copy()

        return (min_vert_ws.copy(), min_vert_normal)

    def _setup_new_bones(self, context) -> None:

        if context.mode != 'POSE': # SEI_WT_net_bone -> bl_context_mode
            return None

        if self.point_last is self.point_current:
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
        # Bone.

        @staticmethod
        def get_nearest_bone(
            armature: bpy.types.Armature,
            position: Vector,
            epsilon: float = 1e-4
        ) -> bpy.types.Bone:

            min_dist_sq = epsilon * epsilon
            min_bone = None

            for bone in armature.bones:

                if (
                    self.B_TYPE == 'BEZIER'
                    and (bone.name.endswith('_line')
                    or bone.name.startswith('BBézier'))
                ):
                    continue

                dist_sq = (bone.head - position).length_squared

                if dist_sq > min_dist_sq:
                    continue

                min_dist_sq = dist_sq
                min_bone = bone

            return min_bone

        SUFFIX_H0 = '_h0' # handle start
        SUFFIX_H1 = '_h1' # handle end
        SUFFIX_P0 = '_p0' # point start
        SUFFIX_P1 = '_p1' # point end

        COL_SELECT = (0.6, 0.9, 1.0)
        COL_ACTIVE = (0.7, 1.0, 1.0)

        COL_NET = (1.0, 1.0, 1.0)
        COL_HANDLE = (1.0, 1.0, 0.0)
        COL_POINT = (0.0, 1.0, 1.0)

        p0_co, p0_normal = self.point_last # _setup_nearest_point()
        p1_co, p1_normal = self.point_current

        # NOTE: Not before due to `_draw_net()`.
        obj_matrix_inv = obj.matrix_world.inverted()
        obj_matrix_inv_3x3 = obj_matrix_inv.to_3x3()

        p0_co = obj_matrix_inv @ p0_co
        p1_co = obj_matrix_inv @ p1_co
        p0_normal = obj_matrix_inv_3x3 @ p0_normal if p0_normal else None
        p1_normal = obj_matrix_inv_3x3 @ p1_normal if p1_normal else None

        del obj_matrix_inv, obj_matrix_inv_3x3

        b_p0 = get_nearest_bone(arm, p0_co, self.B_EPSILON) # next()?
        b_p1 = get_nearest_bone(arm, p1_co, self.B_EPSILON)

        p0_dir = \
        p1_dir = (p1_co - p0_co).normalized()

        if p0_normal is not None:
            p0_dir = (p0_dir - p0_normal * p0_dir.dot(p0_normal)).normalized()

        if p1_normal is not None:
            p1_dir = (p1_dir - p1_normal * p1_dir.dot(p1_normal)).normalized()

        ###

        if self.B_TYPE == 'BENDY':

            #########
            # Edit mode.

            bpy.ops.object.mode_set(mode = 'EDIT')

            eb = arm.edit_bones.new(name = 'Bendy')

            eb_h0 = arm.edit_bones.new(name = f'{eb.name}{SUFFIX_H0}')
            eb_h1 = arm.edit_bones.new(name = f'{eb.name}{SUFFIX_H1}')

            eb_p0 = arm.edit_bones.get(getattr(b_p0, 'name', '')) \
                or arm.edit_bones.new(name = f'{eb.name}{SUFFIX_P0}')
            eb_p1 = arm.edit_bones.get(getattr(b_p1, 'name', '')) \
                or arm.edit_bones.new(name = f'{eb.name}{SUFFIX_P1}')

            bone_names = (
                eb.name,
                eb_h0.name,
                eb_h1.name,
                eb_p0.name,
                eb_p1.name
            )

            # bcoll_bbones.assign(eb)
            # bcoll_handles.assign(eb_h0)
            # bcoll_handles.assign(eb_h1)
            # bcoll_points.assign(eb_p0)
            # bcoll_points.assign(eb_p1)

            eb.use_deform = True
            eb.parent = eb_h0
            eb.head = p0_co
            eb.tail = p1_co
            eb.bbone_segments = self.B_SEGMENTS
            eb.bbone_x = \
            eb.bbone_z = \
            eb.envelope_distance = \
            eb.head_radius = \
            eb.tail_radius = 0.0625 * self.B_SCALE
            eb.bbone_handle_type_start = \
            eb.bbone_handle_type_end = 'TANGENT'
            eb.bbone_custom_handle_start = eb_h0
            eb.bbone_custom_handle_end = eb_h1
            eb.bbone_handle_use_ease_start = \
            eb.bbone_handle_use_ease_end = True

            eb_h0.use_deform = False
            eb_h0.parent = eb_p0
            eb_h0.head = eb.head
            eb_h0.tail = eb.head + p0_dir
            eb_h0.length = eb.length * 0.333 # 0.5 * self.B_SCALE
            eb_h0.bbone_x = \
            eb_h0.bbone_z = \
            eb_h0.envelope_distance = \
            eb_h0.head_radius = \
            eb_h0.tail_radius = 0.125 * self.B_SCALE

            eb_h1.use_deform = False
            eb_h1.parent = eb_p1
            eb_h1.head = eb.tail
            eb_h1.tail = eb.tail + p1_dir
            eb_h1.length = eb.length * 0.333 # 0.5 * self.B_SCALE
            eb_h1.bbone_x = \
            eb_h1.bbone_z = \
            eb_h1.envelope_distance = \
            eb_h1.head_radius = \
            eb_h1.tail_radius = 0.125 * self.B_SCALE

            if b_p0 is None:
                eb_p0.use_deform = False
                eb_p0.head = eb.head
                eb_p0.tail = eb.head + Vector((0.0, 1.0, 0.0)) # world y-axis
                eb_p0.length = 1.0 * self.B_SCALE
                eb_p0.bbone_x = \
                eb_p0.bbone_z = \
                eb_p0.envelope_distance = \
                eb_p0.head_radius = \
                eb_p0.tail_radius = 0.25 * self.B_SCALE

            if b_p1 is None:
                eb_p1.use_deform = False
                eb_p1.head = eb.tail
                eb_p1.tail = eb.tail + Vector((0.0, 1.0, 0.0)) # world y-axis
                eb_p1.length = 1.0 * self.B_SCALE
                eb_p1.bbone_x = \
                eb_p1.bbone_z = \
                eb_p1.envelope_distance = \
                eb_p1.head_radius = \
                eb_p1.tail_radius = 0.25 * self.B_SCALE

            #########
            # Pose mode.

            bpy.ops.object.mode_set(mode = 'POSE')

            pb = obj.pose.bones[bone_names[0]]
            pb_h0 = obj.pose.bones[bone_names[1]]
            pb_h1 = obj.pose.bones[bone_names[2]]
            pb_p0 = obj.pose.bones[bone_names[3]]
            pb_p1 = obj.pose.bones[bone_names[4]]

            bcoll_bbones.assign(pb)
            bcoll_handles.assign(pb_h0)
            bcoll_handles.assign(pb_h1)
            bcoll_points.assign(pb_p0)
            bcoll_points.assign(pb_p1)

            pb.lock_location = \
            pb.lock_rotation = \
            pb.lock_scale = (True, ) * 3
            pb.lock_rotation_w = True
            pb.color.palette = 'CUSTOM'
            pb.color.custom.normal = COL_NET
            pb.color.custom.select = COL_SELECT
            pb.color.custom.active = COL_ACTIVE
            constraint = pb.constraints.new('STRETCH_TO')
            constraint.target = obj
            constraint.subtarget = pb_h1.name

            pb_h0.lock_location = (True, ) * 3
            pb_h0.lock_scale = (True, False, True)
            pb_h0.color.palette = 'CUSTOM'
            pb_h0.color.custom.normal = COL_HANDLE
            pb_h0.color.custom.select = COL_SELECT
            pb_h0.color.custom.active = COL_ACTIVE
            pb_h0.custom_shape = map_wgt['line']

            pb_h1.lock_location = (True, ) * 3
            pb_h1.lock_scale = (True, False, True)
            pb_h1.color.palette = 'CUSTOM'
            pb_h1.color.custom.normal = COL_HANDLE
            pb_h1.color.custom.select = COL_SELECT
            pb_h1.color.custom.active = COL_ACTIVE
            pb_h1.custom_shape = map_wgt['line']
            pb_h1.custom_shape_scale_xyz[1] *= -1.0

            pb_p0.color.palette = 'CUSTOM'
            pb_p0.color.custom.normal = COL_POINT
            pb_p0.color.custom.select = COL_SELECT
            pb_p0.color.custom.active = COL_ACTIVE
            pb_p0.custom_shape = map_wgt['diamond']
            # constraint = pb_p0.constraints.new('ARMATURE')
            # target = constraint.targets.new()
            # target.target = obj
            # target.subtarget = ''

            pb_p1.color.palette = 'CUSTOM'
            pb_p1.color.custom.normal = COL_POINT
            pb_p1.color.custom.select = COL_SELECT
            pb_p1.color.custom.active = COL_ACTIVE
            pb_p1.custom_shape = map_wgt['diamond']
            # constraint = pb_p1.constraints.new('ARMATURE')
            # target = constraint.targets.new()
            # target.target = obj
            # target.subtarget = ''

        elif self.B_TYPE == 'BEZIER':

            @staticmethod
            def get_bezier_weights(t: float) -> tuple:

                w0 = (1 - t) ** 3
                w1 = 3 * t * (1 - t) ** 2
                w2 = 3 * t**2 * (1 - t)
                w3 = t**3

                return (w0, w1, w2, w3)

            #########
            # Edit mode.

            bpy.ops.object.mode_set(mode = 'EDIT')

            eb_none = arm.edit_bones.get('none') \
                or arm.edit_bones.new(name = 'none') # for constraints

            eb = arm.edit_bones.new(name = 'Bézier')

            eb_h0 = arm.edit_bones.new(name = f'{eb.name}{SUFFIX_H0}')
            eb_h1 = arm.edit_bones.new(name = f'{eb.name}{SUFFIX_H1}')

            eb_p0 = arm.edit_bones.get(getattr(b_p0, 'name', '')) \
                or arm.edit_bones.new(name = f'{eb.name}{SUFFIX_P0}')
            eb_p1 = arm.edit_bones.get(getattr(b_p1, 'name', '')) \
                or arm.edit_bones.new(name = f'{eb.name}{SUFFIX_P1}')

            eb_h0_line = arm.edit_bones.new(name = f'{eb_h0.name}_line')
            eb_h1_line = arm.edit_bones.new(name = f'{eb_h1.name}_line')

            bone_names = [
                eb_h0.name,
                eb_h1.name,
                eb_p0.name,
                eb_p1.name,
                eb_h0_line.name,
                eb_h1_line.name
            ]

            eb_none.use_deform = False
            eb_none.hide_select = True
            eb_none.head[:] = 0.0, 0.0, 0.0
            eb_none.tail[:] = 0.0, 0.01, 0.0 # world y-axis
            eb_none.bbone_x = \
            eb_none.bbone_z = \
            eb_none.envelope_distance = \
            eb_none.head_radius = \
            eb_none.tail_radius = 0.0025

            eb_h0.use_deform = False
            eb_h0.parent = eb_p0
            eb_h0.head = p0_co + p0_dir * (p1_co - p0_co).length * 0.333
            eb_h0.tail = eb_h0.head + Vector((0.0, 1.0, 0.0)) # world y-axis
            eb_h0.length = 0.5 * self.B_SCALE
            eb_h0.bbone_x = \
            eb_h0.bbone_z = \
            eb_h0.envelope_distance = \
            eb_h0.head_radius = \
            eb_h0.tail_radius = 0.125 * self.B_SCALE

            eb_h1.use_deform = False
            eb_h1.parent = eb_p1
            eb_h1.head = p1_co - p1_dir * (p1_co - p0_co).length * 0.333
            eb_h1.tail = eb_h1.head + Vector((0.0, 1.0, 0.0)) # world y-axis
            eb_h1.length = 0.5 * self.B_SCALE
            eb_h1.bbone_x = \
            eb_h1.bbone_z = \
            eb_h1.envelope_distance = \
            eb_h1.head_radius = \
            eb_h1.tail_radius = 0.125 * self.B_SCALE

            if b_p0 is None:
                eb_p0.use_deform = False
                eb_p0.head = p0_co
                eb_p0.tail = p0_co + Vector((0.0, 1.0, 0.0)) # world y-axis
                eb_p0.length = 1.0 * self.B_SCALE
                eb_p0.bbone_x = \
                eb_p0.bbone_z = \
                eb_p0.envelope_distance = \
                eb_p0.head_radius = \
                eb_p0.tail_radius = 0.25 * self.B_SCALE

            if b_p1 is None:
                eb_p1.use_deform = False
                eb_p1.head = p1_co
                eb_p1.tail = p1_co + Vector((0.0, 1.0, 0.0)) # world y-axis
                eb_p1.length = 1.0 * self.B_SCALE
                eb_p1.bbone_x = \
                eb_p1.bbone_z = \
                eb_p1.envelope_distance = \
                eb_p1.head_radius = \
                eb_p1.tail_radius = 0.25 * self.B_SCALE

            eb_h0_line.use_deform = False
            eb_h0_line.parent = eb_p0
            eb_h0_line.head = eb_p0.head
            eb_h0_line.tail = eb_h0.head
            eb_h0_line.bbone_x = \
            eb_h0_line.bbone_z = \
            eb_h0_line.envelope_distance = \
            eb_h0_line.head_radius = \
            eb_h0_line.tail_radius = 0.0625 * self.B_SCALE

            eb_h1_line.use_deform = False
            eb_h1_line.parent = eb_p1
            eb_h1_line.head = eb_p1.head
            eb_h1_line.tail = eb_h1.head
            eb_h1_line.bbone_x = \
            eb_h1_line.bbone_z = \
            eb_h1_line.envelope_distance = \
            eb_h1_line.head_radius = \
            eb_h1_line.tail_radius = 0.0625 * self.B_SCALE

            for i in range(self.B_SEGMENTS):

                if i < 1:
                    eb_b = eb
                    eb_b.name = f'B{eb_b.name}' # get_nearest_bone()

                else:
                    eb_b = arm.edit_bones.new(name = f'{eb.name}_{i}')

                # eb_b.name = f'B{eb_b.name}' # for get_nearest_bone()
                eb_b.use_deform = True
                eb_b.bbone_x = \
                eb_b.bbone_z = \
                eb_b.envelope_distance = \
                eb_b.head_radius = \
                eb_b.tail_radius = 0.0625 * self.B_SCALE

                ebones = (eb_p0, eb_h0, eb_h1, eb_p1)
                weights = get_bezier_weights(i / self.B_SEGMENTS) # p0 h0 h1 p1
                weights_next = get_bezier_weights((i + 1) / self.B_SEGMENTS)

                for i in range(4):

                    eb_b.head += ebones[i].head * weights[i]
                    eb_b.tail += ebones[i].head * weights_next[i]

                bone_names.append(eb_b.name)

            #########
            # Pose mode.

            bpy.ops.object.mode_set(mode = 'POSE')

            pb_none = obj.pose.bones['none']
            pb_h0 = obj.pose.bones[bone_names[0]]
            pb_h1 = obj.pose.bones[bone_names[1]]
            pb_p0 = obj.pose.bones[bone_names[2]]
            pb_p1 = obj.pose.bones[bone_names[3]]
            pb_h0_line = obj.pose.bones[bone_names[4]]
            pb_h1_line = obj.pose.bones[bone_names[5]]

            bcoll_bbones.assign(pb_none)
            bcoll_handles.assign(pb_h0)
            bcoll_handles.assign(pb_h1)
            bcoll_points.assign(pb_p0)
            bcoll_points.assign(pb_p1)
            bcoll_handles.assign(pb_h0_line)
            bcoll_handles.assign(pb_h1_line)

            pb_none.lock_rotation = \
            pb_none.lock_scale = (True, ) * 3
            pb_none.lock_rotation_w = True

            for index, b_name in enumerate(bone_names[6:]):

                pb = obj.pose.bones[b_name]

                bcoll_bbones.assign(pb)

                pb.lock_location = \
                pb.lock_rotation = \
                pb.lock_scale = (True, ) * 3
                pb.lock_rotation_w = True
                pb.color.palette = 'CUSTOM'
                pb.color.custom.normal = COL_NET
                pb.color.custom.select = COL_SELECT
                pb.color.custom.active = COL_ACTIVE

                pbones = (pb_p0, pb_h0, pb_h1, pb_p1)
                weights = get_bezier_weights(index / self.B_SEGMENTS) # p0 h0 h1 p1

                constraint = pb.constraints.new('COPY_LOCATION')
                constraint.name = 'None'
                constraint.target = obj
                constraint.subtarget = 'none'
                constraint.target_space = \
                constraint.owner_space = 'POSE'

                for i in range(4):

                    constraint = pb.constraints.new('COPY_LOCATION')
                    constraint.target = obj
                    constraint.subtarget = pbones[i].name
                    constraint.use_offset = True
                    constraint.influence = weights[i]
                    constraint.target_space = \
                    constraint.owner_space = 'POSE'

                constraint = pb.constraints.new('STRETCH_TO')
                constraint.target = obj
                constraint.subtarget = bone_names[index + 7] \
                    if index < len(bone_names) - 8 else pb_p1.name

            pb_h0.lock_rotation = \
            pb_h0.lock_scale = (True, ) * 3
            pb_h0.lock_rotation_w = True
            pb_h0.color.palette = 'CUSTOM'
            pb_h0.color.custom.normal = COL_HANDLE
            pb_h0.color.custom.select = COL_SELECT
            pb_h0.color.custom.active = COL_ACTIVE
            pb_h0.custom_shape = map_wgt['diamond']

            pb_h1.lock_rotation = \
            pb_h1.lock_scale = (True, ) * 3
            pb_h1.lock_rotation_w = True
            pb_h1.color.palette = 'CUSTOM'
            pb_h1.color.custom.normal = COL_HANDLE
            pb_h1.color.custom.select = COL_SELECT
            pb_h1.color.custom.active = COL_ACTIVE
            pb_h1.custom_shape = map_wgt['diamond']

            pb_h0_line.lock_location = \
            pb_h0_line.lock_rotation = \
            pb_h0_line.lock_scale = (True, ) * 3
            pb_h0_line.lock_rotation_w = True
            pb_h0_line.color.palette = 'CUSTOM'
            pb_h0_line.color.custom.normal = COL_HANDLE
            pb_h0_line.color.custom.select = COL_SELECT
            pb_h0_line.color.custom.active = COL_ACTIVE
            pb_h0_line.custom_shape = map_wgt['line']
            constraint = pb_h0_line.constraints.new('STRETCH_TO')
            constraint.target = obj
            constraint.subtarget = pb_h0.name
            constraint.volume = 'NO_VOLUME'

            pb_h1_line.lock_location = \
            pb_h1_line.lock_rotation = \
            pb_h1_line.lock_scale = (True, ) * 3
            pb_h1_line.lock_rotation_w = True
            pb_h1_line.color.palette = 'CUSTOM'
            pb_h1_line.color.custom.normal = COL_HANDLE
            pb_h1_line.color.custom.select = COL_SELECT
            pb_h1_line.color.custom.active = COL_ACTIVE
            pb_h1_line.custom_shape = map_wgt['line']
            constraint = pb_h1_line.constraints.new('STRETCH_TO')
            constraint.target = obj
            constraint.subtarget = pb_h1.name
            constraint.volume = 'NO_VOLUME'

            pb_p0.color.palette = 'CUSTOM'
            pb_p0.color.custom.normal = COL_POINT
            pb_p0.color.custom.select = COL_SELECT
            pb_p0.color.custom.active = COL_ACTIVE
            pb_p0.custom_shape = map_wgt['diamond']
            # constraint = pb_p0.constraints.new('ARMATURE')
            # target = constraint.targets.new()
            # target.target = obj
            # target.subtarget = ''

            pb_p1.color.palette = 'CUSTOM'
            pb_p1.color.custom.normal = COL_POINT
            pb_p1.color.custom.select = COL_SELECT
            pb_p1.color.custom.active = COL_ACTIVE
            pb_p1.custom_shape = map_wgt['diamond']
            # constraint = pb_p1.constraints.new('ARMATURE')
            # target = constraint.targets.new()
            # target.target = obj
            # target.subtarget = ''

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

        # Handlers.

        shaders = (
            self._setup_shader_point_uniform(), # gpu.shader.from_builtin('POINT_UNIFORM_COLOR')
            gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        )
        cls = type(self) # self.__class__
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_bbonenet, (context, shaders), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self) # modal

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

            self.point_current = self._setup_nearest_point(context, event)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            if self.point_last is None:

                self.point_last = self.point_current

                print_message('tool, start')

                return {'RUNNING_MODAL'}

            else:

                self._setup_new_bones(context)
                self._cancel(context)

                print_message('tool, end')

                # NOTE: Reset the operator so undo is available.
                bpy.ops.sei.bbonenet(
                    'INVOKE_DEFAULT',
                    SIZE_PX = self.SIZE_PX,
                    B_SNAP = self.B_SNAP,
                    B_SNAP_TYPE = self.B_SNAP_TYPE,
                    B_TYPE = self.B_TYPE,
                    B_SEGMENTS = self.B_SEGMENTS,
                    B_SCALE = self.B_SCALE,
                    B_EPSILON = self.B_EPSILON
                )

                return {'FINISHED'}

        return {'PASS_THROUGH'}

class SEI_PT_bbonenet_popover(bpy.types.Panel):
    '''
    Popover panel for extra options.
    '''
    bl_idname = 'SEI_PT_bbonenet_popover'
    bl_label = 'Extra Options'
    bl_description = 'Popover panel for extra options'
    bl_space_type = 'TOPBAR'
    bl_region_type = 'HEADER'

    def draw(self, context):

        # NOTE: `WorkSpaceTool` is 'VIEW_3D'.
        mode = context.mode
        tool = context.workspace.tools.from_space_view3d_mode(mode)

        if tool is None:
            return

        # Draw.
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = tool.operator_properties('sei.bbonenet')

        row = layout.row()
        row.prop(props, 'B_TYPE', expand = True)

        col = layout.column()
        col.prop(props, 'B_SEGMENTS', text = 'Segments')
        col.prop(props, 'B_SCALE')

        col.separator()

        col.prop(props, 'B_EPSILON')
        col.row().prop(props, 'B_SNAP_TYPE', text = 'Normal', expand = True)

class SEI_WT_bbonenet(bpy.types.WorkSpaceTool):
    '''
    ./scripts/startup/bl_ui/space_toolsystem_common.py
    '''
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

        row = layout.row(align = True)
        row.prop(props, 'SIZE_PX', text = 'Radius', slider = True)
        row.prop(props, 'B_SNAP', text = '',
            icon = 'SNAP_ON' if props.B_SNAP else 'SNAP_OFF')

        layout.separator()

        row = layout.row()
        row.ui_units_x = 7
        row.popover('SEI_PT_bbonenet_popover', text = 'Bone',
            icon = 'BONE_DATA' if props.B_TYPE == 'BBONE' else 'CURVE_DATA')

# ===========================

def register():

    bpy.utils.register_class(SEI_OT_bbonenet)
    bpy.utils.register_class(SEI_PT_bbonenet_popover)
    bpy.utils.register_tool(SEI_WT_bbonenet, separator = True)

    # try:
    #     bpy.utils.register_tool(SEI_WT_bbonenet, separator = True)
    # except:
    #     pass

def unregister():

    bpy.utils.unregister_class(SEI_OT_bbonenet)
    bpy.utils.unregister_class(SEI_PT_bbonenet_popover)
    bpy.utils.unregister_tool(SEI_WT_bbonenet)

if __name__ == "__main__": # debug; live edit
    register()
