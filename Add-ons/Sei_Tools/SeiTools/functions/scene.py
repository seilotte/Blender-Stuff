import bpy

def scene_assign_view_layer_name():
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'ARMATURE', 'LIGHT', 'CAMERA']:
            obj.data.name = obj.name

def scene_toggle_object_wireframe(context):
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            obj.show_wire = not obj.show_wire