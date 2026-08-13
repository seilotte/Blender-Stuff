import bpy
import gpu

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

bl_info = {
    "name": "Sei SurfaceNet",
    "author": "Seilotte",
    "version": (0, 1, 1),
    "blender": (5, 2, 0),
    "location": "3D View > Toolbar > Edit Mode",
    "description": "Construct nurbs surfaces as a net",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/sei_net",
    "doc_url": "https://github.com/seilotte/Blender-Stuff/issues",
    "category": "Workflow",
}

DEBUG_MODE = False

def print_message(message: str = "") -> None:
    if DEBUG_MODE is True:
        print(f'Sei surfacenet: {message}')

class SEI_OT_surfacenet(bpy.types.Operator):
    bl_idname = 'sei.surfacenet'
    bl_label = 'Surfacenet'
    bl_description = 'Construct nurbs Surfaces as a net'
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

    S_SNAP: bpy.props.BoolProperty(
        name = 'Snap',
        description = 'Snap to the current nurbs surface',
        default = False
    )

    S_SNAP_TYPE: bpy.props.EnumProperty(
        name = 'Type',
        description = 'Select Vertex or Face normal',
        items = [('VERTEX', 'Vertex', '', 0), ('FACE', 'Face', '', 1)],
        default = 0
    )

    S_SEGMENTS: bpy.props.IntProperty(
        name = 'Segments',
        description = 'Number of subdivision of surface',
        default = 4,
        min = 1,
        max = 64
    )

    S_ARMATURE: bpy.props.StringProperty(
        name = 'Target',
        description = 'Select the target armature object name',
        default = '',
        search = lambda self, context, edit_text: (
            obj.name
            for obj in bpy.data.objects[:]
            if obj.type == 'ARMATURE'
            and edit_text.lower() in obj.name.lower()
        )
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
        default = 1e-4,
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
        self.points = []

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

    def _draw_surfacenet(self, context, shaders: tuple) -> None:

        if context.mode != 'EDIT_SURFACE':
            return

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('ALPHA')
        gpu.state.point_size_set(11.0) # opengl; TODO: x * ui_scale

        points = [p[0] for p in self.points if p]

        #########
        # Points.

        if self.point_current: # _setup_nearest_point()

            shader = shaders[0] # point
            shader.bind()

            # shader.uniform_float('ModelViewProjectionMatrix', gpu.matrix.)
            shader.uniform_float('colour', (0.0, 1.0, 1.0, 1.0))

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': [self.point_current[0]]})
            batch.draw(shader)

        if points:

            shader = shaders[0] # point
            shader.bind()

            shader.uniform_float('colour', (1.0, 1.0, 0.0, 1.0))

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': points})
            batch.draw(shader)

        #########
        # Lines.

        if self.point_current and points:

            shader = shaders[1] # lines
            shader.bind()

            shader.uniform_float('color', (1.0, 1.0, 0.0, 1.0))
            shader.uniform_float('lineWidth', 2.0)
            shader.uniform_float('viewportSize', gpu.state.viewport_get()[2:])

            batch = batch_for_shader(
                shader, 'LINES', {'pos': [points[-1], self.point_current[0]]})
            batch.draw(shader)

        #########
        # Tris.

        if self.point_current and points:

            points.append(self.point_current[0])

            shader = shaders[2] # tris
            shader.bind()

            shader.uniform_float('color', (1.0, 1.0, 0.0, 0.1))

            batch = batch_for_shader(
                shader, 'TRI_FAN', {'pos': points})
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
        # Get nearest surface point.

        if self.S_SNAP:

            # TODO: Loop over all surfaces?
            obj = context.object
            curve = obj.data

            obj_matrix = obj.matrix_world

            min_dist_sq = self.SIZE_PX * self.SIZE_PX
            min_p_ws = None

            for spline in curve.splines:
                for point in spline.points:

                    p_ws = obj_matrix @ Vector(point.co[:-1]) # vec4 -> vec3
                    p_ss = view3d_utils.location_3d_to_region_2d(
                        region, rv3d, p_ws)

                    if p_ss is None:
                        continue

                    dist_sq = (p_ss - mouse_ss).length_squared

                    if dist_sq > min_dist_sq:
                        continue

                    min_dist_sq = dist_sq
                    min_p_ws = p_ws

            if min_p_ws is not None:
                mouse_ws = min_p_ws.copy()

        #########
        # Get nearest scene mesh point.

        ro_ws = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, mouse_ss)

        rd_ws = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, mouse_ss)

        depsgraph = context.evaluated_depsgraph_get()

        # NOTE: There is no way to only do
        # `scene.ray_cast()` against `MESH`.
        hit_ws = \
        hit_face_normal = \
        hit_face_index = None

        for dup in depsgraph.object_instances:

            obj = dup.instance_object if dup.is_instance else dup.object

            if obj.type != 'MESH':
                continue

            obj_matrix = obj.matrix_world
            obj_matrix_inv = obj_matrix.inverted()

            _, hit_ls, normal, index = obj.ray_cast(
                obj_matrix_inv @ ro_ws, obj_matrix_inv.to_3x3() @ rd_ws)

            if index < 0: # no hit
                continue

            hit_ws = obj_matrix @ hit_ls
            hit_face_normal = normal
            hit_face_index = index

            break

        if hit_face_index is None: # no hit
            return (mouse_ws, None)

        mouse_ws = hit_ws.copy()

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

        if self.S_SNAP_TYPE == 'FACE':
            min_vert_normal = (obj_matrix.to_3x3() @ hit_face_normal).copy()

        return (min_vert_ws.copy(), min_vert_normal)

    def _setup_armature(
        self,
        context,
        obj_surface: bpy.types.Object,
        points: list
    ) -> None:

        @staticmethod
        def set_active_object(context, obj: bpy.types.Object) -> None:

            bpy.ops.object.mode_set(mode = 'OBJECT')

            bpy.ops.object.select_all(action = 'DESELECT')
            obj.select_set(True)

            context.view_layer.objects.active = obj

            return None

        @staticmethod
        def setup_modifiers(
            obj_surface: bpy.types.Object,
            obj_armature: bpy.types.Object
        ) -> None:

            # NOTE: Assume the first modifier found is used for our purpose.
            mods = obj_surface.modifiers

            modifier = \
                next((m for m in mods if m.type == 'ARMATURE'), None) \
                or mods.new('Armature', 'ARMATURE')

            modifier.use_apply_on_spline = True
            modifier.object = obj_armature
            modifier.use_vertex_groups = False
            modifier.use_bone_envelopes = True

            mods.move(mods.find(modifier.name), 0)

            return None

        @staticmethod
        def setup_widgets() -> dict:

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
                    vertices = [(-0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.5, 0.0, 0.0), (0.0, -0.5, 0.0), (0.0, 0.0, -0.5), (0.0, 0.0, 0.5), (0.0, 0.8, 0.0)],
                    edges = [(0, 4), (4, 3), (3, 0), (3, 5), (5, 0), (0, 1), (1, 4), (5, 1), (2, 3), (4, 2), (2, 5), (1, 2), (1, 6)],
                    faces = [(0, 4, 3), (0, 3, 5), (0, 1, 4), (0, 5, 1), (2, 3, 4), (2, 5, 3), (1, 2, 4), (1, 5, 2)]
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

            return map_wgt

        @staticmethod
        def get_nearest_edit_bone(
            armature: bpy.types.Armature,
            position: Vector,
            epsilon: float = 1e-4
        ) -> bpy.types.EditBone:

            min_dist_sq = epsilon * epsilon
            min_ebone = None

            for ebone in armature.edit_bones:

                if ebone.name.endswith('_line'):
                    continue

                dist_sq = (ebone.head - position).length_squared

                if dist_sq > min_dist_sq:
                    continue

                min_dist_sq = dist_sq
                min_ebone = ebone

            return min_ebone

        #########
        # Armature.
        # TODO: Delete the respective bones when a spline is deleted.

        obj_armature = bpy.data.objects.get(self.S_ARMATURE)
        arm = getattr(obj_armature, 'data', None)

        if (
            obj_armature is None
            or obj_armature.type != 'ARMATURE'
            or obj_armature.visible_get() is False
            or arm is None
        ):
            self.report({'INFO'}, 'Armature not found.')
            return None

        setup_modifiers(obj_surface, obj_armature)

        bcoll_net = arm.collections_all.get('Net') \
            or arm.collections.new('Net')
        bcoll_points = arm.collections_all.get('Net_Points') \
            or arm.collections.new('Net_Points', parent = bcoll_net)
        bcoll_points_extra = arm.collections_all.get('Net_Points_Extra') \
            or arm.collections.new('Net_Points_Extra', parent = bcoll_points)
        bcoll_handles = arm.collections_all.get('Net_Handles') \
            or arm.collections.new('Net_Handles', parent = bcoll_net)
        bcoll_handles_lines = arm.collections_all.get('Net_Handles_Lines') \
            or arm.collections.new('Net_Handles_Lines', parent = bcoll_handles)

        bcoll_points_extra.is_visible = False

        #########
        # Bone.

        map_wgt = setup_widgets()

        SUFFIX_P = '_p' # point
        SUFFIX_H = '_h' # handle

        COL_SELECT = (0.6, 0.9, 1.0)
        COL_ACTIVE = (0.7, 1.0, 1.0)

        COL_POINT = (0.0, 1.0, 1.0)
        COL_HANDLE = (1.0, 1.0, 0.0)

        #########
        # Edit mode (armature).

        set_active_object(context, obj_armature)
        bpy.ops.object.mode_set(mode = 'EDIT')

        eb_none = arm.edit_bones.get('none') \
            or arm.edit_bones.new(name = 'none')# for constraints

        eb_none.use_deform = False
        eb_none.hide_select = True
        eb_none.head[:] = 0.0, 0.0, 0.0
        eb_none.tail[:] = 0.0, 0.01, 0.0 # world y-axis
        eb_none.bbone_x = \
        eb_none.bbone_z = \
        eb_none.envelope_distance = \
        eb_none.head_radius = \
        eb_none.tail_radius = 0.0025

        '''
            p03   p13   p23   p33
            p02   p12   p22   p32
            p01   p11   p21   p31
        v ↑ p00   p10   p20   p30
            u →

        points = [
            p00, p01, p02, p03, # spline 0
            p10, p11, p12, p13,
            p20, p21, p22, p23,
            p30, p31, p32, p33,
        ]
        '''

        data = (
            # (points_index, name, scale)
            (0, f'00{SUFFIX_P}', 1.0),
            (1, f'01{SUFFIX_H}', 0.5),
            (2, f'02{SUFFIX_H}', 0.5),
            (3, f'03{SUFFIX_P}', 1.0),

            (4, f'10{SUFFIX_H}', 0.5),
            (5, f'11{SUFFIX_P}', 0.25),
            (6, f'12{SUFFIX_P}', 0.25),
            (7, f'13{SUFFIX_H}', 0.5),

            (8, f'20{SUFFIX_H}', 0.5),
            (9, f'21{SUFFIX_P}', 0.25),
            (10, f'22{SUFFIX_P}', 0.25),
            (11, f'23{SUFFIX_H}', 0.5),

            (12, f'30{SUFFIX_P}', 1.0),
            (13, f'31{SUFFIX_H}', 0.5),
            (14, f'32{SUFFIX_H}', 0.5),
            (15, f'33{SUFFIX_P}', 1.0),
        )

        bone_names = []

        for index, name, scale in data:

            # TODO: Find surface bones instead of nearest.
            co = points[index]
            eb_near = get_nearest_edit_bone(arm, co, self.B_EPSILON)

            eb = eb_near or arm.edit_bones.new(name = name)

            bone_names.append(eb.name)

            if eb_near is not None:
                continue

            eb.head = co
            eb.tail = eb.head + Vector((0.0, 1.0, 0.0)) # world y-axis
            eb.length = scale * self.B_SCALE
            eb.bbone_x = \
            eb.bbone_z = \
            eb.envelope_distance = \
            eb.head_radius = \
            eb.tail_radius = eb.length * 0.25

        # TODO: Clean-up.
        eb_00 = arm.edit_bones[bone_names[0]]
        eb_01 = arm.edit_bones[bone_names[1]]
        eb_02 = arm.edit_bones[bone_names[2]]
        eb_03 = arm.edit_bones[bone_names[3]]
        eb_10 = arm.edit_bones[bone_names[4]]
        eb_11 = arm.edit_bones[bone_names[5]]
        eb_12 = arm.edit_bones[bone_names[6]]
        eb_13 = arm.edit_bones[bone_names[7]]
        eb_20 = arm.edit_bones[bone_names[8]]
        eb_21 = arm.edit_bones[bone_names[9]]
        eb_22 = arm.edit_bones[bone_names[10]]
        eb_23 = arm.edit_bones[bone_names[11]]
        eb_30 = arm.edit_bones[bone_names[12]]
        eb_31 = arm.edit_bones[bone_names[13]]
        eb_32 = arm.edit_bones[bone_names[14]]
        eb_33 = arm.edit_bones[bone_names[15]]

        # handles
        eb_01.parent = \
        eb_10.parent = eb_00
        eb_20.parent = \
        eb_31.parent = eb_30
        eb_32.parent = \
        eb_23.parent = eb_33
        eb_13.parent = \
        eb_02.parent = eb_03

        # handles lines
        for eb_to in (eb_01, eb_10, eb_20, eb_31, eb_32, eb_23, eb_13, eb_02):

            if arm.edit_bones.get(f'{eb.name}_line'):
                continue

            # eb_to = None
            eb_from = eb_to.parent

            eb = arm.edit_bones.new(name = f'{eb_to.name}_line')

            eb.use_deform = False
            eb.parent = eb_from
            eb.head = eb_from.head
            eb.tail = eb_to.head
            eb.bbone_x = \
            eb.bbone_z = \
            eb.envelope_distance = \
            eb.head_radius = \
            eb.tail_radius = 0.0625 * self.B_SCALE

        #########
        # Pose mode.

        bpy.ops.object.mode_set(mode = 'POSE')

        pb_none = obj_armature.pose.bones['none']

        pb_none.lock_location = \
        pb_none.lock_rotation = \
        pb_none.lock_scale = (True, ) * 3
        pb_none.lock_rotation_w = True

        # TODO: Clean-up.
        pb_00 = obj_armature.pose.bones[bone_names[0]]
        pb_01 = obj_armature.pose.bones[bone_names[1]]
        pb_02 = obj_armature.pose.bones[bone_names[2]]
        pb_03 = obj_armature.pose.bones[bone_names[3]]
        pb_10 = obj_armature.pose.bones[bone_names[4]]
        pb_11 = obj_armature.pose.bones[bone_names[5]]
        pb_12 = obj_armature.pose.bones[bone_names[6]]
        pb_13 = obj_armature.pose.bones[bone_names[7]]
        pb_20 = obj_armature.pose.bones[bone_names[8]]
        pb_21 = obj_armature.pose.bones[bone_names[9]]
        pb_22 = obj_armature.pose.bones[bone_names[10]]
        pb_23 = obj_armature.pose.bones[bone_names[11]]
        pb_30 = obj_armature.pose.bones[bone_names[12]]
        pb_31 = obj_armature.pose.bones[bone_names[13]]
        pb_32 = obj_armature.pose.bones[bone_names[14]]
        pb_33 = obj_armature.pose.bones[bone_names[15]]

        '''
            p03   p13   p23   p33
            p02   p12   p22   p32
            p01   p11   p21   p31
        v ↑ p00   p10   p20   p30
            u →
        '''

        # points
        for pb in (pb_00, pb_30, pb_33, pb_03):

            bcoll_points.assign(pb)

            pb.color.palette = 'CUSTOM'
            pb.color.custom.normal = COL_POINT
            pb.color.custom.select = COL_SELECT
            pb.color.custom.active = COL_ACTIVE
            pb.custom_shape = map_wgt['diamond']
            # constraint = pb.constraints.new('ARMATURE')
            # target = constraint.targets.new()
            # target.target = obj_armature
            # target.subtarget = ''

        # handles
        for pb in (pb_10, pb_20, pb_31, pb_32, pb_23, pb_13, pb_02, pb_01):

            bcoll_handles.assign(pb)

            pb.lock_rotation = \
            pb.lock_scale = (True, ) * 3
            pb.lock_rotation_w = True
            pb.color.palette = 'CUSTOM'
            pb.color.custom.normal = COL_HANDLE
            pb.color.custom.select = COL_SELECT
            pb.color.custom.active = COL_ACTIVE
            pb.custom_shape = map_wgt['diamond']

        # handles_lines
        for pb_to in (pb_10, pb_20, pb_31, pb_32, pb_23, pb_13, pb_02, pb_01):

            pb = obj_armature.pose.bones.get(f'{pb_to.name}_line')

            if pb is None:
                continue

            bcoll_handles_lines.assign(pb)

            pb.lock_location = \
            pb.lock_rotation = \
            pb.lock_scale = (True, ) * 3
            pb.lock_rotation_w = True
            pb.color.palette = 'CUSTOM'
            pb.color.custom.normal = COL_HANDLE
            pb.color.custom.select = COL_SELECT
            pb.color.custom.active = COL_ACTIVE
            pb.custom_shape = map_wgt['line']
            constraint = pb.constraints.new('STRETCH_TO')
            constraint.target = obj_armature
            constraint.subtarget = pb_to.name
            constraint.volume = 'NO_VOLUME'

        # middle; extra
        data = (
            (pb_11, (
                (0, pb_10, 2/3),
                (1, pb_13, 1/3),
                (2, pb_01, 2/3),
                (3, pb_31, 1/3),
                (4, pb_00, 4/9),
                (5, pb_30, 2/9),
                (6, pb_03, 2/9),
                (7, pb_33, 1/9),
            )),
            (pb_21, (
                (0, pb_20, 2/3),
                (1, pb_23, 1/3),
                (2, pb_01, 1/3),
                (3, pb_31, 2/3),
                (4, pb_00, 2/9),
                (5, pb_30, 4/9),
                (6, pb_03, 1/9),
                (7, pb_33, 2/9),
            )),
            (pb_12, (
                (0, pb_10, 1/3),
                (1, pb_13, 2/3),
                (2, pb_02, 2/3),
                (3, pb_32, 1/3),
                (4, pb_00, 2/9),
                (5, pb_30, 1/9),
                (6, pb_03, 4/9),
                (7, pb_33, 2/9),
            )),
            (pb_22, (
                (0, pb_20, 1/3),
                (1, pb_23, 2/3),
                (2, pb_02, 1/3),
                (3, pb_32, 2/3),
                (4, pb_00, 1/9),
                (5, pb_30, 2/9),
                (6, pb_03, 2/9),
                (7, pb_33, 4/9),
            ))
        )

        for pb, targets in data:

            bcoll_points_extra.assign(pb)

            pb.lock_location = \
            pb.lock_rotation = \
            pb.lock_scale = (True, ) * 3
            pb.lock_rotation_w = True

            c = pb.constraints.new('COPY_LOCATION')
            c.name = pb_none.name
            c.target = obj_armature
            c.subtarget = pb_none.name
            c.target_space = \
            c.owner_space = 'POSE'

            for index, subtarget, weight in targets:

                c = pb.constraints.new('COPY_LOCATION')
                c.name = subtarget.name
                c.target = obj_armature
                c.subtarget = subtarget.name
                c.invert_x = \
                c.invert_y = \
                c.invert_z = index > 3
                c.use_offset = True
                c.target_space = \
                c.owner_space = 'POSE'
                c.influence = weight

        #########
        # Edit mode (surface).

        set_active_object(context, obj_surface)
        bpy.ops.object.mode_set(mode = 'EDIT')

        return None

    def _setup_new_surface(self, context) -> None:

        if context.mode != 'EDIT_SURFACE': # SEI_WT_net_bone -> bl_context_mode
            return None

        points = self.points
        points.append(self.point_current)

        if len(points) != 4:

            self.report({'WARNING'}, 'Expected four points.')
            print_message(points)

            return None

        #########
        # Surface.

        obj_surface = context.object
        curve = obj_surface.data

        curve.dimensions = '3D'
        curve.resolution_u = \
        curve.resolution_v = curve.resolution_u
        curve.render_resolution_u = \
        curve.render_resolution_v = curve.render_resolution_u

        #########
        # Counter-clockwise.

        p0, p1, p2, p3 = (p[0] for p in points)
        normal = (p1 - p0).cross(p2 - p0).normalized()

        rv3d = context.region_data
        view_vector = rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))

        # TODO: Use mesh normal if available.
        if normal.dot(view_vector) > 0.0:
            points = [points[0], points[3], points[2], points[1]]

        del p0, p1, p2, p3, normal, rv3d, view_vector

        #########
        # Points.
        # TODO: Find points of surfaces for continuity.

        # NOTE: Not before due to `_draw_surfacenet()`.
        obj_matrix_inv = obj_surface.matrix_world.inverted()
        obj_matrix_inv_3x3 = obj_matrix_inv.to_3x3()

        handles = []

        for i, (p, normal) in enumerate(points):

            p = obj_matrix_inv @ p
            normal = obj_matrix_inv_3x3 @ normal if normal else None

            prev = points[(i - 1) % 4][0] - p
            next = points[(i + 1) % 4][0] - p

            h0 = (prev).normalized() # handle left
            h1 = (next).normalized() # handle right

            if normal is not None:

                h0 = (h0 - normal * h0.dot(normal)).normalized()
                h1 = (h1 - normal * h1.dot(normal)).normalized()

            handles.extend([
                p + h0 * (prev).length * 0.333,
                p + h1 * (next).length * 0.333
            ])

        '''
            p03   p13   p23   p33
            p02   p12   p22   p32
            p01   p11   p21   p31
        v ↑ p00   p10   p20   p30
            u →
        '''

        p00 = points[0][0]
        p30 = points[1][0]
        p33 = points[2][0]
        p03 = points[3][0]

        p01 = handles[0]
        p10 = handles[1]
        p20 = handles[2]
        p31 = handles[3]
        p32 = handles[4]
        p23 = handles[5]
        p13 = handles[6]
        p02 = handles[7]

        p11 = (
              p10 * (2/3)
            + p13 * (1/3)
            + p01 * (2/3)
            + p31 * (1/3)
            - p00 * (4/9)
            - p30 * (2/9)
            - p03 * (2/9)
            - p33 * (1/9)
        )
        p21 = (
              p20 * (2/3)
            + p23 * (1/3)
            + p01 * (1/3)
            + p31 * (2/3)
            - p00 * (2/9)
            - p30 * (4/9)
            - p03 * (1/9)
            - p33 * (2/9)
        )
        p12 = (
              p10 * (1/3)
            + p13 * (2/3)
            + p02 * (2/3)
            + p32 * (1/3)
            - p00 * (2/9)
            - p30 * (1/9)
            - p03 * (4/9)
            - p33 * (2/9)
        )
        p22 = (
              p20 * (1/3)
            + p23 * (2/3)
            + p02 * (1/3)
            + p32 * (2/3)
            - p00 * (1/9)
            - p30 * (2/9)
            - p03 * (2/9)
            - p33 * (4/9)
        )

        #########
        # Nurbs Surface.
        # https://blender.stackexchange.com/questions/7020/create-nurbs-surface-with-python

        points = [
            p00, p01, p02, p03, # spline 0
            p10, p11, p12, p13,
            p20, p21, p22, p23,
            p30, p31, p32, p33,
        ]

        for spline in curve.splines:
            for point in spline.points:

                point.select = False # make_segment()

        for i in range(0, 16, 4):

            spline = curve.splines.new('NURBS')
            spline.points.add(3) # 1 by default

            for p, co in zip(spline.points, points[i:i+4]):

                p.co = co[:] + (1.0, ) # vec3 -> vec4
                p.select = True

        bpy.ops.curve.make_segment()

        # NOTE: At the end due to `make_segment()`.
        spline = curve.splines[-1]
        spline.use_endpoint_u = \
        spline.use_endpoint_v = True
        spline.resolution_u = \
        spline.resolution_v = self.S_SEGMENTS

        print_message(
            'tool, created surface\n' +
            '\n'.join(f'    {i:02d}: {p}' for i, p in enumerate(points))
        )

        #########
        # Armature.

        self._setup_armature(context, obj_surface, points)

        print_message('tool, created bones')

        return None

    #########
    # Operator.

    @classmethod
    def poll(cls, context):
        return (
            not cls._handle
            and context.mode == 'EDIT_SURFACE'
        )

    def invoke(self, context, event):

        if context.mode != 'EDIT_SURFACE':
            return {'CANCELLED'}

        #########
        # Initialize

        self.point_current = None # (vec3_coord, vec3_normal)
        self.points = [] # [(vec3_coord, vec3_normal), ...]

        # Handlers.

        shaders = (
            self._setup_shader_point_uniform(), # gpu.shader.from_builtin('POINT_UNIFORM_COLOR')
            gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR'),
            gpu.shader.from_builtin('UNIFORM_COLOR')
        )
        cls = type(self) # self.__class__
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_surfacenet, (context, shaders), 'WINDOW', 'POST_VIEW')

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
            or mode != 'EDIT_SURFACE'
            or tool is None
            or tool.idname != SEI_WT_surfacenet.bl_idname
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

            if len(self.points) < 3:

                self.points.append(self.point_current)

                print_message(f'tool, start, {len(self.points)}')

                return {'RUNNING_MODAL'}

            else:

                self._setup_new_surface(context)
                self._cancel(context)

                print_message('tool, end')

                # NOTE: Reset the operator so undo is available.
                bpy.ops.sei.surfacenet(
                    'INVOKE_DEFAULT',
                    SIZE_PX = self.SIZE_PX,
                    S_SNAP = self.S_SNAP,
                    S_SNAP_TYPE = self.S_SNAP_TYPE,
                    S_SEGMENTS = self.S_SEGMENTS,
                    S_ARMATURE = self.S_ARMATURE,
                    B_SCALE = self.B_SCALE,
                    B_EPSILON = self.B_EPSILON
                )

                return {'FINISHED'}

        return {'PASS_THROUGH'}

class SEI_PT_surfacenet_popover(bpy.types.Panel):
    '''
    Popover panel for extra options.
    '''
    bl_idname = 'SEI_PT_surfacenet_popover'
    bl_label = 'Extra Options'
    bl_description = 'Popover panel for extra options'
    bl_space_type = 'TOPBAR'
    bl_region_type = 'HEADER'

    def draw(self, context):

        # NOTE: `WorkSpaceTool` is `VIEW_3D`.
        mode = context.mode
        tool = context.workspace.tools.from_space_view3d_mode(mode)

        if tool is None:
            return

        # Draw.
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = tool.operator_properties('sei.surfacenet')
        draw_mode = getattr(context, 'draw_mode', None)

        if draw_mode == 'SURFACE':

            col = layout.column()
            col.prop(props, 'S_SEGMENTS')

            col.separator()

            col.row().prop(props, 'S_SNAP_TYPE', text = 'Normal', expand = True)

        elif draw_mode == 'ARMATURE':

            col = layout.column()
            col.prop(props, 'B_SCALE')

            col.separator()

            col.prop(props, 'B_EPSILON', text = 'Merge')

        else:
            return

class SEI_WT_surfacenet(bpy.types.WorkSpaceTool):
    '''
    ./scripts/startup/bl_ui/space_toolsystem_common.py
    '''
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_SURFACE'
    bl_idname = 'sei.surfacenet_tool'
    bl_label = 'surfacenet'
    bl_description = 'Construct nurbs surfaces as a net'
    bl_icon = 'ops.curve.extrude_move'
    bl_widget = None
    bl_keymap = (
        ('sei.surfacenet', {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties('sei.surfacenet')

        row = layout.row(align = True)
        row.ui_units_x = 7
        row.prop(props, 'SIZE_PX', text = 'Radius', slider = True)
        row.prop(props, 'S_SNAP', text = '',
            icon = 'SNAP_ON' if props.S_SNAP else 'SNAP_OFF')

        layout.separator()

        row = layout.row()
        row.ui_units_x = 7
        row.context_string_set('draw_mode', 'SURFACE')
        row.popover('SEI_PT_surfacenet_popover', text = 'Surface', icon = 'SURFACE_NSURFACE')

        row = layout.row(align = True)
        row.ui_units_x = 7
        row.context_string_set('draw_mode', 'ARMATURE')
        row.prop(props, 'S_ARMATURE', text = '', icon = 'OUTLINER_OB_ARMATURE') # prop_search()
        row.popover('SEI_PT_surfacenet_popover', text = '...')

# ===========================

def register():

    bpy.utils.register_class(SEI_OT_surfacenet)
    bpy.utils.register_class(SEI_PT_surfacenet_popover)
    bpy.utils.register_tool(SEI_WT_surfacenet, separator = True)

    # try:
    #     bpy.utils.register_tool(SEI_WT_surfacenet, separator = True)
    # except:
    #     pass

def unregister():

    bpy.utils.unregister_class(SEI_OT_surfacenet)
    bpy.utils.unregister_class(SEI_PT_surfacenet_popover)
    bpy.utils.unregister_tool(SEI_WT_surfacenet)

if __name__ == "__main__": # debug; live edit
    register()
