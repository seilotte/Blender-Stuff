import bpy

#def hide_show_objects(obj_name1, obj_name2):
#    obj1 = bpy.data.objects.get(obj_name1)
#    obj2 = bpy.data.objects.get(obj_name2)

#    if obj1 and obj2:
#        switch = obj1.hide_viewport
#        obj1.hide_viewport = obj2.hide_viewport
#        obj2.hide_viewport = switch

#hide_show_objects('tsu_body', 'tsu.001')

def switch_visibility(hidden_obj, visible_obj):
    hidden_obj.hide_viewport = False
    hidden_obj.hide_render = False
    visible_obj.hide_viewport = True
    visible_obj.hide_render = True

def hide_show_objects(obj_name1, obj_name2):
    obj1 = bpy.data.objects.get(obj_name1)
    obj2 = bpy.data.objects.get(obj_name2)

    if obj1 and obj2:
        # Object 1 is hidden, Object 2 is visible
        if obj1.hide_viewport and not obj2.hide_viewport:
            switch_visibility(obj1, obj2)
        # Object 1 is visible, Object 2 is hidden
        elif not obj1.hide_viewport and obj2.hide_viewport:
            switch_visibility(obj2, obj1)
        # Both objects have the same hide state, toggle the visibility of Object 2
        else:
            obj2.hide_viewport = not obj2.hide_viewport

hide_show_objects('tsu_body', 'tsu.001')