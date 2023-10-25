import bpy
import os
from bpy.types import Operator

script_dir = os.path.dirname(os.path.realpath(__file__))

# Global panel OT properties.
class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

# Assign armature.
class SEI_OT_AssignImageSpace(SeiOperator, Operator):
    bl_label = 'Assign Image Space'
    bl_idname = 'sei.assign_image_space'
    bl_description = 'Assign image space to the selected images'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\sei_assign_image_space.py')

        return {'FINISHED'}

# ===========================

classes = [
    SEI_OT_AssignImageSpace,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)