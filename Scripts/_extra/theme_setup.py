'''
Developed in Blender 5.0.0.

WARNING:
    This modifies the user settings!
    There is not an undo option.
    If things go wrong "Reset" the theme.
'''

import bpy
import mathutils

from bpy import context
#from mathutils import Color as c

DEBUG = False

TEXT_SIZE = 14
COLOURS = [
    ('FFFFFF', 'FFFFFF'), # todo -> todo; template

    ('4772B3', 'CC5390'), # blue -> main pink; main0
    ('71A8FF', 'CC5390'), # blue -> main pink; main1

    ('E19658', 'E1A883'), # todo -> desaturated orange; icon_object
    ('00D4A3', '66CCB4'), # todo -> desaturated green; icon_mesh
    ('74A2FF', 'B3D1FF'), # todo -> desaturated blue; icon_modifier
    ('CC6670', 'CC8F8F'), # todo -> desaturated red; icon_shading

    ('FF8500', 'FFFF55'), # todo -> desaturated yellow; vert_gp
    ('FF7A00', 'FFFF55'), # todo -> desaturated yellow; vert
    ('FF9900', 'FFFF55'), # todo -> desaturated yellow; edge
    ('FFD800', 'FFFF55'), # todo -> desaturated yellow; edge_selection
    ('FFA300', 'FFFF55'), # todo -> desaturated yellow; face
    ('FFB700', 'FFFF55'), # todo -> desaturated yellow; face_selection

    ('ED5700', 'E6CFD4'), # todo -> white pink; obj_selected
    ('FFA028', 'CC5390'), # todo -> main pink; obj_active

    ('E96A00', 'B08B90'), # orange -> white pink; obj_selected_outliner
    ('FFAF29', 'F5DFDF'), # light orange -> main pink; obj_active_outliner
    ('1D314D', '595052'), # todo -> todo; selected_highlight_outliner
    ('334D80', 'CC5390'), # todo -> main pink; active_highlight_outliner

    ('#FF8F0D', 'E6CFD4'), # orange -> white pink; strip_selected_vsequencer
]



def main_fn():

    def print_fn(string: str):
        if DEBUG: print(string)

    def compare_dot(a: tuple, b: tuple, eps: float = 0.001) -> bool:
        return sum((a[i] - b[i]) ** 2 for i in (0, 1, 2)) < eps ** 2

    def hex_to_rgba(hex_color: str):
        '''
        Convert HEX color to RGB or RGBA, based on length of HEX code.
        https://projects.blender.org/nickberckley/theme_updater/src/branch/main/source/functions.py
        '''
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 6:  # RGB
            r, g, b = [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]
            return (r, g, b)

        elif len(hex_color) == 8:  # RGBA
            r, g, b, a = [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4, 6)]
            return (r, g, b, a)

        else:
            raise ValueError(f'Invalid hex color length: {hex_color}')



    # Set "Sei Theme".
#    bpy.ops.wm.interface_theme_preset_add(name = 'Sei Theme')
#    context.preferences.themes[0].filepath = 'Sei Theme'



    # Set points size.
    style = context.preferences.ui_styles[0]

    style.panel_title.points = TEXT_SIZE
    style.widget.points = TEXT_SIZE
    style.tooltip.points = TEXT_SIZE

#    for attr_name in dir(style):
#        attr_obj = getattr(style, attr_name)
#        if hasattr(attr_obj, 'points'):
#            setattr(attr_obj, 'points', POINTS_SIZE)



    # Set theme colours.
    def replace_colours_recursive(obj: object, colours: tuple, depth: int = 0):
        if depth > 3: # stop recursion
            return

        for attr_name in dir(obj):
            if attr_name.startswith('__'):
                continue

            value = getattr(obj, attr_name) # attr_obj

            if isinstance(value, mathutils.Color) \
            and compare_dot(value[:], colours[0]): # source

                print_fn(f'    {depth:<2} {attr_name:<20} {tuple(round(v, 3) for v in value[:])} -> {colours[1]}')

                value[:] = colours[1] # target

            elif isinstance(value, bpy.types.bpy_prop_array) \
            and len(value) == 4 \
            and all(isinstance(v, float) for v in value) \
            and compare_dot(value[:3], colours[0]): # 4 float array; type(attribute)

                print_fn(f'    {depth:<2} {attr_name:<20} {tuple(round(v, 3) for v in value[:])} -> {colours[1]}')

                value[0] = colours[1][0]
                value[1] = colours[1][1]
                value[2] = colours[1][2]

            elif isinstance(value, object):
                replace_colours_recursive(value, colours, depth + 1)

        return None

    def replace_colours(theme: bpy.types.Theme, colours: tuple):
        for attr_name in dir(theme):
            if attr_name.startswith('__'):
                continue

            attr_obj = getattr(theme, attr_name)

            if not hasattr(attr_obj, '__class__'):
                continue

            if not attr_obj.__class__.__name__.startswith('Theme'):
                continue

            print_fn(f'Checking {attr_obj.__class__.__name__}...')
            replace_colours_recursive(attr_obj, colours)

        return None

    theme = context.preferences.themes[0]

    # TODO: Loop colours instead of attributes?
    for colours in COLOURS:
        colours = (
            hex_to_rgba(colours[0]), hex_to_rgba(colours[1])
        )

        replace_colours(theme, colours)



    # Save "Sei Theme".
#    bpy.ops.wm.interface_theme_preset_save()
    print_fn('Finished "Sei Theme".')

    return None

# ========

if __name__ == '__main__':
    main_fn()
