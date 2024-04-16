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
- Add sei rig types code / button. 🗹
- Add rigify rig types support.

// arrow menu
- Sei collection -> Bone collection 🗹
- Bone collection -> Sei collection 🗹

## Bones in Collection
- Sync names with armature bone names.
- Invert list bone order.
- Add color sets. // To bones or to collections?

### Bone Tools
- Align to world coordinates operator.
- Assign bone shape operator. // Generate Rig does it...
- Flip bones operator. // Shortcut = Alt+f
'''

import bpy

from bpy.props import (BoolProperty, CollectionProperty, EnumProperty,
                        IntProperty, PointerProperty, StringProperty)
from bpy.types import Operator, Panel, UIList, Menu, PropertyGroup
from bl_ui.generic_ui_list import draw_ui_list

#bl_info = {
#    "name": "Sei Rig Tool",
#    "author": "Seilotte",
#    "version": (1, 0, 0),
#    "blender": (4, 0, 0),
#    "location": "3D View > Properties > Sei",
#    "description": "",
#    "tracker_url": "seilotte.github.io",    
#    "doc_url": "seilotte.github.io",
#    "category": "Animation",
#    }

########################### Custom Variables

# armature = mesh = object.data
# armature.collections.bones
# armature.sei_rig_variables.collections.bones

class SEI_RIG_variables_collection_item(PropertyGroup):
#    name: StringProperty()
    bone_shapes: EnumProperty(
        name = 'Bone Shapes',
        items = [
            # (identifier, name, description, icon, bumber)
            ('none', 'None', '', 'NONE', 1),
            (None),
            ('plane', 'Plane', '', 'CHECKBOX_DEHLT', 2), # MESH_PLANE:CHECKBOX_DEHLT
            ('cube', 'Cube', '', 'UGLYPACKAGE', 4), # MESH_CUBE:UGLYPACKAGE
            ('diamond', 'Diamond', '', 'KEYFRAME', 8),
            ('diamond_arrows', 'Diamond Arrows', '', 'ARROW_LEFTRIGHT', 16),
            (None),
            ('wireframe', 'Wireframe', '', 'MOD_WIREFRAME', 32), # BONE_DATA:MOD_WIREFRAME
        ]
    )

class SEI_RIG_variables_collection(PropertyGroup):
#    bones: CollectionProperty(type=PropertyGroup)
    bones: CollectionProperty(type=SEI_RIG_variables_collection_item)
    bones_index: IntProperty(default=0)

    rig_types: EnumProperty(
        name = 'Rig Types',
        items = [
            # (identifier, name, description, icon, number)
            ('none', 'None', '', 'NONE', 1),
            (None),
            ('tweak', 'Tweak', '', 'KEYFRAME', 2),
#            ('tentacle', 'Tentacle', '', 'CON_TRACKTO', 4),
#            ('chain', 'Chain', '', 'LINKED', 2),
#            ('tail', 'Tail', '', 'CON_TRACKTO', 4),
#            (None),
#            ('eye', 'Eye', '', 'HIDE_OFF', 8), # HIDE_OFF:CAMERA_STEREO
            (None),
            ('head', 'Head', '', 'USER', 16),
            ('spine', 'Spine', '', 'MOD_CLOTH', 32),
            ('arm', 'Arm', '','VIEW_PAN', 64),
            ('leg', 'Leg', '', 'MOD_DYNAMICPAINT', 128),
#            ('finger', 'Finger', '', 'THREE_DOTS', 256),
        ]
    )

    rotation_axis: EnumProperty(
        name = 'Rotation Axis',
#        default = 'z'
        items = [
            # (identifier, name, description, icon, number)
            ('x', 'X [Automatic]', ''),
            ('z', 'Z [Automatic]', ''),
        ]
    )

#    generate_tweaks: BoolProperty(default=True)
#    subdiv_tweaks: IntProperty(default=0, min=0, soft_max=6)

    spine_pivot_index: IntProperty(default=1, min=1, max=999)

#    helper_elbow_length: IntProperty(default=10, min=0, max=100, subtype='PERCENTAGE')
#    helper_knee_length: IntProperty(default=10, min=0, max=100, subtype='PERCENTAGE')

class SEI_RIG_variables(PropertyGroup):
    collections: CollectionProperty(type=SEI_RIG_variables_collection)
    collections_index: IntProperty(default=0)

    use_collection: BoolProperty(default=False, description='OFF: Uses selected bones; ON: Uses bones in the active sei collection')

    target_rig: PointerProperty(name='Armature', type=bpy.types.Armature)
    show_panel: BoolProperty(default=True)

#    generate_ui: BoolProperty(default=True, description='Generate a user interface script for bone collections')
    use_xyz_euler: BoolProperty(default=True, description='Apply rotation order "XYZ" to the object and bones - prone to Gimbal Lock')


########################### Global PT/OT Properties

class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}


########################### Operators
######### OT UI UL Add
class SEI_RIG_OT_collection_add(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_add'
    bl_label = 'Add Collection'

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables

        new_coll = vars.collections.add()
        new_coll.name = f'Col.{len(vars.collections) - 1:03}' if len(vars.collections) > 1 else 'Root'
        vars.collections_index = len(vars.collections) - 1

        return {'FINISHED'}

class SEI_RIG_OT_collection_bone_add(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_bone_add'
    bl_label = 'Add Collection Bone'

    @classmethod
    def poll(cls, context):
        return context.mode in ['POSE', 'EDIT_ARMATURE']

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        context_bones = context.selected_pose_bones if context.mode == 'POSE' else context.selected_editable_bones
        existing_bones = []

        for bone in context_bones:
            if sei_coll.bones.get(bone.name):
                existing_bones.append(bone.name)
                continue

            new_item = sei_coll.bones.add()
            new_item.name = bone.name
            sei_coll.bones_index = len(sei_coll.bones) - 1

        if existing_bones:
            self.report({'WARNING'}, f'Bone(s) already in "{sei_coll.name}": \n{", ".join(existing_bones)}')

        return {'FINISHED'}

######### OT UI UL Remove
def ui_item_remove(variable, index):
    if 0 <= index < len(variable):
        variable.remove(index)

    if index > 0:
        index -= 1

    return index

class SEI_RIG_OT_collection_remove(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_remove'
    bl_label = 'Remove Collection'

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables

        vars.collections_index = ui_item_remove(vars.collections, vars.collections_index)

        return {'FINISHED'}

class SEI_RIG_OT_collection_bone_remove(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_bone_remove'
    bl_label = 'Remove Collection Bone'

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        sei_coll.bones_index = ui_item_remove(sei_coll.bones, sei_coll.bones_index)

        return {'FINISHED'}

######### OT UI UL Move
def ui_item_move(variable, index, direction):
    if direction == 'UP':
        new_index = (index - 1) % len(variable)
        variable.move(index, new_index)
    elif direction == 'DOWN':
        new_index = (index + 1) % len(variable)
        variable.move(index, new_index)
    else: return index # Safety for an invalid direction.

    return new_index

class SEI_RIG_OT_collection_move(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_move'
    bl_label = 'Move Collection'

    direction: StringProperty(default='UP', options={'HIDDEN'})

#    @classmethod
#    def poll(cls, context):
#        return context.active_object.data.sei_rig_variables.collections

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables

        if vars.collections:
            vars.collections_index = ui_item_move(vars.collections, vars.collections_index, self.direction)

        return {'FINISHED'}

class SEI_RIG_OT_collection_bone_move(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_bone_move'
    bl_label = 'Move Collection Bone'

    direction: StringProperty(default='UP', options={'HIDDEN'})

#    @classmethod
#    def poll(cls, context):
#        vars = context.active_object.data.sei_rig_variables
#        return vars.collections[vars.collections_index].bones

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        if sei_coll.bones:
            sei_coll.bones_index = ui_item_move(sei_coll.bones, sei_coll.bones_index, self.direction)

        return {'FINISHED'}

######### OT UI Select/Deselect Bones in Collection
class SeiOperator_select_bones(SeiOperator):
    @classmethod
    def poll(cls, context):
        vars = context.active_object.data.sei_rig_variables
        return context.mode in ['POSE', 'EDIT_ARMATURE'] \
            and vars.collections and vars.collections[vars.collections_index].bones

    def select_bones(self, context, select):
        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        mesh = context.active_object.data
        context_bones = mesh.bones if context.mode == 'POSE' else mesh.edit_bones # pose.bones don't have ".select".

        for sei_bone in sei_coll.bones:
            bone = context_bones.get(sei_bone.name)

            if bone:
                bone.select = select
                if context.mode == 'EDIT_ARMATURE':
                    bone.select_head = bone.select_tail = select

        return {'FINISHED'}

class SEI_RIG_OT_collection_select_bones(SeiOperator_select_bones, Operator):
    bl_idname = 'sei_rig.collection_select_bones'
    bl_label = 'Select Bones in Collection'

    def execute(self, context):
        return self.select_bones(context, select=True)

class SEI_RIG_OT_collection_deselect_bones(SeiOperator_select_bones, Operator):
    bl_idname = 'sei_rig.collection_deselect_bones'
    bl_label = 'Deselect Bones in Collection'

    def execute(self, context):
        return self.select_bones(context, select=False)

######### OT MT Convert Collections.
class SEI_RIG_OT_collection_to_bone_collection(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_to_bone_collection'
    bl_label = 'Convert to Bone Collection'

    @classmethod
    def poll(cls, context):
        return context.active_object.data.sei_rig_variables.collections \
            and bpy.app.version >= (4, 0, 0)

    def execute(self, context):

        mesh = context.active_object.data
        vars = mesh.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        new_coll = mesh.collections.get(sei_coll.name) \
                    or mesh.collections.new(name=sei_coll.name)

        for sei_bone in sei_coll.bones:
            bone = mesh.bones.get(sei_bone.name)

            if bone:
                new_coll.assign(bone)

        self.report({'INFO'}, f'"Successfully converted or updated "{new_coll.name}".')
        # Refresh properties UI to display the changes (bone collections).
        [a.tag_redraw() for a in context.screen.areas if a.type=='PROPERTIES']

        return {'FINISHED'}

class SEI_RIG_OT_collection_from_bone_collection(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_from_bone_collection'
    bl_label = 'Convert from Bone Collection'

    @classmethod
    def poll(cls, context):
        return context.active_object.data.collections.active \
            and bpy.app.version >= (4, 0, 0)

    def execute(self, context):

        mesh = context.active_object.data
        vars = mesh.sei_rig_variables

        bone_coll = mesh.collections.active

        if not bone_coll:
            return {'FINISHED'}

        new_coll = vars.collections.get(bone_coll.name)

        if new_coll:
            vars.collections_index = vars.collections.find(new_coll.name)
        else:
            new_coll = vars.collections.add()
            new_coll.name = bone_coll.name
            vars.collections_index = len(vars.collections) - 1

        for bone in bone_coll.bones:
            if new_coll.bones.get(bone.name):
                continue

            new_bone = new_coll.bones.add()
            new_bone.name = bone.name
            vars.collections[vars.collections_index].bones_index = len(new_coll.bones) - 1

        self.report({'INFO'}, f'"Successfully converted or updated "{new_coll.name}".')

        return {'FINISHED'}

######### OT MT Delete All.
class SEI_RIG_OT_collections_clear(SeiOperator, Operator):
    bl_idname = 'sei_rig.collections_clear'
    bl_label = 'Delete All Collections'

    @classmethod
    def poll(cls, context):
        return context.active_object.data.sei_rig_variables.collections

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables

        vars.collections.clear()

        return {'FINISHED'}

class SEI_RIG_OT_collection_bones_clear(SeiOperator, Operator):
    bl_idname = 'sei_rig.collection_bones_clear'
    bl_label = 'Delete All Bones in Collection'

    @classmethod
    def poll(cls, context):
        vars = context.active_object.data.sei_rig_variables
        return vars.collections and vars.collections[vars.collections_index].bones

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        sei_coll.bones.clear()

        return {'FINISHED'}

######### OT MT Generate.
class SEI_RIG_OT_generate(SeiOperator, Operator):
    bl_idname = 'sei_rig.generate'
    bl_label = 'Generate Rig'

    @classmethod
    def poll(cls, context):
        vars = context.active_object.data.sei_rig_variables

        return vars.collections and vars.collections[0].bones \
            and vars.target_rig != context.active_object.data

    def execute(self, context):

        exec(bpy.data.texts['Text.001'].as_string(), {'self': self, 'context': context})

        return {'FINISHED'}

class SEI_RIG_OT_generate_arcsys(SeiOperator, Operator):
    bl_idname = 'sei_rig.generate_arcsys'
    bl_label = 'Generate Arc System Works Rig'

    @classmethod
    def poll(cls, context):
        vars = context.active_object.data.sei_rig_variables
        return vars.collections and vars.collections[0].bones \
            and vars.target_rig != context.active_object.data

    def execute(self, context):

#        bpy.ops.sei_rig.generate()
        self.report({'INFO'}, 'I am working on it... Send help.')

        return {'FINISHED'}


########################### UI Panel

class SEI_RIG_UL_collections(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)

        row.prop(item, 'name', text='', emboss=False,
                icon='OUTLINER_COLLECTION' if item.bones else 'COLLECTION_COLOR_03')
        row.prop(item, 'rig_types', icon_only=True)

class SEI_RIG_UL_collections_bones(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        icon = 'BONE_DATA'

        if data.rig_types == 'spine' and index == data.spine_pivot_index:
            icon = 'DOT'

        if not context.active_object.data.bones.get(item.name):
            icon = 'X' # X:ERROR
            row.alert = True

        row.prop(item, 'name', text='', emboss=False, icon=icon)
        row.prop(item, 'bone_shapes', icon_only=True)

class SEI_RIG_MT_collection_menu(Menu):
    bl_label = 'Sei Collection Specials'

    def draw(self, context):
        layout = self.layout

        layout.operator('sei_rig.collection_to_bone_collection', text='Convert to Bone Collection', icon='ARROW_LEFTRIGHT')
        layout.operator('sei_rig.collection_from_bone_collection', text='Convert from Bone Collection', icon='ARROW_LEFTRIGHT')

        layout.separator()

        layout.operator('sei_rig.collection_select_bones', text='Select Bones in Active Collection', icon='GROUP_BONE')
        layout.operator('sei_rig.collection_deselect_bones', text='Deselect Bones in Active Collection', icon='GROUP_BONE')

        layout.separator()

        layout.operator('sei_rig.collections_clear', text='Delete All Collections', icon='X')
        layout.operator('sei_rig.collection_bones_clear', text='Delete All Bones in Active Collection', icon='X')

class SEI_RIG_MT_generate_menu(Menu):
    bl_label = 'Generate Specials'

    def draw(self, context):
        layout = self.layout
        vars = context.object.data.sei_rig_variables

        layout.operator(
            'sei_rig.generate_arcsys',
            text = 'Re-Generate Rig [Arc System Works]' if vars.target_rig and vars.target_rig.get('sei_rig_id') else 'Generate Rig [Arc System Works]',
            icon = 'FILE_REFRESH' if vars.target_rig and vars.target_rig.get('sei_rig_id') else 'POSE_HLT'
        )


# Main panel - Rig Tools.
class SEI_RIG_PT_rig_tools(SeiPanel, Panel):
    bl_idname = 'SEI_RIG_PT_rig_tools'
    bl_label = ' Rig Tools'

    def draw_header(self, context):
        self.layout.operator('wm.url_open', text='', icon='HELP').url = 'seilotte.github.io'

    def draw(self, context):
        layout = self.layout

#        if bpy.app.version < (4, 0, 0):
#            layout.alert = True
#            layout.label(text='Expect issues; Use version 4.0.0 or higher.', icon='ERROR')
#            layout.alert = False

        # Since "bpy.types.Armatures.sei_rig_variables", we need to do this checks.
        # It is also convinient for operators.
        if not context.active_object:
            layout.label(text='No active object.', icon='ERROR') # INFO: ERROR
            return
        if context.active_object.type != 'ARMATURE':
            layout.label(text='No active armature.', icon='ERROR')
            return

        vars = context.object.data.sei_rig_variables

        # Main button (genearte) UI.
        col = layout.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False # No animation.

        row = col.row(align=True)
        row.operator(
            'sei_rig.generate',
            text = 'Re-Generate Rig' if vars.target_rig and vars.target_rig.get('sei_rig_id') else 'Generate Rig',
            icon = 'FILE_REFRESH' if vars.target_rig and vars.target_rig.get('sei_rig_id') else 'POSE_HLT'
        )
        row.menu('SEI_RIG_MT_generate_menu', text='', icon='DOWNARROW_HLT')

        col.prop(vars, 'target_rig', text='Target Rig', icon='ARMATURE_DATA')

        # Sei bone collections UI.
        layout.separator()
        layout.label(text='Bone Collections:', icon='SORT_ASC')

        row = layout.row()
        # Check the template "ui_list_simple.py" for more information.
        row.template_list('SEI_RIG_UL_collections', '', vars, 'collections', vars, 'collections_index')

        col = row.column(align=True)
        col.operator('sei_rig.collection_add', text='', icon='ADD')
        col.operator('sei_rig.collection_remove', text='', icon='REMOVE')

        col.separator()
        col.menu('SEI_RIG_MT_collection_menu', text='', icon='DOWNARROW_HLT')

        col.separator()
        col.operator('sei_rig.collection_move', text='', icon='TRIA_UP').direction = 'UP'
        col.operator('sei_rig.collection_move', text='', icon='TRIA_DOWN').direction = 'DOWN'

        if not vars.collections:
            layout.label(text='No Bone Collections', icon='INFO')
            return

        sub = layout.row(align=True)
        sub.operator('sei_rig.collection_select_bones', text='Select')
        sub.operator('sei_rig.collection_deselect_bones', text='Deselect')

        # Settings - Rig type UI.
        row = layout.row(align=True)
        row.prop(vars, 'show_panel', text='', emboss=False,
                icon='DOWNARROW_HLT' if vars.show_panel else 'RIGHTARROW')
        row.label(text='Settings:') # SETTINGS:PREFERENCES

        sei_active_coll = vars.collections[vars.collections_index]

        if vars.show_panel:
            row = layout.column()
            row = row.split(factor=0.01) # Left UI space.
            row.separator()

            col = row.column(align=True)
#            col.prop(vars, 'generate_ui', text='Generate UI')
            col.prop(vars, 'use_xyz_euler', text='XYZ Euler')

            col.separator()
            col.prop(sei_active_coll, 'rig_types')

#            col_box = col.box().grid_flow(columns=2)
            col_box = col.box().column(align=True)
            if sei_active_coll.rig_types == 'spine':
#                col_box.label(text='', icon='DOT')
                col_box.prop(sei_active_coll, 'spine_pivot_index', text='Pivot Index')
            elif sei_active_coll.rig_types in ['arm', 'leg']:
                col_box.prop(sei_active_coll, 'rotation_axis', text='Rotation Axis')

        # Bone collection items (bones) UI.
        layout.separator()
        layout.label(text='Bones in Collection:', icon='SORT_ASC')

        row = layout.row()
        # Check the template "ui_list_simple.py" for more information.
        row.template_list('SEI_RIG_UL_collections_bones', '', sei_active_coll, 'bones', sei_active_coll, 'bones_index')

        col = row.column(align=True)
        col.operator('sei_rig.collection_bone_move', text='', icon='TRIA_UP').direction = 'UP'
        col.operator('sei_rig.collection_bone_move', text='', icon='TRIA_DOWN').direction = 'DOWN'

        sub = layout.row(align=True)
        sub.operator('sei_rig.collection_bone_add', text='Assign')
        sub.operator('sei_rig.collection_bone_remove', text='Remove')


########################### Bone Tools
######### Operators
def bone_parent_or_unparent(self, context, parent):
    vars = context.active_object.data.sei_rig_variables
#    sei_coll = vars.collections[vars.collections_index]

    active_mode = context.active_object.mode
    bpy.ops.object.mode_set(mode='EDIT') # ".parent" only in edit mode.

    bones = context.selected_editable_bones
    active_bone = context.active_bone

#    if vars.use_collection and sei_coll.bones:
    if vars.use_collection:
        sei_coll = vars.collections[vars.collections_index]
        if not sei_coll.bones: pass

        bones = [context.active_object.data.edit_bones.get(i.name) for i in sei_coll.bones]
        active_bone = bones[0]

        if None in bones: # Check that bones exist.
            self.report({'WARNING'}, f'No bones were found and no action was taken.')
            return

    if active_bone.parent in bones:
        active_bone.parent = None

    for bone in bones:
        if parent:
            bone.parent = active_bone
            active_bone = bone if vars.use_collection else active_bone # Use "active_bone" as the previous bone.
        else:
            bone.parent = None

    bpy.ops.object.mode_set(mode=active_mode)

    return {'FINISHED'}

class SEI_RIG_OT_bone_parent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_parent'
    bl_label = 'Assign Parent'
    bl_description = 'Assign parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(self, context, parent=True)

class SEI_RIG_OT_bone_unparent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_unparent'
    bl_label = 'Remove Parent'
    bl_description = 'Remove parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(self, context, parent=False)

class SEI_RIG_OT_bone_select_children(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_select_children'
    bl_label = 'Select Children'
    bl_description = 'Select child bones'

    def execute(self, context):

        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        bone_children = context.active_bone.children_recursive

        if vars.use_collection and sei_coll.bones:
            sei_bone = sei_coll.bones[sei_coll.bones_index]

            if context.mode == 'EDIT_ARMATURE':
                bone_children = context.object.data.edit_bones[sei_bone.name].children_recursive
            else: # Pose.
                bone_children = context.object.data.bones[sei_bone.name].children_recursive

        for bone in bone_children:
            bone.select = True
            if context.mode == 'EDIT_ARMATURE':
                bone.select_head = bone.select_tail = True

        return {'FINISHED'}

class SEI_RIG_OT_bone_parent_tail_to_head(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_parent_tail_to_head'
    bl_label = 'Parent Tail to Head'
    bl_description = 'Move parent tail to child head'

    def execute(self, context):
        vars = context.active_object.data.sei_rig_variables
        sei_coll = vars.collections[vars.collections_index]

        active_mode = context.active_object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        bones = context.selected_editable_bones

        if vars.use_collection and sei_coll.bones:
            bones = [context.active_object.data.edit_bones.get(i.name) for i in sei_coll.bones]

            if None in bones: # Check that bones exist.
                self.report({'WARNING'}, f'No bones were found and no action was taken.')
                return

        for bone in bones:
            if bone.parent in bones:
                bone.parent.tail = bone.head

        bpy.ops.object.mode_set(mode=active_mode)

        return {'FINISHED'}


######### UI Panel
# Sub Panel - Bone Tools.
class SEI_RIG_PT_bone_tools(SeiPanel, Panel):
    bl_idname = 'SEI_RIG_PT_bone_tools'
    bl_label = 'Bone Tools'

    bl_parent_id = 'SEI_RIG_PT_rig_tools'
#    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode in ['EDIT_ARMATURE', 'POSE'] and context.active_bone

    def draw(self, context):
        layout = self.layout
        vars = context.active_object.data.sei_rig_variables

        if vars.collections and vars.collections[vars.collections_index].bones:
            layout.box().prop(vars, 'use_collection', text='Use Collection Order')
        else:
            layout.box().label(text='Using selected bones.', icon='INFO')

        row = layout.row(align=True)
        row.operator('sei_rig.bone_parent', text='Parent')
        row.operator('sei_rig.bone_unparent', text='Unparent')

        layout.operator('sei_rig.bone_select_children', text='Select Children', icon='GROUP_BONE')
        layout.operator('sei_rig.bone_parent_tail_to_head', text='Tail [parent] to Head', icon='BONE_DATA')

        layout.separator()

        col = layout.column_flow(columns=2)
        col.prop(context.active_bone, 'use_connect')
        col.prop(context.active_bone, 'use_deform')
        col.prop(context.object.data, 'show_axes', text='Axes')
        col.prop(context.object.data, 'show_names', text='Name')


#===========================

classes = [
    SEI_RIG_variables_collection_item, # Order matters since we are "nesting".
    SEI_RIG_variables_collection,
    SEI_RIG_variables,

    # Collections UL Operators.
    SEI_RIG_OT_collection_add,
    SEI_RIG_OT_collection_remove,
    SEI_RIG_OT_collection_move,

    SEI_RIG_OT_collection_select_bones,
    SEI_RIG_OT_collection_deselect_bones,

    # Collections MT Operators.
    SEI_RIG_OT_collection_to_bone_collection,
    SEI_RIG_OT_collection_from_bone_collection,
    SEI_RIG_OT_collections_clear,
    SEI_RIG_OT_collection_bones_clear,

    # Sei Bones UL Operators.
    SEI_RIG_OT_collection_bone_add,
    SEI_RIG_OT_collection_bone_remove,
    SEI_RIG_OT_collection_bone_move,

    # Generate MT Operators.
    SEI_RIG_OT_generate,
    SEI_RIG_OT_generate_arcsys,

    # Main UI.
    SEI_RIG_UL_collections,
    SEI_RIG_UL_collections_bones,
    SEI_RIG_MT_collection_menu,
    SEI_RIG_MT_generate_menu,
    SEI_RIG_PT_rig_tools,


    # Bone Tools UI; Sub Panel.
    SEI_RIG_OT_bone_parent,
    SEI_RIG_OT_bone_unparent,
    SEI_RIG_OT_bone_select_children,
    SEI_RIG_OT_bone_parent_tail_to_head,

    SEI_RIG_PT_bone_tools,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Armature.sei_rig_variables = PointerProperty(type=SEI_RIG_variables)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Armature.sei_rig_variables

if __name__ == "__main__": # debug; live edit
    register()