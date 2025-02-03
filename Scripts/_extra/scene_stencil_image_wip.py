import bpy
import gpu
import numpy as np

from gpu_extras.batch import batch_for_shader

shader = gpu.types.GPUShader(
    vertexcode = \
    '''
    in vec3 position;
    in int index_object;

    flat out int index;

    uniform mat4 viewproj_matrix;

    void main()
    {
        gl_Position = viewproj_matrix * vec4(position, 1.0);
        index = index_object;
    }
    ''',

    fragcode = \
    '''
    flat in int index;

    out vec4 col0;

    void main()
    {
        // debug; random colour
        /*
        int r = (index * 12345) & 255;
        int g = (index * 6789) & 255;
        int b = (index * 13579) & 255;

        col0 = vec4(vec3(r, g, b) / 255.0, 1.0);
        */
        col0 = vec4(vec3(index) / 255.0, 1.0);
    }
    '''
)

def draw_stencil(self, context, image):
    scene = context.scene
    depsgraph = context.evaluated_depsgraph_get()

    coll = scene.get('collection_stencil')

    if coll is None:
        return

    vertices = []
    indices = []
    indices_obj = []

    counter = 1
    offset = 0

    for coll in [coll] + coll.children_recursive:
        for obj in coll.objects:
            if obj.type != 'MESH' \
            or obj.visible_get() is False:
                continue

            # TODO: Use CBlenderMalt for better performance?
            mesh = obj.evaluated_get(depsgraph).data
            mesh.calc_loop_triangles()

            v = np.empty((len(mesh.vertices), 3), 'f')
            i = np.empty((len(mesh.loop_triangles), 3), 'i')
#            c = np.empty((len(mesh.vertices), 4), 'f')
            i_obj = np.full(len(v), counter, dtype = int)

            mesh.vertices.foreach_get('co', v.ravel())
            mesh.loop_triangles.foreach_get('vertices', i.ravel())
#            mesh.attributes['Color'].data.foreach_get('color', c.ravel())

            vertices.append(v)
            indices.append(i + offset)
            indices_obj.append(i_obj)

            offset += len(v)
            counter += 1

    if not vertices or not indices:
        return

    del counter, offset

    vertices = np.concatenate(vertices, axis=0)
    indices = np.concatenate(indices, axis=0)
    indices_obj = np.concatenate(indices_obj, axis=0)

#    print(vertices, indices, indices_obj)

    batch = batch_for_shader(
        shader,
        'TRIS',
        {
            "position": vertices,
            "index_object": indices_obj,
        },
        indices = indices,
    )

    del vertices, indices, indices_obj

    if context and context.region_data.view_perspective != 'CAMERA':
        _, _, width, height = gpu.state.viewport_get()

        matrix = context.region_data.perspective_matrix

    else:
        width = scene.render.resolution_x
        height = scene.render.resolution_y

        matrix = \
        scene.camera.calc_matrix_camera(depsgraph, x=width, y=height) \
        @ scene.camera.matrix_world.inverted()

    width  = round((scene.render.resolution_percentage / 100) * width)
    height = round((scene.render.resolution_percentage / 100) * height)

    offscreen = gpu.types.GPUOffScreen(width, height, format = 'RGBA8')
    with offscreen.bind():
        framebuffer = gpu.state.active_framebuffer_get()
        framebuffer.clear(depth = 1.0)

        gpu.state.depth_mask_set(True)
        gpu.state.depth_test_set('LESS')
        gpu.state.blend_set('NONE')

        shader.uniform_float('viewproj_matrix', matrix)
        batch.draw(shader)

        buffer = framebuffer.read_color(0, 0, width, height, 4, 0, 'FLOAT')
        buffer.dimensions = width * height * 4

    offscreen.free()

    image.scale(width, height)
    image.pixels.foreach_set(buffer)

class SEI_OT_stencil(bpy.types.Operator):
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    bl_idname = 'sei.stencil'
    bl_label = 'Stencil'
    bl_description = 'Toggle stencil'

    _handle = None

    def execute(self, context):
        if SEI_OT_stencil._handle:
            bpy.types.SpaceView3D.draw_handler_remove(
                SEI_OT_stencil._handle,
                'WINDOW'
            )
            SEI_OT_stencil._handle = None

        else:
            if '_STENCIL' not in bpy.data.images:
                bpy.data.images.new('_STENCIL', 2, 2, float_buffer=False)

            image = bpy.data.images['_STENCIL']
            image.use_fake_user = True
            image.colorspace_settings.name = 'Non-Color'
#            image.pack()

            SEI_OT_stencil._handle = \
            bpy.types.SpaceView3D.draw_handler_add(
                draw_stencil,
                (self, context, image),
                'WINDOW',
                'POST_PIXEL' # POST_PIXEL;PRE_VIEW;POST_VIEW
            )

        context.area.tag_redraw()

        return {'FINISHED'}

class SEI_PT_stencil(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stencil'

    bl_idname = 'SEI_PT_stencil'
    bl_label = 'Stencil Tools'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()
        col.prop(context.scene, 'collection_stencil')
        col.operator(
            'sei.stencil',
            icon = 'PAUSE' if SEI_OT_stencil._handle else 'PLAY'
        )

        layout.separator()

        col = layout.column(align=True)
        col.prop(context.scene.render, "resolution_x", text="Resolution X")
        col.prop(context.scene.render, "resolution_y", text="Y")
        col.prop(context.scene.render, "resolution_percentage", text="%")

#===========================

classes = [
    SEI_PT_stencil,
    SEI_OT_stencil
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.collection_stencil = bpy.props.PointerProperty(
        type = bpy.types.Collection,
        name = 'Collection',
        description = 'Collection to retrieve objects'
    )

    # temporay; does not work
    # TODO: Render an image sequence?
#    bpy.app.handlers.render_pre[:] = [i for i in bpy.app.handlers.render_pre if i.__name__ != 'draw_stencil']
#    bpy.app.handlers.render_pre.append(draw_stencil)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.collection_stencil

if __name__ == "__main__":
    register()