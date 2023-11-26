'''
The code assumes you have an image node selected in the active object.
Make sure just the desired object is selected and it is not shade flat.
Read the code to change the settings.

TODO: Fix "Info:" errors when baking.
'''
import bpy
from math import radians

scene = bpy.context.scene
active_engine = scene.render.engine

if active_engine != 'CYCLES':
    scene.render.engine = 'CYCLES'

# Set render settings.
scene.cycles.use_adaptive_sampling = False
scene.cycles.samples = 32
scene.cycles.use_denoising = False

scene.cycles.bake_type = 'NORMAL'
scene.render.bake.normal_space = 'TANGENT'
scene.render.bake.target = 'IMAGE_TEXTURES' # VERTEX_COLORS
scene.render.bake.use_clear = True
scene.render.bake.margin = 16
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.0001

# Duplicate object.
obj = bpy.context.active_object
bpy.ops.object.duplicate(linked=False) # Ops is more convinient in this case.
tmp_obj = bpy.context.active_object

bpy.context.view_layer.objects.active = obj
obj.select_set(True)

#obj.data.shade_flat()
obj.data.shade_smooth()
obj.data.use_auto_smooth = False

tmp_obj.data.shade_smooth()
tmp_obj.data.use_auto_smooth = True
tmp_obj.data.auto_smooth_angle = radians(180)

# Create image.
tmp_image = bpy.data.images.new(
    name = "tmp_" + obj.name,
    width = 2048,
    height = 2048,
    alpha = False,
    is_data = True,
)

material = obj.active_material
tex_node = material.node_tree.nodes.active
tex_node.image = tmp_image

bpy.ops.object.bake(type='NORMAL')

obj.data.shade_smooth()
obj.data.use_auto_smooth = True
obj.data.auto_smooth_angle = radians(180)

scene.render.engine = active_engine

# Save image to directory.
# Careful! It will replace the image if it matches the name.
file_name = f'nmap_{obj.name}.png'
dir = "//" + file_name # Replace "//" with your directory.

tmp_image.filepath_raw = dir
tmp_image.file_format = 'PNG'
tmp_image.save()

bpy.data.images.remove(tmp_image, do_unlink=True)
bpy.data.meshes.remove(tmp_obj.data, do_unlink=True)

print(f'INFO: Successfully saved "{file_name}" in "{dir}".')