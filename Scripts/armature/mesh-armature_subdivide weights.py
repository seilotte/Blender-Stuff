import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty

bl_info = {
    "name": "Subdivide Weights",
    "author": "Seilotte, Kyle",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "Weights > Subdivide Weights | Edit/Pose mode RMB > Subdivide Weights",
    "description": "Subdivide bone with its weight.",
#    "tracker_url": "",
#    "doc_url": "",
    "category": "Workflow",
    }

class ARMATURE_OT_subdivide_weights(bpy.types.Operator):
    bl_idname = 'armature.subdivide_weights'
    bl_label = 'Subdivide Weights'
    bl_description = 'Subdivide the weights of the first selected bone'
#    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    target_object: StringProperty(name='Target Object:', description='Object in which to get or create vertex groups.')
    scale: FloatProperty(default=3.0, soft_min=0.0) # 0 - inf (in scale of bone)
    overlap: FloatProperty(default=2.0, soft_min=0.0)
    number_cuts: IntProperty(default=1, soft_min=1, soft_max=10) # hard_min is bugged

    @classmethod
    def poll(cls, context):
        if context.mode in 'PAINT_WEIGHT' and context.selected_pose_bones:
            return True
        elif context.mode in ['EDIT_ARMATURE', 'POSE'] and context.active_bone:
            return True

    def execute(self, context):
        # Subdivide bone.
        obj = context.object
        bone = context.active_bone

        if context.mode in ['EDIT_ARMATURE', 'POSE'] and bone:
            active_mode = obj.mode
            bpy.ops.object.mode_set(mode='EDIT')

            bone = obj.data.edit_bones[bone.name]

            # TODO: Find a faster solution.
            for ebone in obj.data.edit_bones:
                ebone.select = \
                ebone.select_head = \
                ebone.select_tail = False

            for i in range(self.number_cuts):
                if i == 0:
                    bone.select = \
                    bone.select_head = \
                    bone.select_tail = True

                    vec = bone.vector
                    parent = bone

                    bone.length = bone.length / self.number_cuts

                    continue

#                new_bone = obj.data.edit_bones.new(bone.name)
                new_bone = obj.data.edit_bones.new(
                    f'{bone.name}.{self.number_cuts - i:03}' # Why blender?
                )

                new_bone.select = \
                new_bone.select_head = \
                new_bone.select_tail = True

                new_bone.use_connect = True
                new_bone.use_deform = bone.use_deform

                new_bone.head = bone.head + (vec / self.number_cuts) * i
                new_bone.tail = bone.head + (vec / self.number_cuts) * (i + 1)
                new_bone.roll = bone.roll

                new_bone.parent = parent
                parent = new_bone

            bpy.ops.object.mode_set(mode=active_mode)
            del ebone, vec

        # Subdivide weights.
        obj = bpy.data.objects.get(self.target_object) or context.object
        bones = context.selected_editable_bones if context.mode == 'EDIT_ARMATURE' else \
                context.selected_pose_bones

        if obj is None \
        or bones is None \
        or obj.type != 'MESH' \
        or obj.vertex_groups.get(bones[0].name) is None:
#            self.report({'WARNING'}, 'Skipping weights. Data incomplete (object is mesh, selected bones or vertex group).')
            return {'FINISHED'}

        def half_power(x=0.0, size=0.0, offset=0.0, side=''):
            if side == 'left' and x > offset:
                return 1.0
            elif side == 'right' and x < offset:
                return 1.0
            else:
                return max( -(size * (x-offset)) * (size * (x-offset)) + 1.0 , 0.0)

        for bone in reversed(bones): # Order matters, end -> start.
            if context.mode == 'EDIT_ARMATURE':
                org_bone = bones[0]

                org_head = org_bone.head
                org_tail = org_bone.tail
                org_vec = org_bone.vector

                b = bone
                b_head = b.head
                b_tail = b.tail

            else: # PAINT_WEIGHT, POSE
                org_bone = bones[0].bone

                org_head = org_bone.head_local
                org_tail = org_bone.tail_local
                org_vec = org_bone.vector

                b = bone.bone
                b_head = b.head_local
                b_tail = b.tail_local

            org_vgroup = obj.vertex_groups[bones[0].name]
            new_vgroup = obj.vertex_groups.get(bone.name) or obj.vertex_groups.new(name=bone.name)

            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group != org_vgroup.index:
                        continue

                    # P = (dot(A, B) / dot(B, B)) * B
                    projection = (org_vec.dot(v.co - org_head) / org_vec.dot(org_vec)) * org_vec

                    # Get bounds.
                    bound_left = half_power(
                        projection.length - (org_head - b_head).length, # fraction - head
                        1.0 / (b.length * self.scale + self.overlap),
                        self.overlap, # offset
                        'left'
                    )
                    bound_right = half_power(
                        projection.length - (org_head - b_tail).length, # fraction - tail
                        1.0 / (b.length * self.scale + self.overlap),
                        -self.overlap, # -offset
                        'right'
                    )

                    # Assign weight.
                    if bone == bones[0]: # end; reversed()
                        weight = bound_right
                    elif bone == bones[-1]: # start
                        weight = bound_left
                    else:
                        weight = bound_left * bound_right

                    new_vgroup.add([v.index], weight * g.weight, 'REPLACE')

            # Clean weights.
            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group == new_vgroup.index and g.weight <= 0.0:
                        new_vgroup.remove([v.index])

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False # No animation.

        if context.mode in ['EDIT_ARMATURE', 'POSE']:
            layout.prop(self, 'number_cuts')
            layout.separator()
            layout.prop_search(self, 'target_object', bpy.data, 'objects')

        if self.target_object:
            col = layout.column(align=True)
            col.prop(self, 'scale')
            col.prop(self, 'overlap')

def ARMATURE_subdivide_weights_draw(self, context):
    self.layout.operator('armature.subdivide_weights')

#===========================

def register():
    bpy.utils.register_class(ARMATURE_OT_subdivide_weights)

#    bpy.types.VIEW3D_MT_edit_armature.append(ARMATURE_subdivide_weights_draw) # Edit mode > Armature
#    bpy.types.VIEW3D_MT_pose.append(ARMATURE_subdivide_weights_draw) # Pose mode > Pose
    bpy.types.VIEW3D_MT_armature_context_menu.prepend(ARMATURE_subdivide_weights_draw) # Edit mode > Right click
    bpy.types.VIEW3D_MT_pose_context_menu.prepend(ARMATURE_subdivide_weights_draw) # Pose mode > Right click
    bpy.types.VIEW3D_MT_paint_weight.append(ARMATURE_subdivide_weights_draw) # Weight Paint mode > Weights

def unregister():
    bpy.utils.unregister_class(ARMATURE_OT_subdivide_weights)

#    bpy.types.VIEW3D_MT_edit_armature.remove(ARMATURE_subdivide_weights_draw)
#    bpy.types.VIEW3D_MT_pose.remove(ARMATURE_subdivide_weights_draw)
    bpy.types.VIEW3D_MT_armature_context_menu.remove(ARMATURE_subdivide_weights_draw)
    bpy.types.VIEW3D_MT_pose_context_menu.remove(ARMATURE_subdivide_weights_draw)
    bpy.types.VIEW3D_MT_paint_weight.remove(ARMATURE_subdivide_weights_draw)

if __name__ == "__main__": # debug; live edit
    register()