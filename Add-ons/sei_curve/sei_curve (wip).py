'''
TODO:
    - Armature: Update it instead of re-creating it.
    - Armature: Create tools (pen tool).
    - Mesh: Create the geometry nodes node group.
    - Mesh: Create "radius" (attribute, nodes, vertices).
    - Workspace Tool: Better UI/UX (GPU).
    - Fix snap radius (setup_nearest_point()), currently world-space.
'''

import bpy
import bmesh
import gpu

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
# from gpu_extras.presets import draw_circle_2d
from mathutils import Vector, Color

bl_info = {
    "name": "Sei Curve",
    "author": "Seilotte",
    "version": (0, 1, 0),
    "blender": (5, 1, 2),
    "location": "3D View > Toolbar > Edit Curve",
    "description": "",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/sei_curve",
    "doc_url": "https://github.com/seilotte/Blender-Stuff/issues",
    "category": "Workflow",
}

DEBUG_MODE = True

def print_message(message: str = "") -> None:
    if DEBUG_MODE is True:
        print(f'Sei Curve: {message}')

class SEI_OT_curve_to_mesh(bpy.types.Operator):
    bl_idname = 'sei.curve_to_mesh'
    bl_label = 'Convert to Mesh'
    bl_description = 'Convert the curve to a mesh type'
    bl_options = {'REGISTER', 'UNDO'}

    EPSILON: bpy.props.FloatProperty(
        name = 'Merge Distance',
        description = 'Maximum distance between elements to merge',
        default = 1e-5,
        min = 1e-6, # NOTE: Limit is defined by bone envelopes.
        subtype = 'DISTANCE'
    )

    DO_ARMATURE: bpy.props.BoolProperty(
        name = 'Create Armature',
        description = 'Create armature object',
        default = True
    )

    SIZE_BONES: bpy.props.FloatProperty(
        name = 'Bones Scale',
        description = 'Global bones scale',
        default = 0.01,
        min = 1e-6,
        subtype = 'DISTANCE'
    )

    WIRE_WIDTH: bpy.props.FloatProperty(
        name = 'Wire Width',
        description = 'Adjust the line thickness of custom shapes',
        default = 4.0,
        min = 1.0,
        max = 16.0
    )

    def quantize(self, vector: tuple, epsilon: float = 1e-5) -> tuple:
        return (
            round(vector[0] / epsilon),
            round(vector[1] / epsilon),
            round(vector[2] / epsilon)
        )

    def _setup_curve_data(self, context, obj_curve: bpy.types.Object) -> tuple[list, dict, dict]:

        #########
        # Split curves at each point.

        split_curves = [] # (curve_index, p0, p1)

        counter = 0

        for curve in obj_curve.data.splines:

            verts = [v for v in curve.bezier_points]

            verts_len = len(verts) if curve.use_cyclic_u else len(verts) - 1

            for i in range(verts_len):
                p0 = verts[i]
                p1 = verts[(i + 1) % len(verts)]

                split_curves.append((counter, p0, p1))

                counter += 1

        #########
        # Maps, split_curves & handles.

        map_split_curves = {} # (k0, k1): (curve_index, p0, p1, is_flipped)
        map_handles = {} # (k0, k1): (h0, h1, is_flipped)

        for curve_index, p0, p1 in split_curves:

            k0 = self.quantize(p0.co, self.EPSILON)
            k1 = self.quantize(p1.co, self.EPSILON)

            map_split_curves[(k0, k1)] = (curve_index, p0, p1, False)
            map_split_curves[(k1, k0)] = (curve_index, p1, p0, True)

            map_handles[(k0, k1)] = (p0.handle_right, p1.handle_left, False)
            map_handles[(k1, k0)] = (p1.handle_left, p0.handle_right, True)

        return split_curves, map_split_curves, map_handles

    def _setup_mesh(self, context, curve_data: tuple, obj_curve: bpy.types.Object, obj_mesh: bpy.types.Object) -> None:

        split_curves, map_split_curves, map_handles = curve_data

        mesh = obj_mesh.data

        obj_mesh.name = f'{obj_curve.name}_mesh'
        mesh.name = obj_mesh.name

        obj_mesh.add_rest_position_attribute = True

        #########
        # Initialize bmesh.

        bm = bmesh.new()
        bm.from_mesh(mesh)

        #########
        # Clean-up.

        invalid_verts = [
            v for v in bm.verts
            if not v.link_faces
        ]

        bmesh.ops.delete(bm, geom = invalid_verts, context = 'VERTS')

        invalid_faces = []

        for face in bm.faces:
            for i in range(len(face.loops)):

                v0 = face.loops[i].vert
                v1 = face.loops[(i + 1) % len(face.loops)].vert

                k0 = self.quantize(v0.co, self.EPSILON)
                k1 = self.quantize(v1.co, self.EPSILON)

                if map_split_curves.get((k0, k1)) is None:
                    invalid_faces.append(face)
                    break

        bmesh.ops.delete(bm, geom = invalid_faces, context = 'FACES')

        del invalid_verts, invalid_faces

        #########
        # Create vertices and edges.

        map_vertices = {}

        for v in bm.verts:
            map_vertices[self.quantize(v.co, self.EPSILON)] = v

        for _, p0, p1 in split_curves:

            k0 = self.quantize(p0.co, self.EPSILON)
            k1 = self.quantize(p1.co, self.EPSILON)

            v0 = map_vertices.get(k0)
            v1 = map_vertices.get(k1)

            if v0 is None:
                v0 = bm.verts.new(p0.co)
                map_vertices[k0] = v0

            if v1 is None:
                v1 = bm.verts.new(p1.co)
                map_vertices[k1] = v1

            if v0 is v1:
                continue

            if bm.edges.get((v0, v1)) is None:
                bm.edges.new((v0, v1))

        # bm.verts.ensure_lookup_table()
        # bm.edges.ensure_lookup_table()
        # bm.faces.ensure_lookup_table()

        #########
        # Set up attributes.

        attr_handle_left = bm.loops.layers.int.get('sei_handle_left') \
            or bm.loops.layers.int.new('sei_handle_left')

        attr_handle_right = bm.loops.layers.int.get('sei_handle_right') \
            or bm.loops.layers.int.new('sei_handle_right')

        # NOTE: `data_attrs` is needed due to `.index_update()`.
        map_vertices = {} # reuse
        data_attrs = []

        for face in bm.faces:
            for i in range(len(face.loops)):

                loop0 = face.loops[i]
                loop1 = face.loops[(i + 1) % len(face.loops)]

                v0 = loop0.vert
                v1 = loop1.vert

                k0 = self.quantize(v0.co, self.EPSILON)
                k1 = self.quantize(v1.co, self.EPSILON)

                # curve_data = map_split_curves.get((k0, k1))
                #
                # if curve_data is None:
                #     continue
                #
                # _, p0, p1, is_flipped = curve_data # (curve_index, p0, p1, is_flipped)

                handles_data = map_handles.get((k0, k1)) # (h0, h1, is_flipped)

                if handles_data is None:
                    continue

                h0, h1, is_flipped = handles_data

                k0 = self.quantize(h0, self.EPSILON)
                k1 = self.quantize(h1, self.EPSILON)

                v0 = map_vertices.get(k0)
                v1 = map_vertices.get(k1)

                if v0 is None:
                    v0 = bm.verts.new(h0)
                    map_vertices[k0] = v0

                if v1 is None:
                    v1 = bm.verts.new(h1)
                    map_vertices[k1] = v1

                # attr_hl = attr_handle_right if is_flipped else attr_handle_left
                # attr_hr = attr_handle_left if is_flipped else attr_handle_right
                attr_hl = attr_handle_left
                attr_hr = attr_handle_right

                data_attrs.append((attr_hl, loop0, v0))
                data_attrs.append((attr_hr, loop1, v1))

        bm.verts.index_update()

        for attr, loop, vert in data_attrs:
            loop[attr] = vert.index

        #########
        # Finalize bmesh.

        bm.to_mesh(mesh)
        bm.free()

        mesh.update()

        return None

    def _setup_armature(self, context, obj_curve: bpy.types.Object, obj_mesh: bpy.types.Object) -> bpy.types.Object:

        if self.DO_ARMATURE is False:
            return None

        coll = obj_curve.users_collection[0]

        #########
        # Get points/vertices data.

        mesh = obj_mesh.data

        attr_handle_left = mesh.attributes.get('sei_handle_left')
        attr_handle_right = mesh.attributes.get('sei_handle_right')

        map_points = {} # key: (point, [handles])

        for face in mesh.polygons:
            for i in range(face.loop_total):

                loop_index = face.loop_indices[i]

                loop = mesh.loops[loop_index]
                vert = mesh.vertices[loop.vertex_index]

                key = self.quantize(vert.co.copy(), self.EPSILON)

                # TODO: Do not assume handles always exist.
                if attr_handle_left is None or attr_handle_right is None:
                    continue

                hl_index = attr_handle_left.data[loop_index].value
                hr_index = attr_handle_right.data[loop_index].value

                hl = mesh.vertices[hl_index]
                hr = mesh.vertices[hr_index]

                if map_points.get(key) is None:
                    map_points[key] = (vert.co.copy(), [])

                point, handles = map_points[key]

                # TODO: Reduce nesting.
                for handle in (hl.co.copy(), hr.co.copy()):
                    if not any((h - handle).length < self.EPSILON for h in handles):
                        handles.append(handle)

        del mesh, attr_handle_left, attr_handle_right

        #########
        # Create widgets.

        def mesh_create(name = 'Mesh', vertices = [], edges = [], faces = []):
            obj = bpy.data.objects.get(name)

            if obj is None:
                mesh = bpy.data.meshes.new(name = name)

                mesh.from_pydata(vertices, edges, faces)
                mesh.update()

                obj = bpy.data.objects.new(name, mesh)

            return obj

        map_wgt = {
            'None': None, # .get does this
            'plane': mesh_create( # returns obj
                name = 'WGT-Plane',
                vertices = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0), (0.0, 0.5, 0.0), (0.0, 0.2, 0.0)],
                edges = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5]]
            ),
            'axes_xy': mesh_create( # TODO: Just x & y.
                name = 'WGT-Axes_XY',
                vertices = [(-0.5, 0.0, 0.0), (0.5, 0.0, 0.0), (0.0, -0.5, 0.0), (0.0, 0.5, 0.0), (-0.125, 0.5, 0.0), (0.125, 0.5, 0.0)],
                edges = [[0, 1], [2, 3], [4, 5]]
            ),
            'diamond': mesh_create(
                name = 'WGT-Diamond',
                vertices = [(-0.5, 0.0, 0.0), (0.0, 0.0, -0.5), (0.5, 0.0, 0.0), (0.0, 0.0, 0.5), (0.0, -0.5, 0.0), (0.0, 0.5, 0.0), (0.0, 0.8, 0.0)],
                edges = [[0, 4], [4, 3], [3, 0], [3, 5], [5, 0], [0, 1], [1, 4], [5, 1], [2, 3], [4, 2], [2, 5], [1, 2], [5, 6]]
            ),
        }

        def find_layer_collection(target_collection):
            stack = [context.view_layer.layer_collection]

            while stack:
                current_collection = stack.pop()

                if current_collection.collection == target_collection:
                    return current_collection

                stack.extend(current_collection.children)

            return None

        coll_wgt = bpy.data.collections.get('WGT Widgets')

        if coll_wgt is None:
            coll_wgt = bpy.data.collections.new('WGT Widgets')
            coll.children.link(coll_wgt)

        find_layer_collection(coll_wgt).exclude = True

        for widget in map_wgt.values():
            if widget and coll_wgt.objects.get(widget.name) is None:
                coll_wgt.objects.link(widget)

        #########
        # Delete old armature.

        # TODO:
        # - Do not check by name, add a pointer to the armature?
        # - Do not re-create it every time.
        new_armature = bpy.data.armatures.get(f'{obj_curve.name}_rig')

        if new_armature:
            bpy.data.armatures.remove(new_armature, do_unlink = True)

        #########
        # Create armature.

        new_armature = bpy.data.armatures.new(f'{obj_curve.name}_rig')
        new_obj = bpy.data.objects.new(new_armature.name, new_armature)

        if coll != context.scene.collection:
            coll.objects.link(new_obj)

        context.scene.collection.objects.link(new_obj) # scene collection is always active
        context.view_layer.objects.active = new_obj

        new_obj.hide_render = True
        new_obj.show_in_front = True
        new_obj.display_type = 'WIRE'
#        new_obj.display_type = 'ENVELOPE'

        #########
        # Set up collections.

        coll_main = new_armature.collections.new('Main')
        coll_handles = new_armature.collections.new('Handles')
        # coll_radius = new_armature.collections.new('Radius')

        #########
        # Set up edit bones.

        bpy.ops.object.mode_set(mode = 'EDIT')

        eb_root = new_armature.edit_bones.new('root')
        eb_root.tail = eb_root.head + Vector((0.0, self.SIZE_BONES * 10.0, 0.0)) # world y-axis
        eb_root.use_deform = False

        for i0, (_, (point, handles)) in enumerate(map_points.items()):

            # TODO: Use curve tangent.
            x_axis = (handles[0] - point).normalized()
            y_axis = Vector((0.0, 1.0, 0.0)) if len(handles) < 2 \
                else (handles[1] - point).normalized()
            z_axis = x_axis.cross(y_axis)

            eb_m = new_armature.edit_bones.new(f'm_point{i0}') # middle
            eb_m.head = point
            eb_m.tail = point + y_axis * self.SIZE_BONES * 0.5
            eb_m.align_roll(z_axis)
            eb_m.parent = eb_root
            eb_m.envelope_distance = \
            eb_m.head_radius = \
            eb_m.tail_radius = self.EPSILON

            for i1, handle in enumerate(handles):
                eb_h = new_armature.edit_bones.new(f'{i0}_handle{i1}')
                eb_h.head = handle
                eb_h.tail = handle + Vector((0.0, self.SIZE_BONES * 0.125, 0.0)) # world y-axis
                eb_h.parent = eb_m
                eb_h.envelope_distance = \
                eb_h.head_radius = \
                eb_h.tail_radius = self.EPSILON

        #########
        # Setup pose bones.

        bpy.ops.object.mode_set(mode = 'OBJECT')

        COL_SELECT = (0.6, 0.9, 1.0)
        COL_ACTIVE = (0.7, 1.0, 1.0)

        for pb in new_obj.pose.bones:

            pb.rotation_mode = 'XYZ' # gimbal lock
            pb.custom_shape_wire_width = self.WIRE_WIDTH

            if pb.name.startswith('root'):

                coll_main.assign(pb)

                pb.custom_shape = map_wgt['plane']
                pb.custom_shape_scale_xyz[0] = 0.5
                pb.custom_shape_translation[1] = pb.bone.length * 0.5

            elif pb.name.startswith('m_point'):

                coll_main.assign(pb)

                # pb.lock_scale[2] = True

                pb.color.palette = 'CUSTOM'
                pb.color.custom.select = COL_SELECT
                pb.color.custom.active = COL_ACTIVE

                pb.custom_shape = map_wgt['axes_xy']

            elif '_handle' in pb.name:

                coll_handles.assign(pb)

                pb.lock_rotation = (True, True, True)
                pb.lock_rotation_w = True
                pb.lock_scale = (True, True, True)

                pb.color.palette = 'CUSTOM'
                pb.color.custom.select = COL_SELECT
                pb.color.custom.active = COL_ACTIVE

                pb.custom_shape = map_wgt['diamond']

                constraint = pb.constraints.new('LIMIT_ROTATION')
                constraint.use_limit_x = \
                constraint.use_limit_y = \
                constraint.use_limit_z = True

                constraint = pb.constraints.new('LIMIT_SCALE')
                constraint.use_max_x = \
                constraint.use_max_y = \
                constraint.use_max_z = True
                constraint.max_x = \
                constraint.max_y = \
                constraint.max_z = 1.0

        # TODO: Do not loop twice.
        for index, pb in enumerate(new_obj.pose.bones):

            if pb.name.startswith('root'):
                continue

            elif '_handle' in pb.name:
                continue

            colour = Color()
            colour.hsv = (index * 0.618034 % 1.0, 1.0, 1.0)

            pb.color.custom.normal = colour

            colour.v = 0.8

            for c in pb.children:
                c.color.custom.normal = colour

        #########
        # Finalize.

        context.view_layer.objects.active = obj_curve # view layer always needs an object

        if coll != context.scene.collection:
            context.scene.collection.objects.unlink(new_obj)

        return new_obj

    def _setup_modifiers(self, context, obj_mesh: bpy.types.Object, obj_armature: bpy.types.Object) -> None:

        #########
        # Add modifiers.

        # NOTE: Assume the first modifier found is used for our purpose.
        mods = obj_mesh.modifiers

        modifier = \
            next((m for m in mods if m.type == 'NODES'), None) \
            or mods.new('GeometryNodes', 'NODES')

        # TODO: Create/append the node group.
        modifier.node_group = bpy.data.node_groups.get('gn_curves patch')

        mods.move(mods.find(modifier.name), 0)

        modifier = \
            next((m for m in mods if m.type == 'ARMATURE'), None) \
            or mods.new('Armature', 'ARMATURE')

        modifier.object = obj_armature
        modifier.use_vertex_groups = False
        modifier.use_bone_envelopes = True

        mods.move(mods.find(modifier.name), 0)

        return None

    @classmethod
    def poll(cls, context):

        obj = context.object
        objs = context.selected_objects

        if len(objs) > 2:
            return False

        obj_curve = next((o for o in objs if o.type == 'CURVE'), None)
        obj_mesh = next((o for o in objs if o.type == 'MESH'), None)

        if obj != obj_curve:
            return False

        return obj_curve and obj_mesh

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()
        col.prop(self, 'EPSILON')

        col.separator()
        col.prop(self, 'DO_ARMATURE')

        sub = col.column()
        sub.enabled = self.DO_ARMATURE
        sub.prop(self, 'SIZE_BONES')
        sub.prop(self, 'WIRE_WIDTH')

    def execute(self, context):

        #########
        # Initialize.

        # NOTE: Important checks are taken care by poll.
        obj_curve = context.object
        obj_mesh = next((o for o in context.selected_objects if o.type == 'MESH'), None)

        obj_curve.data.name = obj_curve.name
        obj_curve.hide_render = True

        active_mode = obj_curve.mode

        bpy.ops.object.mode_set(mode = 'OBJECT')

        #########
        # Setups.

        curve_data = self._setup_curve_data(context, obj_curve)
        self._setup_mesh(context, curve_data, obj_curve, obj_mesh)
        obj_armature = self._setup_armature(context, obj_curve, obj_mesh)
        self._setup_modifiers(context, obj_mesh, obj_armature)

        #########
        # Finalize.

        bpy.ops.object.mode_set(mode = active_mode)

        context.view_layer.objects.active = obj_curve
        obj_curve.select_set(True)

        # self.report({'INFO'}, f'Converted to Mesh.')

        return {'FINISHED'}

class SEI_OT_curvenet(bpy.types.Operator):
    bl_idname = 'sei.curvenet'
    bl_label = 'Curvenet'
    bl_description = 'Construct and edit splines as a curvenet'
    bl_options = {'REGISTER', 'UNDO'}

    _is_running = False
    _handle = None

    SIZE: bpy.props.IntProperty(
        name = 'Size',
        description = 'Pixel radius for nearest vertex detection',
        default = 12,
        min = 1,
        max = 1000,
        soft_max = 100,
        subtype = 'PIXEL'
    )

    DEPSGRAPH: bpy.props.BoolProperty(
        name = 'Use Depsgraph',
        description = 'Use depsgraph for nearest vertex detection',
        default = True
    )

    #########
    # Utils; GPU Draw.

    def get_theme_colours(self, context) -> dict:

        def get_float(theme, attr_name: str) -> float:
            value = getattr(theme, attr_name, None)

            if value is None:
                return 1.0

            return value

        def get_rgba(theme, attr_name: str) -> tuple:
            col = getattr(theme, attr_name, None)

            if col is None:
                return (0.0, 0.0, 0.0, 1.0)

            try:
                return (col[0], col[1], col[2], col[3])
            except IndexError:
                return (col[0], col[1], col[2], 1.0)

        theme = context.preferences.themes[0]
        curves = theme.common.curves
        view3d = theme.view_3d

        colours = {
            'FREE': get_rgba(curves, 'handle_free'),
            'FREE_select': get_rgba(curves, 'handle_sel_free'),
            'AUTO': get_rgba(curves, 'handle_auto'),
            'AUTO_select': get_rgba(curves, 'handle_sel_auto'),
            'VECTOR': get_rgba(curves, 'handle_vect'),
            'VECTOR_select': get_rgba(curves, 'handle_sel_vect'),
            'ALIGNED': get_rgba(curves, 'handle_align'),
            'ALIGNED_select': get_rgba(curves, 'handle_sel_align'),
            'handle_clamped': get_rgba(curves, 'handle_auto_clamped'),
            'handle_clamped_select': get_rgba(curves, 'handle_sel_auto_clamped'),
            'handle_vertex': get_rgba(curves, 'handle_vertex'),
            'handle_vertex_select': get_rgba(curves, 'handle_vertex_select'),
            'handle_vertex_size': get_float(curves, 'handle_vertex_size'),

            'editmesh_active': get_rgba(view3d, 'editmesh_active'),
            'vertex': get_rgba(view3d, 'vertex'),
            'vertex_select': get_rgba(view3d, 'vertex_select'),
            'edge': get_rgba(view3d, 'wire_edit'),
            'edge_select': get_rgba(view3d, 'edge_select'),
            'vertex_size': get_float(view3d, 'vertex_size'),
            'edge_width': get_float(view3d, 'edge_width'),
        }

        return colours

    def draw_curvenet(self, context, colours: dict):
        if context.mode != 'EDIT_CURVE':
            return

        obj = context.active_object

        obj_matrix = obj.matrix_world
        curves = obj.data.splines

        #########
        # Get curve data.

        col_point = \
        col_handle_left = \
        col_handle_right = \
        col_edge = \
        col_edge_left = \
        col_edge_right = (0, 0, 0, 1)

        points = []
        points_vcols = []
        edges = []
        edges_vcols = []

        i = 0

        for curve in curves:

            if curve.type != 'BEZIER':
                continue

            for point in curve.bezier_points:

                p = obj_matrix @ point.co
                hl = obj_matrix @ point.handle_left
                hr = obj_matrix @ point.handle_right

                # colours
                col_point = \
                    colours['vertex_select'] if point.select_control_point \
                    else colours['vertex']

                col_handle_left = \
                    colours['vertex_select'] if point.select_left_handle \
                    else colours['vertex']

                col_handle_right = \
                    colours['vertex_select'] if point.select_right_handle \
                    else colours['vertex']

                # col_edge = \

                col_edge_left = \
                    colours[point.handle_left_type + '_select'] if point.select_left_handle \
                    else colours[point.handle_left_type]

                col_edge_right = \
                    colours[point.handle_right_type + '_select'] if point.select_right_handle \
                    else colours[point.handle_right_type]

                # points
                points.append(p)
                points_vcols.append(col_point)
                edges_vcols.append(col_edge)

                # handles
                if point == curve.bezier_points[0] \
                and not curve.use_cyclic_u: # first
                    points.append(hr)
                    points_vcols.append(col_handle_right)
                    edges.append((i, i + 1))
                    edges_vcols.append(col_edge_right)

                    i += 2

                elif point == curve.bezier_points[-1] \
                and not curve.use_cyclic_u: # last
                    points.append(hl)
                    points_vcols.append(col_handle_left)
                    edges.append((i, i + 1))
                    edges_vcols.append(col_edge_left)

                    i += 2

                else:
                    points.append(hl)
                    points.append(hr)
                    points_vcols.append(col_handle_left)
                    points_vcols.append(col_handle_right)
                    edges.append((i, i + 1))
                    edges.append((i, i + 2))
                    edges_vcols.append(col_edge_left)
                    edges_vcols.append(col_edge_right)

                    i += 3

        #########
        # Draw.

        gpu.state.blend_set("NONE")

        size_point = colours['vertex_size'] * 1.415 # sqrt(2)
        size_edge = colours['edge_width']
        size_viewport = gpu.state.viewport_get()[2:]

        # edges
        shader = gpu.shader.from_builtin('POLYLINE_FLAT_COLOR')

        shader.bind()
        shader.uniform_float('lineWidth', size_edge)
        shader.uniform_float('viewportSize', size_viewport)
        gpu.state.line_width_set(size_edge)

        batch = batch_for_shader(
            shader, 'LINES', {'pos': points, 'color': edges_vcols}, indices = edges)
        batch.draw(shader)

        # edges, tool
        if self.point_start and self.point_end:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')

            shader.bind()
            shader.uniform_float('color', (1, 1, 1, 1))
            shader.uniform_float('lineWidth', size_edge * 2.0)
            shader.uniform_float('viewportSize', size_viewport)
            gpu.state.line_width_set(size_edge * 2.0)

            batch = batch_for_shader(
                shader, 'LINES', {'pos': [self.point_start[0], self.point_end[0]]})
            batch.draw(shader)

        # points
        shader = gpu.shader.from_builtin('POINT_FLAT_COLOR')

        shader.bind()
        shader.uniform_float('size', size_point) # not working
        gpu.state.point_size_set(size_point)

        batch = batch_for_shader(
            shader, 'POINTS', {'pos': points, 'color': points_vcols})
        batch.draw(shader)

        # point, tool
        if self.point_nearest:
            # col_point_active = colours['editmesh_active']
            col_point_active = (1, 1, 0, 1) if self.point_nearest[1] else (0, 1, 1, 1) # point_tangent

            shader = gpu.shader.from_builtin('POINT_UNIFORM_COLOR')

            shader.bind()
            shader.uniform_float('color', col_point_active)
            shader.uniform_float('size', size_point * 2.0) # not working
            gpu.state.point_size_set(size_point * 2.0)

            batch = batch_for_shader(
                shader, 'POINTS', {'pos': [self.point_nearest[0]]}) # coord
            batch.draw(shader)

        return

    #########
    # Utils; Tool.

    def setup_nearest_point(self, context, event) -> None:
        '''
        Returns the nearest point of the
        active curve and scene objects in world space.
        '''

        region = context.region
        rv3d = context.region_data

        mouse_2d = Vector((event.mouse_region_x, event.mouse_region_y))

        curve_nearest = None
        mesh_nearest = None

        curve_tangent = None
        mesh_normal = None

        #########
        # Get nearest curve point.

        # NOTE: EDIT_CURVE, skip checks.
        obj = context.active_object
        obj_matrix = obj.matrix_world

        min_dist = self.SIZE * self.SIZE
        nearest = None

        for curve in obj.data.splines:

            if curve.type != 'BEZIER':
                continue

            for point in curve.bezier_points:

                point.select_control_point = False
                point.select_left_handle = False
                point.select_right_handle = False

                world = obj_matrix @ point.co
                screen = view3d_utils.location_3d_to_region_2d(
                    region, rv3d, world)

                if screen is None:
                    continue

                dist = (screen - mouse_2d).length_squared

                if dist > min_dist:
                    continue

                point.select_control_point = True

                min_dist = dist
                nearest = point

        if nearest:
            curve_nearest = obj_matrix @ nearest.co.copy()
            curve_tangent = (nearest.handle_left - nearest.handle_right).copy().normalized()

        #########
        # Get nearest mesh point.

        ray_origin = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, mouse_2d)

        ray_direction = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, mouse_2d)

        depsgraph = context.evaluated_depsgraph_get()

        _, hit_world, _, _, hit_obj, _ = (
            context.scene.ray_cast(
                depsgraph,
                ray_origin,
                ray_direction
            )
        )

        if hit_obj and hit_obj.type == 'MESH':

            obj = hit_obj.evaluated_get(depsgraph) if self.DEPSGRAPH else hit_obj
            obj_matrix = obj.matrix_world

            hit_world = obj_matrix.inverted() @ hit_world # local

            min_dist = self.SIZE * self.SIZE
            nearest = None

            for vert in obj.data.vertices:

                dist = (vert.co - hit_world).length_squared # local

                if dist > min_dist:
                    continue

                min_dist = dist
                nearest = vert

            if nearest:
                mesh_nearest = obj_matrix @ nearest.co.copy() # local -> world
                mesh_normal = nearest.normal.copy()

        #########
        # Get nearest point.

        if curve_nearest is None and mesh_nearest is None:
            self.point_nearest = None
            return

        if curve_nearest is None:
            self.point_nearest = (mesh_nearest, None, mesh_normal)
            return

        if mesh_nearest is None:
            self.point_nearest = (curve_nearest, curve_tangent, None)
            return

        curve_2d = view3d_utils.location_3d_to_region_2d(
            region, rv3d, curve_nearest)
        mesh_2d = view3d_utils.location_3d_to_region_2d(
            region, rv3d, mesh_nearest)

        if (
            # <= curve has priority
            # < mesh has priority
            (curve_2d - mouse_2d).length_squared <
            (mesh_2d - mouse_2d).length_squared
        ):
            self.point_nearest = (curve_nearest, curve_tangent, None)
        else:
            self.point_nearest = (mesh_nearest, None, mesh_normal)

        return

    def setup_point_start(self, context, event) -> None:

        if self.point_nearest is None:
            return

        self.point_start = self.point_nearest

        return

    def setup_point_end(self, context, event) -> None:

        if self.point_start is None:
            return

        if self.point_nearest:
            self.point_end = self.point_nearest
            return

        '''
        region = context.region
        rv3d = context.region_data

        mouse_2d = Vector((event.mouse_region_x, event.mouse_region_y))

        self.point_end = (
            view3d_utils.region_2d_to_location_3d(
                region, rv3d, mouse_2d, Vector((0, 0, 0))),
            None,
            None
        )
        # '''

        return

    def create_spline(self, context, event) -> None:

        # NOTE: Should not be none, skip checks.
        p0_co, p0_tangent, v0_normal = self.point_start
        p1_co, p1_tangent, v1_normal = self.point_end

        if p1_tangent is None and v1_normal is None:
            self.report({'WARNING'}, 'Point or Vertex not found.')
            return

        delta = p0_co - p1_co
        delta_len = delta.length

        direction = delta * (1.0 / delta_len)

        if p0_tangent is None:
            p0_tangent = (direction - v0_normal * direction.dot(v0_normal)).normalized()

        if p1_tangent is None:
            p1_tangent = (direction - v1_normal * direction.dot(v1_normal)).normalized()

        delta_len *= 0.333 # handle_len

        p0_tangent *= delta_len
        p1_tangent *= delta_len

        # NOTE: EDIT_CURVE, skip checks.
        obj = context.active_object

        spline = obj.data.splines.new('BEZIER')
        spline.bezier_points.add(1)

        p0 = spline.bezier_points[0]
        p1 = spline.bezier_points[1]

        p0.co = p0_co
        p0.handle_left = p0.co + p0_tangent
        p0.handle_right = p0.co - p0_tangent

        p1.co = p1_co
        p1.handle_left = p1.co + p1_tangent
        p1.handle_right = p1.co - p1_tangent

        mat_inv = obj.matrix_world.inverted()

        p0.co = mat_inv @ p0.co
        p0.handle_left = mat_inv @ p0.handle_left
        p0.handle_right = mat_inv @ p0.handle_right

        p1.co = mat_inv @ p1.co
        p1.handle_left = mat_inv @ p1.handle_left
        p1.handle_right = mat_inv @ p1.handle_right

        return

    #########
    # Operator.

    @classmethod
    def poll(cls, context):
        return not cls._is_running

    def invoke(self, context, event):

        if context.mode != 'EDIT_CURVE':
            return {'FINISHED'}

        op = SEI_OT_curvenet
        overlay = context.space_data.overlay # assume view3d

        #########
        # Initialize

        self.display_handle = overlay.display_handle
        self.point_nearest = None # (coord, point_tangent, vert_normal)
        self.point_start = None # coord
        self.point_end = None # coord

        #########
        # Draw.

        overlay.display_handle = 'NONE'
        colours = self.get_theme_colours(context)

        op._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_curvenet,(context, colours), 'WINDOW', 'POST_VIEW')

        context.area.tag_redraw()

        #########
        # Modal.

        op._is_running = True
        context.window_manager.modal_handler_add(self)

        # print_message('invoke')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        #########
        # Cancel.

        tool = context.workspace.tools.from_space_view3d_mode(context.mode)

        if (
            context.area is None
            or context.mode != 'EDIT_CURVE'
            or tool is None
            or tool.idname != SEI_curvenet_tool.bl_idname
            or event.type == 'WINDOW_DEACTIVATE'
        ):
            op = SEI_OT_curvenet

            bpy.types.SpaceView3D.draw_handler_remove(
                op._handle, 'WINDOW')

            if context.area:
                overlay = context.space_data.overlay
                overlay.display_handle = self.display_handle

                context.area.tag_redraw()

            op._handle = None
            op._is_running = False

            # print_message('cancel')

            return {'FINISHED'}

        del tool

        #########
        # Tool.

        if event.type == 'MOUSEMOVE':

            context.area.tag_redraw() # TODO: No.

            self.setup_nearest_point(context, event)

            if self.point_start:
                self.setup_point_end(context, event)

                # print_message('tool, running')

                return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            if self.point_start is None:
                self.setup_point_start(context, event)

                # print_message('tool, start')

            else:
                self.create_spline(context, event)
                self.point_start = None
                self.point_end = None

                # print_message('tool, end')

                return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':

            if self.point_start:
                self.point_start = None
                self.point_end = None

                # print_message('tool, cancelled')

                return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def execute(self, context):

        print_message('execute')

        return {'FINISHED'}

class SEI_curvenet_tool(bpy.types.WorkSpaceTool):
    # ./scripts/startup/bl_ui/space_toolsystem_common.py
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVE'
    bl_idname = 'sei.curvenet_tool'
    bl_label = 'Curvenet'
    bl_description = 'Construct and edit splines as a curvenet'
    bl_icon = 'ops.pose.breakdowner'
    bl_widget = None
    bl_keymap = (
        ('sei.curvenet', {'type': 'MOUSEMOVE', 'value': 'ANY'}, None),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties('sei.curvenet')

        layout.prop(props, 'SIZE', slider = True)
        layout.prop(props, 'DEPSGRAPH')

    # def draw_cursor(context, tool, xy):
    #     props = tool.operator_properties('sei.curvenet')
    # 
    #     draw_circle_2d(xy, (1.0,) * 4, props.SIZE, segments = 32)

class SEI_PT_curve(bpy.types.Panel):
    bl_idname = 'SEI_PT_curve'
    bl_label = ''
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

    def draw_header(self, context):
        self.layout.label(text = 'Curve Tools', icon = 'CURVE_DATA')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        if not bpy.ops.sei.curve_to_mesh.poll():
            layout.label(text = 'Select Mesh & Curve.', icon = 'INFO')

        col = layout.column()
        col.operator('sei.curve_to_mesh', text = 'Convert to Mesh', icon = 'MESH_DATA')

# ===========================

classes = (
    SEI_OT_curve_to_mesh,
    SEI_OT_curvenet,
    SEI_PT_curve,
)

def register():

    if hasattr(bpy.types, 'SEI_PT_tools'):
        SEI_PT_curve.bl_parent_id = 'SEI_PT_tools'

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_tool(SEI_curvenet_tool, separator = True)

    # try:
    #     bpy.utils.register_tool(SEI_curvenet_tool, separator = True)
    # except:
    #     pass

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.utils.unregister_tool(SEI_curvenet_tool)

if __name__ == "__main__": # debug; live edit
    register()
