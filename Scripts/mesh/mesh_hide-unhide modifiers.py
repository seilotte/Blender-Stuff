import bpy

# All objects or selected?
all = True

mod_name_key = "Gradient"
#mod_name_key = "Outline"


if all:
    objs = bpy.data.objects
else:
    objs = bpy.context.selected_objects

for obj in objs:
    if obj.type != 'MESH':
        continue

    if obj.modifiers:
        for mod in obj.modifiers:
            if mod_name_key in mod.name:
                if mod.show_viewport:
                    mod.show_viewport = False
                    mod.show_render = False
                else:
                    mod.show_viewport = True
                    mod.show_render = True