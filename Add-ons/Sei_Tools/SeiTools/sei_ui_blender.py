import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty

# Operator for fixing group inputs. (Blender UI)
class Sei_OT_FixGroupInputs(Operator):
    bl_label = "Fix Group Inputs"
    bl_idname = "sei.fix_group_inputs"
    bl_description = 'Toggle unused node sockets from "Group Inputs"'

    def execute(self, context):
        tree = context.space_data.node_tree
        if tree.nodes.active: # Check recursively until we find the tree.
            while tree.nodes.active != context.active_node:
                tree = tree.nodes.active.node_tree

                for node in tree.nodes:
                    if node.type != 'GROUP_INPUT': continue
#                    print(f'{node.name} + {node.type}')
                    if node.mute: continue

                    for socket in node.outputs:
                        socket.hide = True

#        self.report({'INFO'}, "Fixed group inputs.")
        return {'FINISHED'}

def sei_fixgroupinputs_button(self, context):
    self.layout.operator("sei.fix_group_inputs", text="Fix Group Inputs")


# Sei simplify. (Blender UI)
# TODO: Make functions.
# Original code, therefore the same license applies.
# https://github.com/Lateasusual/blender-collection-simplify/blob/master/__init__.py
class SEI_OT_SimplifyCollections(bpy.types.Operator):
    bl_label = "Simplify Collections"
    bl_idname = "sei.simplify_collections"
    bl_description = "Show/Hide modifiers in collection"

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    show_v_subsurf: BoolProperty('Show Subsurf in Viewport', default=False)
    show_r_subsurf: BoolProperty('Show Subsurf in Render', default=True)
    show_v_geonodes: BoolProperty('Show Geometry Nodes in Viewport', default=False)
    show_r_geonodes: BoolProperty('Show Geometry Nodes in Render', default=True)
    show_v_mask: BoolProperty('Show Mask in Viewport', default=False)
    show_r_mask: BoolProperty('Show Mask in Render', default=True)
    show_v_armature: BoolProperty('Show Armature in Viewport', default=False)
    show_r_armature: BoolProperty('Show Armature in Render', default=True)
    show_v_datatransfer: BoolProperty('Show Data Transfer in Viewport', default=False)
    show_r_datatransfer: BoolProperty('Show Data Transfer in Render', default=True)
    show_v_smooth: BoolProperty('Show Smooth Corrective in Viewport', default=False)
    show_r_smooth: BoolProperty('Show Smooth Corrective in Render', default=True)
    show_v_shrinkwrap: BoolProperty('Show Shrinkwrap in Viewport', default=False)
    show_r_shrinkwrap: BoolProperty('Show Shrinkwrap in Render', default=True)

    def execute(self, context):
        try:
            col = bpy.data.collections.get(context.scene.simplify_col)
            if not col:
                col = bpy.context.scene.collection
        except KeyError:
            self.report({'ERROR'}, f'Collection "{context.scene.simplify_col}" not found')

        for obj in col.objects:
            for mod in obj.modifiers:
                if mod.type == 'SUBSURF':
                    mod.show_viewport = self.show_v_subsurf
                    mod.show_render = self.show_r_subsurf
                elif mod.type == 'NODES':
                    mod.show_viewport = self.show_v_geonodes
                    mod.show_render = self.show_r_geonodes
                elif mod.type == 'MASK':
                    mod.show_viewport = self.show_v_mask
                    mod.show_render = self.show_r_mask
                elif mod.type == 'ARMATURE':
                    mod.show_viewport = self.show_v_armature
                    mod.show_render = self.show_r_armature
                elif mod.type == 'DATA_TRANSFER':
                    mod.show_viewport = self.show_v_datatransfer
                    mod.show_render = self.show_r_datatransfer
                elif mod.type == 'CORRECTIVE_SMOOTH':
                    mod.show_viewport = self.show_v_smooth
                    mod.show_render = self.show_r_smooth
                elif mod.type == 'SHRINKWRAP':
                    mod.show_viewport = self.show_v_shrinkwrap
                    mod.show_render = self.show_r_shrinkwrap

        return {'FINISHED'}

class SEI_PT_SimplifyCollections(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    bl_label = "Sei Simplify"
    bl_parent_id = "RENDER_PT_simplify"
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
        'BLENDER_WORKBENCH_NEXT'}

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
#        sei_vars = context.scene.sei_variables
        layout = self.layout
#        layout.use_property_split = True


        layout.prop_search(context.scene, "simplify_col", context.scene.collection, "children", text='Collection')

        col = layout.column()

        row = col.split(factor=0.4, align=True)
        row.label(text='Max Subsurf')
        row.prop(context.scene.render, "simplify_subdivision", icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Subsurf', icon='MOD_SUBSURF')
        row.prop(context.scene, 'sei_simplify_viewport_subsurf', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_subsurf', icon='RESTRICT_RENDER_OFF', icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Mask', icon='MOD_MASK')
        row.prop(context.scene, 'sei_simplify_viewport_mask', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_mask', icon='RESTRICT_RENDER_OFF', icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Geo Nodes', icon='GEOMETRY_NODES')
        row.prop(context.scene, 'sei_simplify_viewport_geonodes', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_geonodes', icon='RESTRICT_RENDER_OFF', icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Armature', icon='MOD_ARMATURE')
        row.prop(context.scene, 'sei_simplify_viewport_armature', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_armature', icon='RESTRICT_RENDER_OFF', icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Data Transfer', icon='MOD_DATA_TRANSFER')
        row.prop(context.scene, 'sei_simplify_viewport_datatransfer', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_datatransfer', icon='RESTRICT_RENDER_OFF', icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Smooth Corrective', icon='MOD_SMOOTH')
        row.prop(context.scene, 'sei_simplify_viewport_smooth', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_smooth', icon='RESTRICT_RENDER_OFF', icon_only=True)

        row = col.split(factor=0.4, align=True)
        row.label(text='Shrinkwrap', icon='MOD_SHRINKWRAP')
        row.prop(context.scene, 'sei_simplify_viewport_shrinkwrap', icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, 'sei_simplify_render_shrinkwrap', icon='RESTRICT_RENDER_OFF', icon_only=True)

        # Operator.
        op = layout.operator("sei.simplify_collections", text="Reload", icon='FILE_REFRESH')
        op.show_v_subsurf = context.scene.sei_simplify_viewport_subsurf
        op.show_r_subsurf = context.scene.sei_simplify_render_subsurf
        op.show_v_geonodes = context.scene.sei_simplify_viewport_geonodes
        op.show_r_geonodes = context.scene.sei_simplify_render_geonodes
        op.show_v_mask = context.scene.sei_simplify_viewport_mask
        op.show_r_mask = context.scene.sei_simplify_render_mask
        op.show_v_armature = context.scene.sei_simplify_viewport_armature
        op.show_r_armature = context.scene.sei_simplify_render_armature
        op.show_v_datatransfer = context.scene.sei_simplify_viewport_datatransfer
        op.show_r_datatransfer = context.scene.sei_simplify_render_datatransfer
        op.show_v_smooth = context.scene.sei_simplify_viewport_smooth
        op.show_r_smooth = context.scene.sei_simplify_render_smooth
        op.show_v_shrinkwrap = context.scene.sei_simplify_viewport_shrinkwrap
        op.show_r_shrinkwrap = context.scene.sei_simplify_render_shrinkwrap

# ===========================

classes = [
    Sei_OT_FixGroupInputs,
    SEI_PT_SimplifyCollections,
    SEI_OT_SimplifyCollections,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.NODE_PT_node_tree_interface_inputs.append(sei_fixgroupinputs_button)

    bpy.types.Scene.simplify_col = StringProperty('Collection')
    bpy.types.Scene.sei_simplify_viewport_subsurf = BoolProperty('Show subsurf in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_subsurf = BoolProperty('Show subsurf in render', default=True)
    bpy.types.Scene.sei_simplify_viewport_geonodes = BoolProperty('Show geonodes in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_geonodes = BoolProperty('Show geonodes in render', default=True)
    bpy.types.Scene.sei_simplify_viewport_mask = BoolProperty('Show mask in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_mask = BoolProperty('Show mask in render', default=True)
    bpy.types.Scene.sei_simplify_viewport_armature = BoolProperty('Show armature in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_armature = BoolProperty('Show armature in render', default=True)
    bpy.types.Scene.sei_simplify_viewport_datatransfer = BoolProperty('Show datatransfer in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_datatransfer = BoolProperty('Show datatransfer in render', default=True)
    bpy.types.Scene.sei_simplify_viewport_smooth = BoolProperty('Show smooth in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_smooth = BoolProperty('Show smooth in render', default=True)
    bpy.types.Scene.sei_simplify_viewport_shrinkwrap = BoolProperty('Show shrinkwrap in viewport', options=set())
    bpy.types.Scene.sei_simplify_render_shrinkwrap = BoolProperty('Show shrinkwrap in render', default=True)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.NODE_PT_node_tree_interface_inputs.remove(sei_fixgroupinputs_button)

    del bpy.types.Scene.simplify_col
    del bpy.types.Scene.sei_simplify_viewport_subsurf
    del bpy.types.Scene.sei_simplify_render_subsurf
    del bpy.types.Scene.sei_simplify_viewport_geonodes
    del bpy.types.Scene.sei_simplify_render_geonodes
    del bpy.types.Scene.sei_simplify_viewport_mask
    del bpy.types.Scene.sei_simplify_render_mask
    del bpy.types.Scene.sei_simplify_viewport_armature
    del bpy.types.Scene.sei_simplify_render_armature
    del bpy.types.Scene.sei_simplify_viewport_datatransfer
    del bpy.types.Scene.sei_simplify_render_datatransfer
    del bpy.types.Scene.sei_simplify_viewport_smooth
    del bpy.types.Scene.sei_simplify_render_smooth
    del bpy.types.Scene.sei_simplify_viewport_shrinkwrap
    del bpy.types.Scene.sei_simplify_render_shrinkwrap


if __name__ == '__main__':
    register()