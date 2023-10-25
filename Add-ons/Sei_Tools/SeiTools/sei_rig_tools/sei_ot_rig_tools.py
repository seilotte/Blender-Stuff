import bpy
import os
from bpy.types import Operator

script_dir = os.path.dirname(os.path.realpath(__file__))

# Global panel OT properties.
class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

#Make all armatures, stick and in front.
class SEI_OT_StickInFront(SeiOperator, Operator):
    bl_label = 'Armatures Stick, In Front'
    bl_idname = 'sei.stick_in_front'
    bl_description = 'Make selected armatures display as "Stick" and "In Front"'
    
    def execute(self, context):

        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                obj.data.display_type = 'STICK'
                obj.show_in_front = True
                obj.display_type = 'WIRE'

        return{'FINISHED'}

# Initialize rigify.
class SEI_OT_InitiateRigify(SeiOperator, Operator):
    bl_label = 'Initiate Rigify'
    bl_idname = 'sei.initiate_rigify'
    bl_description = 'Set-up rigify settings in the selected armature'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\initiate_rigify.py')

        return{'FINISHED'}

# Assign armature.
class SEI_OT_AssignArmature(SeiOperator, Operator):
    bl_label = 'Assign Armature'
    bl_idname = 'sei.assign_armature'
    bl_description = 'Assign indicated armature to selected meshes'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\assign_armature.py')

        return{'FINISHED'}

# =========================== Bone Properties

# Select bone childrens.
class SEI_OT_SelectChildren(SeiOperator, Operator):
    bl_label = 'Select Bone Children'
    bl_idname = 'sei.select_children'
    bl_description = 'Select recursive bone childrens'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\bone_select_children.py')

        return{'FINISHED'}

# Parent bones.
class SEI_OT_ParentBones(SeiOperator, Operator):
    bl_label = 'Parent Bones'
    bl_idname = 'sei.bone_parent'
    bl_description = 'Parent bones to the last selected bone'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\bone_parent.py')

        return{'FINISHED'}

# Bone tail to head.
class SEI_OT_TailtoHead(SeiOperator, Operator):
    bl_label = 'Bones Tail to Head'
    bl_idname = 'sei.tail_to_head'
    bl_description = 'Tail to head on selected bones'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\bone_tail_to_head.py')

        return{'FINISHED'}


# Assign rig type.
class SEI_OT_AssignRigType(bpy.types.Operator):
    bl_label = 'Assign Rig Type'
    bl_idname = 'sei.assign_rig_type'

    #If it's not an armature or in pose mode, disable.
    @classmethod
    def poll(self, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE' \
            and context.view_layer.objects.active.mode == 'POSE'

    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\bone_assign_rigtype.py')

        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
                break

        return {'FINISHED'}

# Clear rig type.
class SEI_OT_ClearRigType(bpy.types.Operator):
    bl_label = 'Clear Rig Type'
    bl_idname = 'sei.clear_rig_type'

    #If it's not an armature or in pose mode, disable.
    @classmethod
    def poll(self, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE' \
            and context.view_layer.objects.active.mode == 'POSE'

    def execute(self, context):

        bones = context.selected_pose_bones
        for bone in bones:
            bpy.context.object.pose.bones[bone.name].rigify_type = ''
            bone.bone_group = None
        
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
                break

        return {'FINISHED'}

# Add rotation constraint.
class SEI_OT_AddRotationConstraint(SeiOperator, Operator):
    bl_label = 'Add Rotation Constraint'
    bl_idname = 'sei.add_rotation_constraint'
    bl_description = 'Add a rotation constraint to the selected bones'
    
    def execute(self, context):

        bpy.ops.script.python_file_run(filepath = script_dir + '\\add_rotation_constraint.py')

        return{'FINISHED'}

# ===========================

classes = [
    SEI_OT_StickInFront,
    SEI_OT_InitiateRigify,
    SEI_OT_AssignArmature,
    # Bones.
    SEI_OT_SelectChildren,
    SEI_OT_ParentBones,
    SEI_OT_TailtoHead,
    SEI_OT_AssignRigType,
    SEI_OT_ClearRigType,
    SEI_OT_AddRotationConstraint,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)