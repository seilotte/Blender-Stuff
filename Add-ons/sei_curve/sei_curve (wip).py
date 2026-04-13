'''
TODO:
    - GPU View.
    - Auto create & assign the geometry nodes node group.
    - Do not duplicate the objects every time 'blender.ops.sei.curve_to_curves()' is called.
    - Align bones; how?
'''

import bpy
import mathutils as m

bl_info = {
    "name": "Sei Curve",
    "author": "Seilotte",
    "version": (0, 0, 0),
    "blender": (5, 1, 1),
    "location": "3D View > Properties > Sei",
    "description": "",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/sei_curve",
    "doc_url": "https://github.com/seilotte/Blender-Stuff/issues",
    "category": "Workflow",
}

class SEI_OT_curve_object_update(bpy.types.Operator):
    bl_idname = 'sei.curve_object_update'
    bl_label = 'Update Curve Object'
    bl_description = 'Update the referenced object'

    bl_options = {'REGISTER', 'UNDO'}

    epsilon: bpy.props.FloatProperty(
        name = 'Merge Distance',
        description = 'Maximum distance between elements to merge',
        default = 1e-6,
        min = 1e-7
    )

    @classmethod
    def poll(cls, context):
        return \
        context.object \
        and context.object.type == 'CURVE' \
        and context.object.data.sei_object \
        and context.object.data.sei_object.type == 'MESH'

    def execute(self, context):

        #########
        # Initialize.

        # NOTE: Important checks are taken care by poll().
        obj_curve = context.object
        obj_proxy = obj_curve.data.sei_object

        obj_proxy.name = f'{obj_curve.name}_proxy'
        obj_proxy.data.name = obj_proxy.name

        obj_proxy.hide_render = True

        active_mode = obj_curve.mode
        bpy.ops.object.mode_set(mode = 'OBJECT')

        #########
        # Get old mesh data (object).

        mesh = obj_proxy.data

        old_verts = [v.co for v in mesh.vertices]
#        old_edges = [tuple(e.vertices) for e in mesh.edges]
        old_faces = [tuple(f.vertices) for f in mesh.polygons]

        #########
        # Get new mesh data (curve).

        new_verts = []
        new_edges = []
        new_faces = []

        counter = 0

        for curve in obj_curve.data.splines:
            verts = [v.co for v in curve.bezier_points]
            edges = [(v, v + 1) for v in range(len(verts) - 1)]

            if curve.use_cyclic_u is True:
                edges.append((len(verts) - 1, 0))

            edges = [(a + counter, b + counter) for a, b in edges]

            new_verts.extend(verts)
            new_edges.extend(edges)

            counter += len(verts)

        ###

        map_verts2new = {}

        for old_i, old_v in enumerate(old_verts):
            for new_i, new_v in enumerate(new_verts):
                if (old_v - new_v).length < self.epsilon:
                    map_verts2new[old_i] = new_i
                    break

        for face in old_faces:
            try:
                face_new = tuple(map_verts2new[v] for v in face)

                if len(set(face_new)) == len(face_new): # no duplicates
                    new_faces.append(face_new)

            except KeyError:
                continue # vertex has been deleted

        #########
        # Create mesh.

        mesh = obj_proxy.data

        mesh.clear_geometry()
        mesh.from_pydata(new_verts, new_edges, new_faces)
        mesh.validate()
        mesh.update()

        #########
        # Finalize.

        bpy.ops.object.mode_set(mode = active_mode)

        context.view_layer.objects.active = obj_curve
        obj_curve.select_set(True)

        return {'FINISHED'}

class SEI_OT_curve_to_mesh(bpy.types.Operator):
    bl_idname = 'sei.curve_to_mesh'
    bl_label = 'Convert to Mesh'
    bl_description = 'Convert the curve to a mesh type'

    bl_options = {'REGISTER', 'UNDO'}

    epsilon: bpy.props.FloatProperty(
        name = 'Merge Distance',
        description = 'Maximum distance between elements to merge',
        default = 1e-6,
        min = 1e-7
    )

    size_bones: bpy.props.FloatProperty(
        name = 'Bones Scale',
        description = 'Global bones scale',
        default = 0.01,
        min = 0.0
    )

    def _setup_curves_data(self, context, obj_curve: bpy.types.Object) -> tuple[bpy.types.Curves, list, set]:

        #########
        # Convert to "CURVES" type.

        # NOTE: This way, data is easier to read, like the curve normal.
        # TODO: Do not use depsgraph, we want the data without modifiers, animations, etc.
        depsgraph = context.evaluated_depsgraph_get()
        geometry = depsgraph.id_eval_get(obj_curve).evaluated_geometry()

        new_curves = geometry.curves.copy()
        new_curves.name = f'{obj_curve.name}_sei'

        #########
        # Split curve at each point.

        split_edges = [] # (p0, p1)

        for curve in new_curves.curves:
            verts = [v for v in curve.points]

            is_cyclic = new_curves.attributes['cyclic'].data[curve.index].value
            verts_len = len(verts) if is_cyclic else len(verts) - 1

            for i in range(verts_len):
                p0 = verts[i]
                p1 = verts[(i + 1) % len(verts)]

                split_edges.append((p0, p1))

        #########
        # Map curves points to faces.

        new_edges = [] # (p0, p1, is_reversed, face_index)

        obj_proxy = obj_curve.data.sei_object
        mesh = obj_proxy.data

        for face in mesh.polygons:
            for i in range(face.loop_total):

                loop0 = mesh.loops[face.loop_indices[i]]
                loop1 = mesh.loops[face.loop_indices[(i + 1) % face.loop_total]]

                v0 = mesh.vertices[loop0.vertex_index]
                v1 = mesh.vertices[loop1.vertex_index]

                # Find the curve points.
                new_p0 = new_p1 = None
                is_reversed = False

                for split_edge in split_edges:
                    split_v0, split_v1 = split_edge

                    if (
                        (v0.co - split_v0.position).length < self.epsilon and
                        (v1.co - split_v1.position).length < self.epsilon
                    ):
                        new_p0 = split_v0
                        new_p1 = split_v1
                        break

                    elif (
                        (v0.co - split_v1.position).length < self.epsilon and
                        (v1.co - split_v0.position).length < self.epsilon
                    ):
                        new_p0 = split_v1
                        new_p1 = split_v0
                        is_reversed = True
                        break

                if new_p0 is None or new_p1 is None:
                    raise ValueError(f'Failed to match vertices from "{mesh.name}" to "{new_curves.name}". Try increasing "Merge Distance".')

                new_edges.append((new_p0, new_p1, is_reversed, face.index))

        #########
        # Dedup edges (curves).

        dedup_edges = {} # point_index: {handles}

        for p0, p1, _, _ in new_edges:
            for point in (p0, p1):

                position = point.position
                handle_left = new_curves.attributes['handle_left'].data[point.index].vector
                handle_right = new_curves.attributes['handle_right'].data[point.index].vector

                # add point
                for index in dedup_edges.keys():
                    p = new_curves.points[index].position

                    if (p - position).length < self.epsilon:
                        found_index = index
                        break
                else:
                    found_index = point.index
                    dedup_edges[found_index] = set()

                # add handles
                for handle in (handle_left, handle_right):
                    for h in dedup_edges[found_index]:
                        if (h - handle).length < self.epsilon:
                            break
                    else:
                        dedup_edges[found_index].add(handle.copy().freeze())

        return new_curves, new_edges, dedup_edges

    def _setup_armature(self, context, curves_data: tuple, coll: bpy.types.Collection, obj_curve: bpy.types.Object) -> bpy.types.Object:

        curves = curves_data[0] # object
        curves_edges_dedup = curves_data[2] # set; {point_index: {handles}}

        #########
        # Create widgets.

        def mesh_create(name = 'Mesh', vertices = [], edges = [], faces = []):
            obj = bpy.data.objects.get(name)

            if obj is None:
                mesh = bpy.data.meshes.new(name = name)

                mesh.from_pydata(vertices, edges, faces)
                mesh.validate()
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
            'axes': mesh_create( # TODO: Just x & y.
                name = 'WGT-Axes',
                vertices = [(-0.5, 0.0, 0.0), (0.5, 0.0, 0.0), (0.0, -0.5, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, -0.5), (0.0, 0.0, 0.5), (-0.125, 0.5, 0.0), (0.125, 0.5, 0.0)],
                edges = [[0, 1], [2, 3], [4, 5], [6, 7]]
            ),
            'cube': mesh_create(
                name = 'WGT-Cube',
                vertices = [(-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.0, 0.5, 0.0), (0.0, 0.8, 0.0)],
                edges = [[2, 0], [0, 1], [1, 3], [3, 2], [6, 2], [3, 7], [7, 6], [4, 6], [7, 5], [5, 4], [0, 4], [5, 1], [8, 9]]
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
        # Create armature.

        new_armature = bpy.data.armatures.new(f'{curves.name[:-4]}_rig')
        new_obj = bpy.data.objects.new(new_armature.name, new_armature)

#        coll.objects.link(new_obj)

        new_obj.hide_render = True
        new_obj.show_in_front = True
        new_obj.display_type = 'WIRE'
#        new_obj.display_type = 'ENVELOPE'

        context.scene.collection.objects.link(new_obj) # scene collection is always active
        context.view_layer.objects.active = new_obj

        # collections
        coll_main = new_armature.collections.new('Main')
        coll_handles = new_armature.collections.new('Handles')

        # edit bones
        bpy.ops.object.mode_set(mode = 'EDIT')

        eb_root = new_armature.edit_bones.new('root')
        eb_root.tail = eb_root.head + m.Vector((0.0, self.size_bones * 10.0, 0.0)) # world y-axis

        for i0, (point_index, handles) in enumerate(curves_edges_dedup.items()):
            point = curves.points[point_index]
#            normal = curves.normals[point_index].vector

            eb_m = new_armature.edit_bones.new(f'm_point{i0}') # middle
            eb_m.head = point.position
            eb_m.tail = list(handles)[0] # TODO: Deterministic.
            eb_m.length = self.size_bones * 0.5
            eb_m.parent = eb_root
            eb_m.envelope_distance = 1e-4
            eb_m.head_radius = 1e-4
            eb_m.tail_radius = 1e-4

            for i1, handle in enumerate(handles):
                eb_h = new_armature.edit_bones.new(f'{i0}_handle{i1}')
                eb_h.head = handle
                eb_h.tail = eb_h.head + m.Vector((0., self.size_bones * 0.125, 0.)) # world y-axis
                eb_h.parent = eb_m
                eb_h.envelope_distance = 1e-4
                eb_h.head_radius = 1e-4
                eb_h.tail_radius = 1e-4

        # pose bones
        bpy.ops.object.mode_set(mode = 'OBJECT')

        for pb in new_obj.pose.bones:
            pb.rotation_mode = 'XYZ' # gimbal lock

            pb.custom_shape_wire_width = 4.0

            if pb.name.startswith('root'):
                coll_main.assign(pb)

                pb.custom_shape = map_wgt['plane']
                pb.custom_shape_scale_xyz[0] = 0.5
                pb.custom_shape_translation[1] = pb.bone.length * 0.5

            elif pb.name.startswith('m_point'):
                coll_main.assign(pb)

                # TODO: Lock the perpendicular axes relative to the curve tangent.
#                pb.lock_scale[2] = True

                pb.color.palette = 'CUSTOM'
                pb.color.custom.normal = (1.0, 1.0, 0.0) # yellow
                pb.color.custom.select = (0.6, 0.9, 1.0)
                pb.color.custom.active = (0.7, 1.0, 1.0)

                pb.custom_shape = map_wgt['axes']

            elif '_handle' in pb.name:
                coll_handles.assign(pb)

                pb.lock_rotation = (True, True, True)
                pb.lock_rotation_w = True
                pb.lock_scale = (True, True, True)

                pb.color.palette = 'CUSTOM'
                pb.color.custom.normal = (0.0, 1.0, 0.7) # aqua
                pb.color.custom.select = (0.6, 0.9, 1.0)
                pb.color.custom.active = (0.7, 1.0, 1.0)

                pb.custom_shape = map_wgt['cube']

                constraint = pb.constraints.new('COPY_ROTATION')
                constraint.target = new_obj
                constraint.subtarget = 'root'

                constraint = pb.constraints.new('COPY_SCALE')
                constraint.target = new_obj
                constraint.subtarget = 'root'

        context.view_layer.objects.active = obj_curve # view layer always needs an object
        context.scene.collection.objects.unlink(new_obj)

        coll.objects.link(new_obj)

        return new_obj

    def _setup_curve(self, context, curves_data: tuple, coll: bpy.types.Collection, obj_armature: bpy.types.Object) -> bpy.types.Object:

        curves = curves_data[0] # object
        curves_edges = curves_data[1] # list; (p0, p1, is_reversed, face_index)

        #########
        # Create curve.

        new_curve = bpy.data.curves.new(f'{curves.name[:-4]}_mesh', 'CURVE')
        new_obj = bpy.data.objects.new(new_curve.name, new_curve)

        coll.objects.link(new_obj)

        new_curve.dimensions = '3D'

        for p0, p1, is_reversed, face_index in curves_edges:
            spline = new_curve.splines.new('BEZIER')
            spline.bezier_points.add(1)

            for i in range(2):
                point = spline.bezier_points[i]
                p = p0 if i == 0 else p1

                point.co = p.position

                point.handle_left_type = 'FREE'
                point.handle_right_type = 'FREE'

                hl = curves.attributes['handle_left'].data[p.index].vector
                hr = curves.attributes['handle_right'].data[p.index].vector

                point.handle_left = hr if is_reversed else hl
                point.handle_right = hl if is_reversed else hr

                # NOTE: I have never seen someone use this property.
                point.radius = face_index

        #########
        # Add modifiers.

        # TODO: Create the node group.
        modifier = new_obj.modifiers.new('GeometryNodes', 'NODES')
        modifier = new_obj.modifiers.new('Armature', 'ARMATURE')

        modifier.use_apply_on_spline = True
        modifier.object = obj_armature
        modifier.use_vertex_groups = False
        modifier.use_bone_envelopes = True

        new_obj.modifiers.move(len(new_obj.modifiers) - 1, 0)

        return new_obj

    @classmethod
    def poll(cls, context):
        return \
        context.object \
        and context.object.type == 'CURVE' \
        and context.object.data.sei_object \
        and context.object.data.sei_object.type == 'MESH'

    def execute(self, context):

        #########
        # Initialize.

        # NOTE: Important checks are taken care by poll().
        obj_curve = context.object

        obj_curve.hide_render = True
        active_mode = obj_curve.mode

        bpy.ops.object.mode_set(mode = 'OBJECT')

        #########
        # Setup collection.

        coll = bpy.data.collections.get(f'coll_{obj_curve.name}')

        if coll is None:
            coll = bpy.data.collections.new(f'coll_{obj_curve.name}')
            obj_curve.users_collection[0].children.link(coll)

        #########
        # Setups.

        bpy.ops.sei.curve_object_update()

        tmp_curves_data = self._setup_curves_data(context, obj_curve) # (object, list_edges)
        new_obj_armature = self._setup_armature(context, tmp_curves_data, coll, obj_curve)
        new_obj_curve = self._setup_curve(context, tmp_curves_data, coll, new_obj_armature)

        #########
        # Finalize.

        bpy.data.hair_curves.remove(tmp_curves_data[0], do_unlink = True)

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

        obj = context.active_object

        if obj is None:
            layout.label(text = 'No Active Curve', icon = 'INFO')
            return

        elif obj.type != 'CURVE':
            layout.label(text = 'Not Curve Type', icon = 'INFO')
            return

        col = layout.column()
        col.prop(context.object.data, 'sei_object')
        col.operator(
            'sei.curve_object_update',
            text = 'Update',
            icon = 'FILE_REFRESH'
        )

        col.separator()
        col.operator(
            'sei.curve_to_mesh',
            text = 'Convert to Mesh',
            icon = 'MESH_DATA'
        )

# ===========================

classes = [
    SEI_OT_curve_object_update,
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
