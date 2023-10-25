import bpy
import os
from bpy.types import Operator

#script_dir = os.path.dirname(os.path.realpath(__file__))

# Global panel OT properties.
class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

def add_modifier(mod_name, mod_type):
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH' and mod_name not in obj.modifiers:
            obj.modifiers.new(mod_name, mod_type)

def remove_modifier(mod_type):
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            mods = [i for i in obj.modifiers if i.type == mod_type]
            if mods:
                obj.modifiers.remove(mods[-1])

# ===========================

# Add/Remove armature modifier.
class SEI_OT_AddArmature(SeiOperator, Operator):
    bl_label = 'Add Armature Modifier'
    bl_idname = 'sei.add_armature_modifier'
    bl_description = 'Adds armature modifier(s) to the selected meshes'
    
    def execute(self, context):
        add_modifier('Armature', 'ARMATURE')
        return {'FINISHED'}

class SEI_OT_RemoveArmature(SeiOperator, Operator):
    bl_label = 'Remove Armature Modifier'
    bl_idname = 'sei.remove_armature_modifier'
    bl_description = 'Removes armature modifier(s) to the selected meshes'
    
    def execute(self, context):
        remove_modifier('ARMATURE')
        return {'FINISHED'}


# Add/Remove mask modifier.
class SEI_OT_AddMask(SeiOperator, Operator):
    bl_label = 'Add Mask Modifier'
    bl_idname = 'sei.add_mask_modifier'
    bl_description = 'Adds mask modifier(s) to the selected meshes'
    
    def execute(self, context):
        add_modifier('', 'MASK')
        return {'FINISHED'}

class SEI_OT_RemoveMask(SeiOperator, Operator):
    bl_label = 'Remove Mask Modifier'
    bl_idname = 'sei.remove_mask_modifier'
    bl_description = 'Removes mask modifier(s) to the selected meshes'
    
    def execute(self, context):
        remove_modifier('MASK')
        return {'FINISHED'}


# Add/Remove smooth corrective modifier.
class SEI_OT_AddSmoothC(SeiOperator, Operator):
    bl_label = 'Add Smooth Corrective Modifier'
    bl_idname = 'sei.add_smoothc_modifier'
    bl_description = 'Adds smooth corrective modifier(s) to the selected meshes'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        add_modifier('', 'CORRECTIVE_SMOOTH')
        return {'FINISHED'}

class SEI_OT_RemoveSmoothC(SeiOperator, Operator):
    bl_label = 'Remove Smooth Corrective Modifier'
    bl_idname = 'sei.remove_smoothc_modifier'
    bl_description = 'Removes smooth corrective modifier(s) to the selected meshes'
    
    def execute(self, context):
        remove_modifier('CORRECTIVE_SMOOTH')
        return {'FINISHED'}


# Add/Remove subsurf modifier.
class SEI_OT_AddSubsurf(SeiOperator, Operator):
    bl_label = 'Add Subdivision Surface Modifier'
    bl_idname = 'sei.add_subsurf_modifier'
    bl_description = 'Adds subdivision surface modifier(s) to the selected meshes'
    
    def execute(self, context):
        vars = context.scene.sei_variables
        all = context.selected_objects

        subsurf_name = 'Subsurf'
        for obj in all:
            if obj.type != 'MESH':
                continue

            if not subsurf_name in obj.modifiers:
                obj.modifiers.new(subsurf_name, 'SUBSURF')

            obj.modifiers[subsurf_name].levels = vars.subsurf_viewport
            obj.modifiers[subsurf_name].render_levels = vars.subsurf_render

        return {'FINISHED'}

class SEI_OT_RemoveSubsurf(SeiOperator, Operator):
    bl_label = 'Remove Subdivision Surface Modifier'
    bl_idname = 'sei.remove_subsurf_modifier'
    bl_description = 'Removes subdivision surface modifier(s) to the selected meshes'
    
    def execute(self, context):
        remove_modifier('SUBSURF')
        return {'FINISHED'}

# ===========================

classes = [
    SEI_OT_AddArmature,
    SEI_OT_RemoveArmature,
    SEI_OT_AddMask,
    SEI_OT_RemoveMask,
    SEI_OT_AddSmoothC,
    SEI_OT_RemoveSmoothC,
    SEI_OT_AddSubsurf,
    SEI_OT_RemoveSubsurf,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)