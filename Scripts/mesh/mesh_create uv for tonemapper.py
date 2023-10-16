import bpy

# Create UV ToneMapper for https://www.youtube.com/watch?v=oNBgbxif-dU
# Tested on: b3.5.1

# Make sure to purge the data when running the script!
# Editor Type > Outliner > Orphan Data > Purge

uv_name = 'UVTone_Mapper'
original_obj = bpy.context.active_object

if original_obj and original_obj.type == 'MESH':
    new_uv = original_obj.data.uv_layers.get(uv_name)
    if not new_uv:
        new_uv = original_obj.data.uv_layers.new(name=uv_name)
    original_obj.data.uv_layers.active = new_uv

    bpy.ops.object.duplicate()
    obj = bpy.context.active_object

    bpy.ops.object.convert(target='MESH')

    for i in range(len(obj.data.uv_layers) -1, -1, -1): # Fix when deleting UV's.
        uv_layer = obj.data.uv_layers[i]
        if uv_layer.name != uv_name:
            obj.data.uv_layers.remove(uv_layer)

    # Project from view.
    active_mode = bpy.context.mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # https://blender.stackexchange.com/questions/99035/how-to-unwrap-project-from-view-with-script
    # https://docs.blender.org/api/blender_python_api_2_64a_release/bpy.ops.html#overriding-context
    for area in bpy.context.screen.areas:
        if area.type != 'VIEW_3D':
            continue        
        for region in area.regions:
            if region.type != 'WINDOW':
                continue

            override = {'area': area, 'region': region, 'edit_object': bpy.context.edit_object}
            bpy.ops.uv.project_from_view(override, camera_bounds=False, correct_aspect=True, scale_to_bounds=True)

    bpy.ops.object.mode_set(mode=active_mode)

    # Transfer the created UV.
    for original_obj_i, obj_i in zip(original_obj.data.uv_layers.active.data, obj.data.uv_layers.active.data):
        original_obj_i.uv = obj_i.uv

    bpy.context.view_layer.objects.active = original_obj
    original_obj.select_set(True)

    bpy.data.meshes.remove(obj.data)
    # Something is missing! TODO: Find what is it. Tmp run purge.
    # Maybe the convert() has to do? Or dependencies?