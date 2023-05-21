import bpy

for obj in bpy.context.selected_objects:
    del obj['mesh_data_transfer_object'] # Object properties.
#    del obj.data['property_example'] # Object data properties.