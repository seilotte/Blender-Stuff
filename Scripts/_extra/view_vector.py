import bpy
import mathutils

# Get the window manager
wm = bpy.context.window_manager

# Get the desired window by index (0 is the default)
desired_window = wm.windows[0]

# Check if the active area is a 3D Viewport
for area in desired_window.screen.areas:
    if area.type == 'VIEW_3D':
        # Get the 3D Viewport space data
        space = area.spaces.active

        # Get the view matrix of the 3D viewport
        view_matrix = space.region_3d.view_matrix

        # Get the View_3d vector from the view matrix
        view_vector = mathutils.Vector((-view_matrix[2][0], -view_matrix[2][1], -view_matrix[2][2]))

        # Normalize the vector
        view_vector.normalize()

        # Print the View_3d vector
        print("View_3d vector:", view_vector)
        break
else:
    print("No active 3D viewport found.")
