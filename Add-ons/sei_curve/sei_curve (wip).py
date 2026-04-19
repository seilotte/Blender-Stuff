'''
TODO:
    - GPU View.
    - Create & assign the geometry nodes node group.
    - Armature: Update it instead of re-creating it.
'''

import bpy
import bmesh
import mathutils as m
import math

bl_info = {
    "name": "Sei Curve",
    "author": "Seilotte",
    "version": (0, 1, 0),
    "blender": (5, 1, 1),
    "location": "3D View > Properties > Sei",
    "description": "",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/sei_curve",
    "doc_url": "https://github.com/seilotte/Blender-Stuff/issues",
    "category": "Workflow",
}

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

    RADIUS: bpy.props.FloatProperty(
        name = 'Radius',
        description = 'Global radius for the outline vertices',
        default = 0.01,
        min = 1e-6,
        subtype = 'DISTANCE'
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

    def _setup_curve_data(self, context, obj_curve: bpy.types.Object) -> tuple[list, dict]:

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
        # Build split curves map.

        map_split_curves = {} # (k0, k1): (curve_index, p0, p1, is_flipped)

        for curve_index, p0, p1 in split_curves:

            k0 = self.quantize(p0.co, self.EPSILON)
            k1 = self.quantize(p1.co, self.EPSILON)

            map_split_curves[(k0, k1)] = (curve_index, p0, p1, False)
            map_split_curves[(k1, k0)] = (curve_index, p1, p0, True)

        return split_curves, map_split_curves

    def _setup_mesh(self, context, curve_data: tuple, obj_curve: bpy.types.Object) -> dict:

        split_curves, map_split_curves = curve_data

        obj_mesh = obj_curve.data.sei_object
        mesh = obj_mesh.data

        obj_mesh.name = f'{obj_curve.name}_mesh'
        mesh.name = obj_mesh.name

        #########
        # Update mesh.

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

        bm.to_mesh(mesh)
        bm.free()

        mesh.update()

        #########
        # Create points (radius)

        # NOTE: No bmesh, due to vertices indices.
        if (self.RADIUS < self.EPSILON):
            self.report({'WARNING'}, 'Bone enevelopes will not work on the "radius" vertices')

        map_verts_data = {} # key: (co, normal)
        map_points = {} # key: (v0, v1, v1_index, [handles], vert_normal)

        for face in mesh.polygons:
            for index in face.vertices:

                v = mesh.vertices[index]
                k = self.quantize(v.co, self.EPSILON)

                map_verts_data.setdefault(k, (v.co.copy(), v.normal.copy()))

        for _, p0, p1 in split_curves:
            for p in (p0, p1):

                k = self.quantize(p.co, self.EPSILON)

                if (map_point := map_points.get(k)) is None:

                    if (v0_data := map_verts_data.get(k)) is None:
                        continue

                    v0_co, v0_normal = v0_data

                    mesh.vertices.add(1)
                    v1 = mesh.vertices[-1]
                    v1.co = v0_co + v0_normal * self.RADIUS

                    map_point = (v0_co, v1.co.copy(), v1.index, [], v0_normal)
                    map_points[k] = map_point

                handles = map_point[3]

                for handle in (p.handle_left, p.handle_right):
                    if not any((h - handle).length < self.EPSILON for h in handles):
                        handles.append(handle)

                if len(handles) > 4:
                    self.report({'WARNING'}, f'Point "{p.co}" has "{len(handles)}" handles. Maximum 4.')

        #########
        # Create attributes.

        attr_curve_index = mesh.attributes.get('sei_curve_index') \
            or mesh.attributes.new('sei_curve_index', 'INT', 'CORNER')

        attr_curve_is_flipped = mesh.attributes.get('sei_curve_is_flipped') \
            or mesh.attributes.new('sei_curve_is_flipped', 'BOOLEAN', 'CORNER')

        attr_radius_index = mesh.attributes.get('sei_radius_index') \
            or mesh.attributes.new('sei_radius_index', 'INT', 'POINT')

        for vert in mesh.vertices:
            attr_radius_index.data[vert.index].value = -1

        #########
        # Setup attributes.

        for face in mesh.polygons:
            for i in range(face.loop_total):

                loop0_index = face.loop_indices[i]
                loop1_index = face.loop_indices[(i + 1) % face.loop_total]

                loop0 = mesh.loops[loop0_index]
                loop1 = mesh.loops[loop1_index]

                v0 = mesh.vertices[loop0.vertex_index]
                v1 = mesh.vertices[loop1.vertex_index]

                # Find the curve points.
                k0 = self.quantize(v0.co, self.EPSILON)
                k1 = self.quantize(v1.co, self.EPSILON)

                curve_data = map_split_curves.get((k0, k1))
                curve_data1 = map_points.get(k0)

                if curve_data is None or curve_data1 is None:
                    raise ValueError(
                        f'Failed to match vertices from "{mesh.name}" to "{obj_curve.name}". '
                        'Try increasing "Merge Distance".'
                    )

                curve_index, _, _, is_flipped = curve_data # (curve_index, p0, p1, is_flipped)
                v1_index = curve_data1[2] # key: (v0, v1, v1_index, [handles], vert_normal)

                attr_curve_index.data[loop0_index].value = curve_index
                attr_curve_is_flipped.data[loop0_index].value = is_flipped
                attr_radius_index.data[loop0.vertex_index].value = v1_index

        return map_points

    def _setup_armature(self, context, map_points: dict, obj_curve: bpy.types.Object) -> bpy.types.Object:

        coll = obj_curve.users_collection[0]

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
        # Setup collections.

        coll_main = new_armature.collections.new('Main')
        coll_handles = new_armature.collections.new('Handles')
        coll_radius = new_armature.collections.new('Radius')

        #########
        # Setup edit bones.

        bpy.ops.object.mode_set(mode = 'EDIT')

        eb_root = new_armature.edit_bones.new('root')
        eb_root.tail = eb_root.head + m.Vector((0.0, self.SIZE_BONES * 10.0, 0.0)) # world y-axis

        for i0, (_, (point, point1, _, handles, vert_normal)) in enumerate(map_points.items()):

            # NOTE:
            # - Assume 2 or 4 handles.
            # - In theory, this are faces with 2 handles per point.
            if len(handles) < 4:
                dir0 = (handles[1] - handles[0]).normalized()

                y_axis = dir0
                z_axis = vert_normal

            else:
                dir0 = (handles[0] - point).normalized() # point because "FREE" handle types
                dir1 = (handles[2] - point).normalized()

                y_axis = dir0
                x_axis = dir1
                z_axis = y_axis.cross(x_axis).normalized()

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
                eb_h.tail = handle + m.Vector((0., self.SIZE_BONES * 0.125, 0.)) # world y-axis
                eb_h.parent = eb_m
                eb_h.envelope_distance = \
                eb_h.head_radius = \
                eb_h.tail_radius = self.EPSILON

            eb_r = new_armature.edit_bones.new(f'm_point{i0}_radius') # radius
            eb_r.head = point1
            eb_r.tail = point1 + (point1 - point).normalized() * self.SIZE_BONES * 0.0625
            eb_r.parent = eb_root
            eb_r.envelope_distance = \
            eb_r.head_radius = \
            eb_r.tail_radius = self.EPSILON

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

            elif pb.name.startswith('m_point') \
            and not pb.name.endswith('_radius'):
                coll_main.assign(pb)

#                pb.lock_scale[2] = True

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

            elif pb.name.endswith('_radius'):
                coll_radius.assign(pb)

                pb.lock_location = (True, False, True)
                pb.lock_rotation = (True, True, True)
                pb.lock_rotation_w = True
                pb.lock_scale = (True, True, True)

                pb.color.palette = 'CUSTOM'
                pb.color.custom.select = COL_SELECT
                pb.color.custom.active = COL_ACTIVE

                pb.custom_shape = map_wgt['diamond']

                pb_parent = new_obj.pose.bones[pb.name[:-7]] # should exist

                constraint = pb.constraints.new('LIMIT_LOCATION')
                constraint.use_min_y = True
                constraint.use_max_y = True
                constraint.min_y = -(pb.head - pb_parent.head).length
                constraint.max_y = 1.0 + constraint.min_y
                constraint.use_transform_limit = True
                constraint.owner_space = 'LOCAL'

                constraint = pb.constraints.new('COPY_LOCATION')
                constraint.target = new_obj
                constraint.subtarget = pb_parent.name
                constraint.use_offset = True
                constraint.target_space = 'LOCAL_OWNER_ORIENT'
                constraint.owner_space = 'LOCAL'

        # TODO: Do not loop twice.
        def hash01(index: int) -> float:
#            return (x * 0.618034) % 1.0

            x = index
            x ^= x >> 16
            x *= 0x7feb352d
            x ^= x >> 15
            x *= 0x846ca68b
            x ^= x >> 16

            return (x & 0xFFFFFFFF) / 0xFFFFFFFF

        for index, pb in enumerate(new_obj.pose.bones):

            if pb.name.startswith('root'):
                continue

            elif '_handle' in pb.name:
                continue

            elif pb.name.endswith('_radius'):
                continue

            colour = m.Color()
            colour.hsv = (hash01(index), 1.0, 1.0)

            pb.color.custom.normal = colour

            colour.v = 0.8

            for c in pb.children:
                c.color.custom.normal = colour

            colour.v = 0.6

            pb_radius = new_obj.pose.bones[f'{pb.name}_radius'] # should exist
            pb_radius.color.custom.normal = colour

        context.view_layer.objects.active = obj_curve # view layer always needs an object

        if coll != context.scene.collection:
            context.scene.collection.objects.unlink(new_obj)

        return new_obj

    def _setup_modifiers(self, context, obj_curve: bpy.types.Object, obj_armature: bpy.types.Object) -> None:

        obj_mesh = obj_curve.data.sei_object

        #########
        # Add modifiers.

        # NOTE: Assume the first modifier found is used for the curve.
        mods = obj_curve.modifiers

        modifier = \
            next((m for m in mods if m.type == 'ARMATURE'), None) \
            or mods.new('Armature', 'ARMATURE')

        modifier.use_apply_on_spline = True
        modifier.object = obj_armature
        modifier.use_vertex_groups = False
        modifier.use_bone_envelopes = True

        mods.move(mods.find(modifier.name), 0)

        ###

        mods = obj_mesh.modifiers

        modifier = \
            next((m for m in mods if m.type == 'NODES'), None) \
            or mods.new('GeometryNodes', 'NODES')

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
        return \
        context.object \
        and context.object.type == 'CURVE' \
        and context.object.data.sei_object \
        and context.object.data.sei_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()
        col.prop(self, 'EPSILON')
        col.prop(self, 'RADIUS')

        col.separator()
        col.prop(self, 'SIZE_BONES')
        col.prop(self, 'WIRE_WIDTH')

    def execute(self, context):

        #########
        # Initialize.

        # NOTE: Important checks are taken care by poll().
        obj_curve = context.object

        obj_curve.hide_render = True
        active_mode = obj_curve.mode

        bpy.ops.object.mode_set(mode = 'OBJECT')

        #########
        # Setups.

        curve_data = self._setup_curve_data(context, obj_curve)
        map_points = self._setup_mesh(context, curve_data, obj_curve)
        obj_armature = self._setup_armature(context, map_points, obj_curve)
        self._setup_modifiers(context, obj_curve, obj_armature)

        #########
        # Finalize.

        bpy.ops.object.mode_set(mode = active_mode)

        context.view_layer.objects.active = obj_curve
        obj_curve.select_set(True)

        return {'FINISHED'}

class SEI_PT_curve(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

    bl_idname = 'SEI_PT_curve'
    bl_label = 'Curve Tools'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        obj = context.object

        if obj is None:
            layout.label(text = 'No Active Object', icon = 'INFO')
            return

        elif obj.type != 'CURVE':
            layout.label(text = 'Not Curve Type', icon = 'INFO')
            return

        col = layout.column()
        col.prop(obj.data, 'sei_object')
        col.operator(
            'sei.curve_to_mesh',
            text = 'Convert to Mesh',
            icon = 'MESH_DATA'
        )

# ===========================

classes = [
    SEI_OT_curve_to_mesh,
    SEI_PT_curve
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Curve.sei_object = bpy.props.PointerProperty(
        type = bpy.types.Object,
        name = 'Object',
        description = 'Object to retrieve mesh data'
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Curve.sei_object

if __name__ == "__main__": # debug; live edit
    register()
