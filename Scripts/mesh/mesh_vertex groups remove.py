import bpy

lst = [
    '---',
    'G_head_root',
    'G_Head_def',
    '_VertexAlpha',
]

for obj in bpy.context.selected_objects:
    for i in obj.vertex_groups:
        if i.name not in lst:
            obj.vertex_groups.remove(i)