import bpy

context = bpy.context

vcol_name = "Col"
vcol_channel = 3 # Alpha channel.

for obj in context.selected_objects:
    if obj.type != 'MESH': continue

    new_vcol_name = f'{vcol_name}[{vcol_channel}]'
    if new_vcol_name not in obj.data.attributes:
        obj.data.attributes.new(name=new_vcol_name, domain='CORNER', type='BYTE_COLOR')

    new_vcol = obj.data.attributes[new_vcol_name]
    vcol = obj.data.attributes[vcol_name]

    for face in obj.data.polygons:
        for loop in face.loop_indices:
            channel_value = vcol.data[loop].color[vcol_channel]
            new_vcol.data[loop].color = (channel_value, channel_value, channel_value, channel_value)