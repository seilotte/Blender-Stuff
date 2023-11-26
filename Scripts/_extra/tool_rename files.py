import bpy
import os

# You need to run blender as an administrator.
# TODO: It would be nice to split the file name, instead of manually specifying the format.
# Or make only wich formats to exclude.

root_dir = r'target_directory'
file_format = '.png'
x = 30 # Start from which number?

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(file_format):
            new_name = str(x) + file_format

            file_path = os.path.join(subdir, file)
            new_file_path = os.path.join(subdir, new_name)
            #os.rename(current_file_name, new_file_name)
            os.rename(file_path, new_file_path)
            x += 1