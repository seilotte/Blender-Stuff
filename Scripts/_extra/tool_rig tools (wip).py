'''
Sei Rig Tools
Done 🗹

# To Do
- Refactor/Organize the code.
- Arc System Works Rig 1 click button.
	- Body
	- Face
- Apex Legends Rig 1 click button.
	- Body
	- Face

## Bone Collections
- Add sei rig types code / button.
- Add rigify rig types support.

// arrow menu
- Sei collection -> Bone collection
- Bone collection -> Sei collection

## Bones in Collection
- Sync names with armature bone names.

### Bone Tools
- Assign bone shape operator.
- Flip bones operator. // Shortcut = Alt+f
'''

import bpy
from bpy.props import (StringProperty, IntProperty, PointerProperty, CollectionProperty,
                        EnumProperty, BoolProperty)
from bpy.types import Operator, Panel, UIList, Menu

#========= Custom Variables

class SEI_variables_rig_collection_item(bpy.types.PropertyGroup):
    name: StringProperty()
    bone_shapes: EnumProperty(
    name = 'Bone Shapes',
    items = [ # (identifier, name, description, icon, number)
        ('none', 'None', '', 'NONE', 1),
        (None),
        ('diamond', 'Diamond', '', 'KEYFRAME', 2),
        ('cube', 'Cube', '', 'UGLYPACKAGE', 4), # MESH_CUBE:UGLYPACKAGE
        ('plane', 'Plane', '', 'CHECKBOX_DEHLT', 8), # MESH_PLANE:CHECKBOX_DEHLT
        (None),
        ('wireframe', 'Wireframe', '', 'MOD_WIREFRAME', 16), # BONE_DATA:MOD_WIREFRAME
    ])

class SEI_variables_rig_collection(bpy.types.PropertyGroup):
#    item: CollectionProperty(type=bpy.types.PropertyGroup)
    item: CollectionProperty(type=SEI_variables_rig_collection_item)
    item_index: IntProperty(default=0)

    rig_types: EnumProperty(
    name = 'Rig Types',
    items = [ # (identifier, name, description, icon, number)
        ('none', 'None', '', 'NONE', 1),
        (None),
        ('chain', 'Chain', '', 'LINKED', 2),
        ('tail', 'Tail', '', 'CON_TRACKTO', 4),
        (None),
        ('eye', 'Eye', '', 'HIDE_OFF', 8), # HIDE_OFF:CAMERA_STEREO
        ('head', 'Head', '', 'USER', 16),
        (None),
        ('torso', 'Torso', '', 'MOD_CLOTH', 32),
        ('arm', 'Arm', '','VIEW_PAN', 64),
        ('finger', 'Finger', '', 'THREE_DOTS', 128),
        ('leg', 'Leg', '', 'MOD_DYNAMICPAINT', 256),
    ])

class SEI_variables_rig(bpy.types.PropertyGroup):
    collection: CollectionProperty(type=SEI_variables_rig_collection)
    collection_index: IntProperty(default=0)

    use_collection: BoolProperty(default=False, description='OFF: Uses selected bones. ; ON: Uses bones in active bone collection [sei]')


#========= Utility Functions

def ui_item_move(variable, index, direction):
    if direction == 'UP':
        new_index = (index - 1) % len(variable)
        variable.move(index, new_index)
    elif direction == 'DOWN':
        new_index = (index + 1) % len(variable)
        variable.move(index, new_index)
    else: return index # Safety for an invalid direction.

    return new_index

def ui_item_remove(variable, index):
    if 0 <= index < len(variable):
        variable.remove(index)

    if index > 0:
        index -= 1

    return index


def bone_get_context_bones(context):
    return context.selected_editable_bones if context.mode == 'EDIT_ARMATURE' else context.selected_pose_bones


#========= Global PT/OT Properties

class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei Rig'

class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}


#========= Operators
#=== OT UI Add
class SEI_OT_rig_collection_add(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_add'
    bl_label = "Add Collection"

    def execute(self, context):
        vars = context.object.data.sei_variables_rig

        new_item = vars.collection.add()
        new_item.name = f'Col.{len(vars.collection) - 1:03}'
        vars.collection_index = len(vars.collection) - 1

        return {'FINISHED'}

class SEI_OT_rig_collection_item_add(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_item_add'
    bl_label = "Add Collection Item"

    @classmethod
    def poll(cls, context):
        return context.mode in ['POSE', 'EDIT_ARMATURE']

    def execute(self, context):
        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]

        for bone in bone_get_context_bones(context):

            if bone.name in sei_collection.item:
                self.report({'WARNING'}, f'"{bone.name}" is already in the "{sei_collection.name}".')
                continue

            new_item = sei_collection.item.add()
            new_item.name = bone.name
            sei_collection.item_index = len(sei_collection.item) - 1

        return {'FINISHED'}

#=== OT UI Remove
class SEI_OT_rig_collection_remove(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_remove'
    bl_label = "Remove Collection"

    def execute(self, context):

        vars = context.object.data.sei_variables_rig
        vars.collection_index = ui_item_remove(vars.collection, vars.collection_index)

        return {'FINISHED'}

class SEI_OT_rig_collection_item_remove(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_item_remove'
    bl_label = "Remove Collection Item"

    def execute(self, context):

        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]
        sei_collection.item_index = ui_item_remove(sei_collection.item, sei_collection.item_index)

        return {'FINISHED'}

#=== OT UI Move
class SEI_OT_rig_collection_move(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_move'
    bl_label = "Move Collection"

    direction: StringProperty(default='UP', options={'HIDDEN'})
        
    def execute(self, context):
        vars = context.object.data.sei_variables_rig

        if vars.collection:
            vars.collection_index = ui_item_move(vars.collection, vars.collection_index, self.direction)

        return {'FINISHED'}

class SEI_OT_rig_collection_item_move(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_item_move'
    bl_label = "Move Collection Item"

    direction: StringProperty(default='UP', options={'HIDDEN'})

    def execute(self, context):
        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]

        if sei_collection.item:
            sei_collection.item_index = ui_item_move(sei_collection.item, sei_collection.item_index, self.direction)

        return {'FINISHED'}

#=== OT Select Bones [Collection]
class SeiOperator_select_bones(SeiOperator):
    @classmethod
    def poll(cls, context):
        vars = context.object.data.sei_variables_rig
        return vars.collection and vars.collection[vars.collection_index].item \
            and context.mode in ['POSE', 'EDIT_ARMATURE']

    def select_bones(self, context, select):
        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]

        mesh = context.object.data
        # Potentially slower but we assure the strings exist in the armature.
        for bone in set(mesh.edit_bones if context.mode == 'EDIT_ARMATURE' else mesh.bones): # pose.bones don't have ".select".
            if bone.name in sei_collection.item:
                bone.select = select
                if context.mode == 'EDIT_ARMATURE':
                    bone.select_head = bone.select_tail = select

        return {'FINISHED'}

class SEI_OT_rig_collection_select_bones(SeiOperator_select_bones, Operator):
    bl_idname = 'sei.rig_collection_select_bones'
    bl_label = "Select Bones in Collection"

    def execute(self, context):
        return self.select_bones(context, select=True)

class SEI_OT_rig_collection_deselect_bones(SeiOperator_select_bones, Operator):
    bl_idname = 'sei.rig_collection_deselect_bones'
    bl_label = "Deselect Bones in Collection"

    def execute(self, context):
        return self.select_bones(context, select=False)

#=== UI OT Delete All
class SEI_OT_rig_collection_delete_all(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_delete_all'
    bl_label = "Delete All Collections"

    @classmethod
    def poll(cls, context):
        return context.object.data.sei_variables_rig.collection

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        vars = context.object.data.sei_variables_rig

        vars.collection_index = 0
        for i in range(len(vars.collection)):
            vars.collection.remove(0)

        return {'FINISHED'}

class SEI_OT_rig_collection_item_delete_all(SeiOperator, Operator):
    bl_idname = 'sei.rig_collection_item_delete_all'
    bl_label = "Delete All Items"

    @classmethod
    def poll(cls, context):
        vars = context.object.data.sei_variables_rig
        return vars.collection \
            and vars.collection[vars.collection_index].item

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]

        sei_collection.item_index = 0
        for i in range(len(sei_collection.item)):
            sei_collection.item.remove(0)

        return {'FINISHED'}

#========= UI Panel

class SEI_UL_rig_collection(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, 'name', text='', emboss=False, translate=False,
                    icon='OUTLINER_COLLECTION' if item.item else 'COLLECTION_COLOR_03')
        layout.prop(item, 'rig_types', icon_only=True)

class SEI_UL_rig_collection_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, 'name', text='', emboss=False, translate=False, icon='BONE_DATA')
        layout.prop(item, 'bone_shapes', icon_only=True)


class SEI_MT_rig_collection_context_menu(Menu):
    bl_label = 'Sei Collection Specials'

    def draw(self, context):
        layout = self.layout

        layout.operator('sei.rig_collection_select_bones', text='Select Bones in Active Collection', icon='GROUP_BONE')
        layout.operator('sei.rig_collection_deselect_bones', text='Deselect Bones in Active Collection', icon='GROUP_BONE')

        layout.separator()

        layout.operator('sei.rig_collection_delete_all', text='Delete All Collections', icon='X')
        layout.operator('sei.rig_collection_item_delete_all', text='Delete All Bones in Active Collection', icon='X')

# Main panel.
class SEI_PT_rig_rig_tools(SeiPanel, Panel):
    bl_idname = 'SEI_PT_rig_rig_tools'
    bl_label = 'Rig Tools'

    def draw_header(self, context):
        self.layout.label(icon='BLENDER')

    def draw(self, context):
        layout = self.layout

        # Since "bpy.types.Armatures.sei_variables_rig", we need to do this checks.
        if context.object and context.object.type != 'ARMATURE':
            layout.label(text='No active armature.', icon='ERROR') # INFO:ERROR
        elif not context.object:
            layout.label(text='No active object.', icon='ERROR')
        else:
            vars = context.object.data.sei_variables_rig

            # Bone collections UI.
            layout.label(text='Bone Collections:')

            row = layout.row()
            row.template_list('SEI_UL_rig_collection', '', vars, 'collection', vars, 'collection_index')

            col = row.column(align=True)
            col.operator('sei.rig_collection_add', text='', icon='ADD')
            col.operator('sei.rig_collection_remove', text='', icon='REMOVE')

            col.separator()
            col.menu('SEI_MT_rig_collection_context_menu', text='', icon='DOWNARROW_HLT')

            if not vars.collection:
                layout.label(text='No Bone Collections.', icon='INFO')
            else:
                col.separator()

                col.operator('sei.rig_collection_move', icon='TRIA_UP', text='').direction = 'UP'
                col.operator('sei.rig_collection_move', icon='TRIA_DOWN', text='').direction = 'DOWN'

                row = layout.row()
                sub = row.row(align=True)
                sub.operator('sei.rig_collection_select_bones', text='Select')
                sub.operator('sei.rig_collection_deselect_bones', text='Deselect')

                # Bone collection items UI.
                layout.separator()
                layout.label(text='Bones in Collection:')

                sei_collection = vars.collection[vars.collection_index] # sei_active_collection

                row = layout.row()
                row.template_list('SEI_UL_rig_collection_items', '', sei_collection, 'item', sei_collection, 'item_index')

                col = row.column(align=True)
                col.operator('sei.rig_collection_item_move', icon='TRIA_UP', text='').direction = 'UP'
                col.operator('sei.rig_collection_item_move', icon='TRIA_DOWN', text='').direction = 'DOWN'

                row = layout.row()
                sub = row.row(align=True)
                sub.operator('sei.rig_collection_item_add', text='Assign')
                sub.operator('sei.rig_collection_item_remove', text='Remove')


###########################
#=== Bone Properites
###########################

def bone_parent_or_unparent(context, parent):
    vars = context.object.data.sei_variables_rig
    sei_collection = vars.collection[vars.collection_index]

    active_mode = context.object.mode
    bpy.ops.object.mode_set(mode='EDIT') # ".parent" only in edit_bones.

    if vars.use_collection and sei_collection.item:
        bones = [context.object.data.edit_bones[i.name] for i in sei_collection.item]

        for bone in bones[1:] if parent else bones:
            bone.parent = None

        if parent:
            bp = bones[0] # bp = bone_parent. "bp" since too much "bone, parent".
            if bp.parent in bones:
                bp.parent = None
            for bone in bones[1:]:
                bone.parent = bp
                bp = bone

    else: # It doesn't use the list order.
        for bone in context.selected_editable_bones:
            if parent and bone.name == context.active_bone.name:
                continue
            bone.parent = None

        if parent:
            if context.active_bone.parent in context.selected_editable_bones:
                context.active_bone.parent = None
            for bone in context.selected_editable_bones:
                bone.parent = context.active_bone

    bpy.ops.object.mode_set(mode=active_mode)

    return {'FINISHED'}

class SEI_OT_rig_bone_parent(SeiOperator, Operator):
    bl_idname = 'sei.rig_bone_parent'
    bl_label = 'Assign Parent'
    bl_description = 'Assign parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=True)

class SEI_OT_rig_bone_unparent(SeiOperator, Operator):
    bl_idname = 'sei.rig_bone_unparent'
    bl_label = 'Remove Parent'
    bl_description = 'Remove parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=False)


class SEI_OT_rig_bone_select_children(SeiOperator, Operator):
    bl_idname = 'sei.rig_bone_select_children'
    bl_label = 'Select Children'
    bl_description = 'Select child bones'

    def execute(self, context):
        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]

        bone_children = context.active_bone.children_recursive

        if vars.use_collection and sei_collection.item:
            sei_item = sei_collection.item[sei_collection.item_index]
            if context.mode == 'EDIT_ARMATURE':
                bone_children = context.object.data.edit_bones[sei_item.name].children_recursive
            else:
                bone_children = context.object.data.bones[sei_item.name].children_recursive

        for bone in bone_children:
            bone.select = True
            if context.mode == 'EDIT_ARMATURE':
                bone.select_head = bone.select_tail = True

        return {'FINISHED'}

class SEI_OT_rig_tail_to_head_parent(SeiOperator, Operator):
    bl_idname = 'sei.rig_bone_tail_to_head_parent'
    bl_label = 'Tail to Head - Parent'
    bl_description = 'Move parent tail to child head'

    def execute(self, context):
        vars = context.object.data.sei_variables_rig
        sei_collection = vars.collection[vars.collection_index]

        active_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        bones = context.selected_editable_bones

        if vars.use_collection and sei_collection.item:
            bones = [context.object.data.edit_bones[i.name] for i in sei_collection.item]

        for bone in bones:
            if bone.parent in bones:
                bone.parent.tail = bone.head

        bpy.ops.object.mode_set(mode=active_mode)

        return {'FINISHED'}


class SEI_PT_rig_bone_tools(SeiPanel, Panel):
    bl_idnamae = 'SEI_PT_rig_bone_tools'
    bl_label = 'Bone Tools'
    bl_parent_id = 'SEI_PT_rig_rig_tools'

    @classmethod
    def poll(cls, context):
        return context.mode in ['EDIT_ARMATURE', 'POSE'] and context.active_bone

    def draw(self, context):
        layout = self.layout
        vars = context.object.data.sei_variables_rig

        if vars.collection and vars.collection[vars.collection_index].item:
            layout.box().prop(vars, 'use_collection', text='Use Collection')
        else:
            layout.box().label(text='Using selected bones.', icon='INFO')

        row = layout.row(align=True)
        row.operator('sei.rig_bone_parent', text='Parent')
        row.operator('sei.rig_bone_unparent', text='Unparent')

        layout.operator('sei.rig_bone_select_children', text='Select Children', icon='GROUP_BONE')
        layout.operator('sei.rig_bone_tail_to_head_parent', text='Tail [parent] to Head', icon='BONE_DATA')

        layout.separator()

        row = layout.row(align=True)
        row.prop(context.active_bone, 'use_connect', text='Connected')
        row.prop(context.active_bone, 'use_deform', text='Deform')
        row.prop(context.object.data, 'show_axes', text='Axes')

#===========================

classes = [
    SEI_variables_rig_collection_item, # Order matters since we are "nesting".
    SEI_variables_rig_collection,
    SEI_variables_rig,

    SEI_OT_rig_collection_add,
    SEI_OT_rig_collection_remove,
    SEI_OT_rig_collection_move,

    SEI_OT_rig_collection_select_bones,
    SEI_OT_rig_collection_deselect_bones,
    SEI_OT_rig_collection_delete_all,
    SEI_OT_rig_collection_item_delete_all,


    SEI_OT_rig_collection_item_add,
    SEI_OT_rig_collection_item_remove,
    SEI_OT_rig_collection_item_move,

    SEI_UL_rig_collection,
    SEI_UL_rig_collection_items,
    SEI_MT_rig_collection_context_menu,
    SEI_PT_rig_rig_tools,



    SEI_OT_rig_bone_parent,
    SEI_OT_rig_bone_unparent,
    SEI_OT_rig_bone_select_children,
    SEI_OT_rig_tail_to_head_parent,

    SEI_PT_rig_bone_tools,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Armature.sei_variables_rig = PointerProperty(type=SEI_variables_rig)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Armature.sei_variables_rig

if __name__ == "__main__": # debug
    register()