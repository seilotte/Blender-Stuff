import bpy
import gpu
import os
import numpy as np

bl_info = {
    "name": "Sei Stencil",
    "author": "Seilotte",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "3D View > Properties > Sei",
    "description": "Creates a stencil pass for the viewport and final render.",
    "tracker_url": "seilotte.github.io",
    "doc_url": "seilotte.github.io",
    "category": "Workflow",
}

IMAGE_NAME = '_SSTENCIL'
DEBUG_MODE = True

class SEI_OT_view3d_stencil_visualizer(bpy.types.Operator):
    bl_idname = 'sei.view3d_stencil_visualizer'
    bl_label = 'Visualize Stencil'
    bl_description = 'Toggle the visibility of the stencil for the viewport'

    bl_options = {'REGISTER', 'UNDO'}

    _handle = None

    def _setup_image(self):
        if bpy.data.images.get(IMAGE_NAME) is None:
            bpy.data.images.new(IMAGE_NAME, 8, 8)

        image = bpy.data.images[IMAGE_NAME]
        image.use_fake_user = True
        image.colorspace_settings.name = 'Non-Color'
        image.pack()

        return image

    def _setup_shader(self):
        vsh = \
        '''
        in vec3 position;
        in vec4 vertex_colour;

        out vec3 vcol;

        uniform mat4 viewproj_matrix;
        uniform mat4 obj_matrix;

        void main()
        {
            gl_Position = viewproj_matrix * obj_matrix * vec4(position, 1.0);
            vcol = vertex_colour.rgb;
        }
        '''

        fsh = \
        '''
        in vec3 vcol;

        out vec4 col0;

        void main()
        {
            col0 = vec4(vcol, 1.0);
        }
        '''

        return gpu.types.GPUShader(vertexcode = vsh, fragcode = fsh)

    def draw_stencil(self, context, shader, image):
        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()

        coll = scene.collection_sstencil

        if coll is None:
            return

        batches_matrices = []

        for coll in [coll] + coll.children_recursive:
            for obj in coll.objects:
                if obj.type != 'MESH' \
                or obj.visible_get() is False:
                    continue

                # TODO: Use CBlenderMalt for better performance.
                mesh = obj.evaluated_get(depsgraph).data

                if mesh is None \
                or len(mesh.polygons) < 1:
                    continue

                vcol = mesh.attributes.get(mesh.attributes.default_color_name)

                if vcol is None:
                    vertices = np.empty((len(mesh.vertices), 3), 'f')
                    indices = np.empty((len(mesh.loop_triangles), 3), 'i')
                    colours = np.ones((len(mesh.vertices), 3), 'f') # white

                    mesh.vertices.foreach_get('co', vertices.ravel())
                    mesh.loop_triangles.foreach_get('vertices', indices.ravel())

                elif vcol.domain == 'POINT':
                    vertices = np.empty((len(mesh.vertices), 3), 'f')
                    indices = np.empty((len(mesh.loop_triangles), 3), 'i')
                    colours = np.empty((len(vcol.data), 4), 'f')

                    mesh.vertices.foreach_get('co', vertices.ravel())
                    mesh.loop_triangles.foreach_get('vertices', indices.ravel())
                    vcol.data.foreach_get('color', colours.ravel())

                elif vcol.domain == 'CORNER':
                    vertices = np.empty((len(mesh.vertices), 3), 'f')
                    indices = np.empty((len(mesh.loop_triangles), 3), 'i')
                    colours = np.empty((len(vcol.data), 4), 'f')

                    mesh.vertices.foreach_get('co', vertices.ravel())
                    mesh.loop_triangles.foreach_get('loops', indices.ravel())
                    vcol.data.foreach_get('color', colours.ravel())

                    vertices = vertices[[l.vertex_index for l in mesh.loops]]

                vbo_format = gpu.types.GPUVertFormat()
                vbo_format.attr_add(
                    id='position', comp_type='F32', len=len(vertices[0]), fetch_mode='FLOAT')
                vbo_format.attr_add(
                    id='vertex_colour', comp_type='F32', len=len(colours[0]), fetch_mode='FLOAT')

                vbo = gpu.types.GPUVertBuf(vbo_format, len(vertices))
                vbo.attr_fill('position', vertices)
                vbo.attr_fill('vertex_colour', colours)

                ibo = gpu.types.GPUIndexBuf(type='TRIS', seq=indices)

                batches_matrices.append((
                    gpu.types.GPUBatch(type='TRIS', buf=vbo, elem=ibo),
                    obj.matrix_world
                ))

        if context and context.region_data.view_perspective != 'CAMERA':
            _, _, width, height = gpu.state.viewport_get()

            matrix = context.region_data.perspective_matrix

        else:
            width = scene.render.resolution_x
            height = scene.render.resolution_y

            matrix = \
            scene.camera.calc_matrix_camera(depsgraph, x=width, y=height) \
            @ scene.camera.matrix_world.inverted()

        width  = width * scene.render.resolution_percentage // 100
        height = height * scene.render.resolution_percentage // 100

        offscreen = gpu.types.GPUOffScreen(width, height, format='RGBA8')

        with offscreen.bind():
            framebuffer = gpu.state.active_framebuffer_get()
            framebuffer.clear(depth = 1.0)

            gpu.state.depth_mask_set(True)
            gpu.state.depth_test_set('LESS')
            gpu.state.blend_set('NONE')

            shader.uniform_float('viewproj_matrix', matrix)

            for batch, obj_matrix in batches_matrices:
                shader.uniform_float('obj_matrix', obj_matrix)
                batch.draw(shader)

            buffer = framebuffer.read_color(0, 0, width, height, 4, 0, 'FLOAT')
            buffer.dimensions = width * height * 4

        offscreen.free()

        image.scale(width, height)
        image.pixels.foreach_set(buffer)


    @classmethod
    def poll(cls, context):
        return \
        context.area \
        and context.area.type == 'VIEW_3D' \
        and context.scene.collection_sstencil \
        and context.scene.collection_sstencil.all_objects

    def execute(self, context):
        if SEI_OT_view3d_stencil_visualizer._handle:
            bpy.types.SpaceView3D.draw_handler_remove(
                SEI_OT_view3d_stencil_visualizer._handle,
                'WINDOW'
            )
            SEI_OT_view3d_stencil_visualizer._handle = None

        else:
            image = self._setup_image()
            shader = self._setup_shader()

            SEI_OT_view3d_stencil_visualizer._handle = \
            bpy.types.SpaceView3D.draw_handler_add(
                self.draw_stencil,
                (context, shader, image),
                'WINDOW',
                'POST_PIXEL'
            )

        context.area.tag_redraw()

        return {'FINISHED'}

class SEI_OT_stencil_render(bpy.types.Operator):
    bl_idname = 'sei.stencil_render'
    bl_label = 'Render Stencil'
    bl_description = 'Render active scene with the stencil.'

    bl_options = {'REGISTER', 'UNDO'}

    render_image: bpy.props.BoolProperty(name='Render Image')

    @classmethod
    def poll(cls, context):
        return \
        context.scene.collection_sstencil \
        and context.scene.collection_sstencil.all_objects

    def execute(self, context):
        def print_message(message: str="") -> None:
            if DEBUG_MODE is True:
                print(f'SStencil: {message}')

        #########
        # Initialize values.
        _saved_nodes = []
        _saved_attrs_objects = []
        _saved_attrs_render = []
        _saved_attrs_nodes = []

        _tmp_filepath = ''
        _tmp_image = None

        scene = context.scene

        #########
        # Verify collection.

        # NOTE: poll() takes care of it.
        coll = scene.collection_sstencil

        # TODO: Return if collection_layer.exclude.
        coll.hide_render = False

        #########
        # Get and hide non stencil objects attributes.
        print_message('Get and hide non stencil objects.')

        for obj in scene.objects:
            if obj.type == 'CAMERA' \
            or obj.hide_render is True \
            or obj.name in coll.all_objects:
                continue

            # Save and set.
            _saved_attrs_objects.append((obj, obj.hide_render))
            obj.hide_render = True

        #########
        # Get the image nodes.
        print_message('Get the image nodes.')

        # TODO: Only get scene materials.
        for mat in bpy.data.materials:
            stack = [mat.node_tree]

            while stack:
                current_tree = stack.pop()

                for node in current_tree.nodes:
                    if node.type == 'GROUP':
                        stack.append(node.node_tree)

                    elif node.type == 'TEX_IMAGE' \
                    and node.image \
                    and node.image.name == IMAGE_NAME:
                        _saved_nodes.append(node)

        if not _saved_nodes:
            self.report({'WARNING'}, f'No nodes were found with the image named "{IMAGE_NAME}".')
            return {'FINISHED'}

        #########
        # Get and create the new filepath.
        print_message('Get and create the new filepath.')

        org_filepath = bpy.path.abspath(scene.render.filepath)

        # TODO: bpy.ops.render.render() creates the filepath.
        if os.path.exists(org_filepath) is False:
            self.report({'WARNING'}, f'The specified render filepath does not exist: {org_filepath}')
            return {'FINISHED'}

        directory, filename = os.path.split(org_filepath)
        # name, extension = os.path.splitext(filename)

        _tmp_filepath = os.path.join(directory, '_tmp_sstencil') + os.sep
        os.makedirs(_tmp_filepath, exist_ok=True)

        del org_filepath

        #########
        # Get and set the render attributes.
        print_message('Get and set the render attributes.')

        # NOTE: A dictionary added unecessary complexity.
        attrs_render = [
            (scene.render, 'engine', 'BLENDER_WORKBENCH'),
            (scene.render, 'use_simplify', False),
            (scene.render, 'film_transparent', True),
            (scene.render, 'use_freestyle', False),
            (scene.render, 'use_compositing', False),
            (scene.render, 'use_sequencer', False),
            (scene.render, 'use_file_extension', True),
            (scene.render, 'use_render_cache', False),
            (scene.render, 'use_overwrite', True),
            (scene.render, 'use_placeholder', False),
            (scene.render, 'filepath', _tmp_filepath),

            (scene.display, 'render_aa', '8'),

            (scene.grease_pencil_settings, 'antialias_threshold', 1.0),

            (scene.display.shading, 'light', 'FLAT'),
            (scene.display.shading, 'color_type', 'VERTEX'),
            (scene.display.shading, 'show_backface_culling', False),
            (scene.display.shading, 'show_xray', False),
            (scene.display.shading, 'show_shadows', False),
            (scene.display.shading, 'show_cavity', False),
            (scene.display.shading, 'use_dof', False),
            (scene.display.shading, 'show_object_outline', False),

            (scene.display_settings, 'display_device', 'sRGB'),

            (scene.render.image_settings.view_settings, 'view_transform', 'Standard'),
            (scene.render.image_settings.view_settings, 'look', 'None'),
            (scene.render.image_settings.view_settings, 'exposure', 0.0),
            (scene.render.image_settings.view_settings, 'gamma', 1.0),
            (scene.render.image_settings.view_settings, 'use_curve_mapping', False),
            (scene.render.image_settings.view_settings, 'use_white_balance', False),

            (scene.render.image_settings, 'file_format', 'OPEN_EXR'), # order matters
            (scene.render.image_settings, 'color_mode', 'RGBA'),
            (scene.render.image_settings, 'color_depth', '16'),
            (scene.render.image_settings, 'exr_codec', 'ZIP')
        ]

        # Save and set.
        for obj, attr, value in attrs_render:
            if hasattr(obj, attr):
                _saved_attrs_render.append((obj, attr, getattr(obj, attr)))
                setattr(obj, attr, value)

        del attrs_render

        #########
        # Render (stencil images).
        print_message('Rendering the stencil images.')

        if self.render_image:
            bpy.ops.render.render(write_still=True, use_viewport=True)
        else:
            bpy.ops.render.render(animation=True, use_viewport=True)

        #########
        # Restore the attributes.
        print_message('Restoring the attributes.')

        coll.hide_render = True

        for obj, value in _saved_attrs_objects:
            obj.hide_render = value

        # NOTE: reversed() restores dependant attributes
        # (e.g., PNG vs. OPEN_EXR) in the correct order.
        for obj, attr, value in reversed(_saved_attrs_render):
            if hasattr(obj, attr):
                setattr(obj, attr, value)

        #########
        # Set the image sequence.
        print_message('Setting the image sequence to the image nodes.')

        attrs_nodes = []

        stencil_frames = os.listdir(_tmp_filepath)
        stencil_frames_length = len(stencil_frames)

        node_filepath = os.path.join(_tmp_filepath, sorted(stencil_frames)[0])

        _tmp_image = bpy.data.images.load(node_filepath)

        for node in _saved_nodes:
            # Save and set.
            if hasattr(node, 'image'):
                _saved_attrs_nodes.append((node, 'image', node.image))
                node.image = _tmp_image

            if self.render_image:
                continue

            attrs_nodes = [
                (node.image.colorspace_settings, 'name', 'Non-Color'),

                (node.image, 'source', 'SEQUENCE'),

                (node.image_user, 'frame_duration', stencil_frames_length),
                (node.image_user, 'frame_start', 1),
                (node.image_user, 'frame_offset', scene.frame_start - 1)
            ]

            # Set.
            for obj, attr, value in attrs_nodes:
                if hasattr(obj, attr):
                    setattr(obj, attr, value)

        del attrs_nodes, stencil_frames, stencil_frames_length, node_filepath

        #########
        # Render (normally).
        print_message('Rendering.')

        if self.render_image:
            bpy.ops.render.render(write_still=False, use_viewport=True)
        else:
            bpy.ops.render.render(animation=True, use_viewport=True)

        #########
        # Restore the image nodes attributes.
        print_message('Restoring the image nodes attributes.')

        # NOTE: reversed() restores...
        for obj, attr, value in reversed(_saved_attrs_nodes):
            if hasattr(obj, attr):
                setattr(obj, attr, value)

        #########
        # Delete the temporary files.
        print_message('Deleting the temporary files.')

        bpy.data.images.remove(_tmp_image)

        for file in os.listdir(_tmp_filepath):
            filepath = os.path.join(_tmp_filepath, file)

            if os.path.isfile(filepath):
                os.remove(filepath)

        os.rmdir(_tmp_filepath)

        ###

        self.report({'INFO'}, 'Successfully rendered the image(s).')
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'render_image') # RENDER_STILL

class SEI_PT_stencil(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

    bl_idname = 'SEI_PT_stencil'
    bl_label = 'Stencil Tools'

    def draw_header(self, context):
        self.layout.operator('wm.url_open', text='', icon='HELP').url = 'seilotte.github.io'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()
        col.prop(context.scene, 'collection_sstencil')
        col.operator(
            'sei.view3d_stencil_visualizer',
            text = 'Visualize',
            icon = 'PAUSE' if SEI_OT_view3d_stencil_visualizer._handle else 'PLAY'
        )
        col.operator(
            'sei.stencil_render',
            text = 'Render Animation',
            icon = 'RENDER_ANIMATION'
        )

        layout.separator()

        col = layout.column(align=True)
        col.prop(context.scene.render, "resolution_x", text="Resolution X")
        col.prop(context.scene.render, "resolution_y", text="Y")
        col.prop(context.scene.render, "resolution_percentage", text="%")

# ===========================

classes = [
    SEI_OT_view3d_stencil_visualizer,
    SEI_OT_stencil_render,
    SEI_PT_stencil
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.collection_sstencil = bpy.props.PointerProperty(
        type = bpy.types.Collection,
        name = 'Collection',
        description = 'Collection to retrieve objects'
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.collection_sstencil

if __name__ == "__main__": # debug; live edit
    register()
