## Uninstall the addon -> Run the following script to delete the left overs.
## Have one object active/selected!
#import bpy

#active_mode = bpy.context.object.mode
#bpy.ops.object.mode_set(mode='OBJECT')

#for obj in bpy.data.objects:
#    if obj.type != 'ARMATURE':
#        continue

##    for prop in list(obj.data.keys()):
##        print(prop)

#    mesh = obj.data

#    if mesh.get('sei_rig') is not None:
#        del mesh['sei_rig']
#        print(f'Deleted "sei_rig" property from: {mesh.name}')

#    for bone in mesh.bones:
#        if bone.get('sei_rig') is not None:
#            del bone['sei_rig']
#            print(f'Deleted "sei_rig" property from: {mesh.name}, {bone.name}')

#bpy.ops.object.mode_set(mode=active_mode)

#########

import bpy
import bmesh
import time

from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from math import acos
from mathutils import Matrix

bl_info = {
    "name": "Sei Rig Tools",
    "author": "Seilotte",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "3D View > Properties > Sei",
    "description": "",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/rig_tools",    
    "doc_url": "https://github.com/seilotte/Blender-Stuff/issues",
    "category": "Rigging", # Animation
    }

'''
Prefixes meanings:
    MTA- = Metarig  // "Unmodified"/Original armature.
    RIG- = Rig      // Armature with all the "rig" bones.

    C- = CTR- = Controllers
    M- = MCH- = Mechanical; M_fk-
    H- = HLP- = Helpers
    T- = TWK- = Tweaks; T_end- = Tweak, end of chain.
    W- = WGT- = Widgets

Code meanings:
    bone  = bpy.types.Bone
    ebone = bpy.types.EditBone
    pbone = bpy.types.PoseBone
'''

########################### Custom Variables

# armature = mesh = object.data
# armature.sei_rig
# armature.bones.sei_rig

class SEI_RIG_variables(PropertyGroup):
    target_rig: PointerProperty(type=bpy.types.Armature, name='Target Rig', description='Armature to overwrite while generating the rig')
#    use_xyz_euler: BoolProperty(name='XYZ Euler', description='Apply rotation order "XYZ" to the object and bones - prone to Gimbal Lock', default=True)

    bone_rot_axis: EnumProperty(
        items = [
            # (identifier, name, description, icon, number)
            ('x', 'X', ''),
            ('z', 'Z', ''),
        ],
        name = 'Rotation Axis',
#        description = '',
        default = 'z',
    )

def update_bone_colour(self, context):
    # SEI_RIG_PT_rig_tools assures: Bone exists, is PoseBone.
    obj = context.active_object
    pbones = context.selected_pose_bones

    if obj is None or pbones is None:
        return

    for pbone in pbones:
        if obj.data.bones[pbone.name].sei_rig.rig_type == 'none':
            pbone.color.palette = 'DEFAULT'
            pbone.color.custom.normal = \
            pbone.color.custom.select = \
            pbone.color.custom.active = (0.0, 0.0, 0.0)

        else:
            pbone.color.palette = 'CUSTOM'
            pbone.color.custom.normal = (0.96, 0.26, 0.57) # pink
            pbone.color.custom.select = (0.6, 0.9, 1.0)
            pbone.color.custom.active = (0.7, 1.0, 1.0)

class SEI_RIG_variables_bones(PropertyGroup):
    rig_type: EnumProperty(
        items = [
            # (identifier, name, description, icon, number)
            ('none', 'None', ''),
            (None),
#            ('root', 'Root', ''), # Instead, use bone_name.
#            (None),
            ('tweak', 'Tweak', ''),
            (None),
            ('tentacle', 'Tentacle', ''),
            (None),
            ('arm', 'Arm', ''),
            ('finger', 'Finger', ''),
            ('head', 'Head', ''),
            ('leg', 'Leg', ''),
            ('spine', 'Spine', ''),
        ],
        name = 'Rig Type',
        description = 'Rig type for this bone',
        update = update_bone_colour,
    )

    use_connect: BoolProperty(name='Connect', description='Indicates whether the bone should be included in the bone parent rig type chain') # none
    use_tweakless: BoolProperty(name='Tweakless', description='Exclude the bone from the tweak bones transforms') # none

    use_average: BoolProperty(name='Average', description='Average intermidiate bones with the start and end bone controllers') # tweak
    bbone_segments: IntProperty(name='B-Bones Segments', description='1 = Off; Number of subdivisions of bendy bones', default=1, min=1, max=32) # tweak

    spine_pivot_index: IntProperty(name='Pivot Index', description='Index/Position of the pivot point along the bone rig type chain', default=1, min=1)
    rotation_axis: EnumProperty( # arm, finger, leg
        items = [
            # (identifier, name, description, icon, number)
            ('x', 'X', ''),
            ('z', 'Z', ''),
        ],
        name = 'Rotation Axis',
        description = 'Main rotation axis of the bone rig type chain',
    )

########################### Global PT/OT Properties

class SeiPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sei'

class SeiOperator:
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

########################### Main UI

######### OT Rig Tools

class SEI_RIG_OT_generate(SeiOperator, Operator):
    bl_idname = 'sei_rig.generate'
    bl_label = 'Generate Rig'
    bl_description = 'Generate a rig from the active armature'

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj.data.sei_rig.target_rig != obj.data and \
            any(b.sei_rig.rig_type != 'none' for b in obj.data.bones)

    def execute(self, context):

        start_time = time.time()

        def print_time(string):
            print(f'{string} {time.time() - start_time:.3f} seconds.')

        vars = context.active_object.data.sei_rig

        ###########################
        # 1. Remove old target armature.
        # 1. Create new armature.

        if vars.target_rig:
            bpy.data.armatures.remove(vars.target_rig, do_unlink=True)

        org_obj = context.active_object

        active_mode = org_obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        for layer_obj in context.view_layer.objects:
            layer_obj.select_set(False)

        org_obj.select_set(True)
        context.view_layer.objects.active = org_obj

        # Makes the dup active, assigns to collections. Needs object mode.
        bpy.ops.object.duplicate()

        org_obj.hide_viewport = org_obj.hide_render = True

        obj = context.active_object # Object data.
        mesh = obj.data             # Mesh/Armature data.

        if org_obj.name.startswith('MTA-'):
            obj.name = f'RIG{org_obj.name[3:]}'
        elif org_obj.name.startswith('RIG-'):
            obj.name = org_obj.name
        else:
            obj.name = f'RIG-{org_obj.name}'

        mesh.name = obj.name

        obj.display_type = 'WIRE'
        obj.show_in_front = True
        mesh.display_type = 'WIRE' # WIRE;STICK;OCTAHEDRAL;BBONE;ENVELOPE

        vars.target_rig = mesh

        ###########################
        # 1. Widgets, create meshes.
        # TODO: Do not create all widgets.

        def mesh_create(name='Mesh', vertices=None, edges=[], faces=[]):
            obj = bpy.data.objects.get(name)

            if not obj and vertices:
                mesh = bpy.data.meshes.new(name=name)

                bm = bmesh.new()
                verts = [bm.verts.new(xyz) for xyz in vertices]

                for edge in edges:
                    bm.edges.new([verts[i] for i in edge])

                for face in faces:
                    bm.faces.new([verts[i] for i in face])

                bm.to_mesh(mesh)
                bm.free()

                obj = bpy.data.objects.new(name, mesh)

            return obj

#        def mesh_get_data(mesh):
#            '''
#            Get lists for "create_mesh()" from an object/mesh.
#            Prints vertices, edges and faces lists.
#            '''

#            vertices = [tuple(round(i, 3) for i in v.co) for v in mesh.vertices]
#            edges = [tuple(e.vertices) for e in mesh.edges]
#            faces = [tuple(f.vertices) for f in mesh.polygons]

#            print(f'\nvertices = {vertices},\nedges = {edges}')
##            print(f'\nvertices = {vertices},\nedges = {edges},\nfaces = {faces}')

        map_wgt = {
            'None': None, # .get does this.
            'plane': mesh_create( # Returns obj.
                name = 'WGT-Plane',
                vertices = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0), (0.0, 0.5, 0.0), (0.0, 0.2, 0.0)],
                edges = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5]]
            ),
            'cube': mesh_create(
                name = 'WGT-Cube',
                vertices = [(-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.0, 0.5, 0.0), (0.0, 0.8, 0.0)],
                edges = [[2, 0], [0, 1], [1, 3], [3, 2], [6, 2], [3, 7], [7, 6], [4, 6], [7, 5], [5, 4], [0, 4], [5, 1], [8, 9]]
            ),
            'diamond': mesh_create(
                name = 'WGT-Diamond',
                vertices = [(-0.5, 0.0, 0.0), (0.0, 0.0, -0.5), (0.5, 0.0, 0.0), (0.0, 0.0, 0.5), (0.0, -0.5, 0.0), (0.0, 0.5, 0.0), (0.0, 0.8, 0.0)],
                edges = [[0, 4], [4, 3], [3, 0], [3, 5], [5, 0], [0, 1], [1, 4], [5, 1], [2, 3], [4, 2], [2, 5], [1, 2], [5, 6]]
            ),
            'arrows': mesh_create(
                name = 'WGT-Arrows',
                vertices = [(-0.5, 1.5, -1.0), (0.5, -1.5, -1.0), (0.5, 1.5, -1.0), (0.0, 2.0, -1.0), (0.0, -2.0, -1.0), (-0.5, -1.5, -1.0)],
                edges = [[3, 4], [4, 5], [1, 4], [3, 2], [0, 3]]
            ),
            'octahedral': mesh_create(
                name = 'WGT-Octahedral',
                vertices = [(-0.05, 0.0, 0.0), (0.0, 0.0, -0.05), (0.05, 0.0, 0.0), (0.0, 0.0, 0.05), (0.0, -0.05, 0.0), (0.0, 0.05, 0.0), (-0.05, 1.0, 0.0), (0.0, 1.0, -0.05), (0.05, 1.0, 0.0), (0.0, 1.0, 0.05), (0.0, 0.95, 0.0), (0.0, 1.05, 0.0), (-0.1, 0.1, -0.1), (0.1, 0.1, -0.1), (0.1, 0.1, 0.1), (-0.1, 0.1, 0.1), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
                edges = [[0, 4], [4, 3], [3, 0], [3, 5], [5, 0], [0, 1], [1, 4], [5, 1], [2, 3], [4, 2], [2, 5], [1, 2], [6, 10], [10, 9], [9, 6], [9, 11], [11, 6], [6, 7], [7, 10], [11, 7], [8, 9], [10, 8], [8, 11], [7, 8], [12, 16], [16, 15], [15, 12], [15, 17], [17, 12], [12, 13], [13, 16], [17, 13], [14, 15], [16, 14], [14, 17], [13, 14]]
            ),
            'wire': mesh_create(
                name = 'WGT-Wire',
                vertices = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
                edges = [[0, 1]]
            ),
        }

        # Assign to collection.
        def find_object_collection(object):
            for collection in context.scene.collection.children_recursive:
                if object.name in collection.objects:
                    return collection
            else:
                return context.scene.collection

        def find_layer_collection(target_collection):
            stack = [context.view_layer.layer_collection]

            while stack:
                current_collection = stack.pop()

                if current_collection.collection == target_collection:
                    return current_collection

                stack.extend(current_collection.children)

            return None

        coll_wgt = bpy.data.collections.get('WGT Widgets')

        if not coll_wgt:
            coll_wgt = bpy.data.collections.new('WGT Widgets')
            find_object_collection(obj).children.link(coll_wgt)

        find_layer_collection(coll_wgt).exclude = True

        for widget in map_wgt.values(): # "in" = O(n); .items(), .values()
            if widget is None: continue

            if not coll_wgt.objects.get(widget.name): # "get" or "set()" = O(1).
                coll_wgt.objects.link(widget)

        ###########################
        # 1. Create bone collections.

        for coll in mesh.collections:
            coll.is_visible = False

        def find_bone_collection(target_name):
            for coll in mesh.collections:
                stack = [coll]

                while stack:
                    current_collection = stack.pop()

                    if current_collection.name == target_name:
                        return current_collection

                    stack.extend(current_collection.children)

            return None

        map_coll = {
            'null': find_bone_collection('---') or mesh.collections.new(name='---'),
            'mta': find_bone_collection('_Metarig') or mesh.collections.new(name='_Metarig'),
            'bones': find_bone_collection('_Bones') or mesh.collections.new(name='_Bones'),
            'root': find_bone_collection('_Root') or mesh.collections.new(name='_Root'),
            'ctr': find_bone_collection('_Controllers') or mesh.collections.new(name='_Controllers'),
            'mch': find_bone_collection('_Mechanicals') or mesh.collections.new(name='_Mechanicals'),
            'twk': find_bone_collection('_Tweaks') or mesh.collections.new(name='_Tweaks'),
        }

        for coll in map_coll.values():
            if coll == map_coll['null']:
                continue

            coll.parent = map_coll['null']

        map_coll['null'].is_expanded = True

        map_coll['mta'].is_visible = \
        map_coll['mch'].is_visible = False

        ###########################
        # 1. Assign bones to coll_bones.
        # 1. Get bones with a rig type.

        bones_with_rig_type = []

        for bone in mesh.bones:
            map_coll['mta'].assign(bone)

            if bone.sei_rig.rig_type != 'none':
                bones_with_rig_type.append((bone.name, bone.sei_rig.rig_type))

                bone.sei_rig.rig_type = 'none'
                bone.sei_rig.use_connect = False

                bone.color.palette = 'DEFAULT'
                bone.color.custom.normal = \
                bone.color.custom.select = \
                bone.color.custom.active = (0.0, 0.0, 0.0)

            # TODO: User may want to keep their values.
            bone.bbone_x = \
            bone.bbone_z = bone.length * 0.025

        #########


        print_time('Preparations completed:')


        ###########################
        # 1. Rig types.
        # IMPORTANT PART.

        def return_error(message=""):
            '''
            Assumes:
                - Is executed in a blender operator.
                - Has an active object.
                - Variables: active_mode
            '''
            self.report({'ERROR'}, message)
            bpy.ops.object.mode_set(mode=active_mode)

            return {'FINISHED'}

        def bone_chain_get_names(bone_name=""):
            '''
            Assumes:
                - Variables: mesh, sei_rig properties
            '''
            bone = mesh.bones[bone_name]
            bone.sei_rig.use_connect = False

            chain_list = [bone_name]

            while True:
#                connects = [c for c in bone.children if c.use_connect]
                connects = [c for c in bone.children if c.sei_rig.use_connect]

                if len(connects) == 1:
                    bone = connects[0]
                    bone.sei_rig.use_connect = False

                    chain_list.append(bone.name)
                else:
                    break

            return chain_list

        def bone_chain_validate(chain_list=[], min_bones=1, max_bones=999):
            '''
            Assumes:
                - Is executed in a blender operator.
                - Variables: active_mode
            '''
            if not min_bones <= len(chain_list) <= max_bones:
                self.report(
                    {'ERROR'},
                    f'Expected between {min_bones} and {max_bones} bone(s) ' \
                    f'in the "{chain_list[0]}" chain.'
                )

                return True # Functions return None by default.

        def ebone_get_and_disconnect(bone_names=[]):
            '''
            Assumes:
                - Edit mode.
                - Variables: mesh
            '''
            ebones = []

            for name in bone_names:
                ebone = mesh.edit_bones[name]
                ebone.use_connect = False
                map_coll['bones'].assign(ebone)

                ebones.append(ebone)

            return ebones

        def ebone_new(
            target_ebone=None,
            prefix="",
            length_percentage=1.0,
            parent_ebone=None,
            use_at_tail=False,
            use_align_y_world=False
        ):
            '''
            Create and set up edit_bone parameters.

            Assumes:
                - Edit mode.
                - Variables: mesh
            '''
            new_ebone = mesh.edit_bones.new(f'{prefix}{target_ebone.name}')

#            new_bone.use_connect = \
            new_ebone.use_deform = False

            if use_align_y_world:
                new_ebone.tail[1] = round(target_ebone.length, 3) * length_percentage
                new_ebone.head += target_ebone.head
                new_ebone.tail += target_ebone.head
            else:
                new_ebone.head = target_ebone.head
                new_ebone.tail = target_ebone.tail
                new_ebone.roll = target_ebone.roll
                new_ebone.length *= length_percentage

            new_ebone.bbone_x = \
            new_ebone.bbone_z = new_ebone.length * 0.025

            if use_at_tail:
                new_ebone.head += target_ebone.vector
                new_ebone.tail += target_ebone.vector

            if isinstance(parent_ebone, str):
                parent_ebone = mesh.edit_bones[parent_ebone]

            new_ebone.parent = parent_ebone

            return new_ebone

        def ebone_setup_tweaks(
            ebones=[],
            make_end=True,
            use_average=False,
            return_list=False
        ):
            '''
            It is meant to be used inside a sei rig type.
            Create and set up tweak bones.

            Assumes:
                - Edit mode.
                - Variables: ebones, root_eb, bone, map_pbones, map_coll[],
                             map_bcol[], map_wgt[], bones_with_rig_type,
                             sei_rig properties, mesh
                - Functions: ebone_new()
            '''

            new_ebones = []
            chain_len = len(ebones)
            first_parent = ebones[0].parent or root_eb

            for index in range(chain_len):
                eb = ebones[index]

                parent = eb.parent or first_parent

                if parent in ebones:
                    parent = first_parent

                lock_rot = () if mesh.bones[bone_name].sei_rig.bbone_segments > 1 else \
                           (True, False, True)

                new_eb = ebone_new(eb, 'T-', 0.25, parent, 0, 0)
                new_ebones.append(new_eb)
                if use_average and make_end and index > 0:
                    map_pbones.append((
                        new_eb.name,
                        (map_coll['twk'], map_bcol['blue2'], map_wgt['diamond']),
                        (0, lock_rot, 0),
                        (),
                        [(
                            'COPY_LOCATION',
                            f'T-{ebones[0].name}',
                            ('use_offset', True),
                            ('target_space', 'LOCAL_OWNER_ORIENT'),
                            ('owner_space', 'LOCAL'),
                            ('influence', 1.0 - (index / chain_len))
                        ), (
                            'COPY_LOCATION',
                            f'T_end-{ebones[-1].name}',
                            ('use_offset', True),
                            ('target_space', 'LOCAL_OWNER_ORIENT'),
                            ('owner_space', 'LOCAL'),
                            ('influence', index / chain_len)
                        )]
                    ))
                else:
                    map_pbones.append((
                        new_eb.name,
                        (map_coll['twk'], map_bcol['blue2'], map_wgt['diamond']),
                        (0, lock_rot, 0),
                        (),
                        []
                    ))

                eb.parent = new_eb

                # Isolate transforms.
                for child in eb.children:
                    if child.name in [i[0] for i in bones_with_rig_type] \
                    or mesh.bones[child.name].sei_rig.use_tweakless:
                        child.parent = eb.parent

                if eb == ebones[-1]:
                    subtarget = f'T_end-{eb.name}' if make_end else ""
                else:
                    subtarget = f'T-{ebones[index+1].name}'

                map_pbones.append((
                    eb.name,
                    (),
                    (),
                    (),
                    [('STRETCH_TO', subtarget)]
                ))

                if not make_end or eb != ebones[-1]:
                    continue

                new_eb = ebone_new(eb, 'T_end-', 0.25, parent, 1, 0)
                new_ebones.append(new_eb)
                map_pbones.append((
                    new_eb.name,
                    (map_coll['twk'], map_bcol['blue'], map_wgt['diamond']),
                    (0, lock_rot, 0),
                    (),
                    []
                ))

            if return_list:
                return new_ebones

            return None

        def ebone_get_pole_vector(first_ebone, last_ebone):
            '''
            Credit: compute_elbow_vector(); https://github.com/blender/blender-addons/blob/main/rigify/rigs/limbs/limb_rigs.py

            Assumes:
                - Edit mode.
            '''
            lo_vector = last_ebone.vector
            tot_vector = last_ebone.tail - first_ebone.head
            pole_vector = (lo_vector.project(tot_vector) - lo_vector).normalized() \
                        * tot_vector.length

            return pole_vector

        def ebone_get_pole_angle(first_ebone, last_ebone, pole_ebone):
            '''
            Credit: https://blender.stackexchange.com/questions/19754/how-to-set-calculate-pole-angle-of-ik-constraint-so-the-chain-does-not-move

            first_ebone // Last bone of the ik chain.
            last_ebone  // Bone with the ik constraint.
            pole_ebone  // Pole target bone.

            Assumes:
                - Edit mode.
            '''
            pole_normal = (last_ebone.tail - first_ebone.head).cross(pole_ebone.head - first_ebone.head)

            projected_pole_axis = pole_normal.cross(first_ebone.vector)
            angle = first_ebone.x_axis.angle(projected_pole_axis)

            if first_ebone.x_axis.cross(projected_pole_axis).angle(first_ebone.vector) < 1:
                angle = -angle

#            print(round(angle * 57.2957795131, 3)) # debug

            return angle

        def pbone_clear_constraints(bone_names=[]):
            '''
            Assumes:
                - Pose mode.
                - Variables: obj
            '''
            for name in bone_names:
                pbone = obj.pose.bones[name]

                for constraint in pbone.constraints:
                    pbone.constraints.remove(constraint)

            return

        def pbone_setup_map(map_pbones=[]):
            '''
            Set up pose_bones parameters.

            Assumes:
                - Pose mode.
                - Variables: obj, map_coll[], mathutils.Matrix
            '''
            for bone_name, data, data_lock, data_shape, data_constraints \
            in map_pbones:
                pbone = obj.pose.bones[bone_name]

                # Collection, colour, shape.
                coll_target, bone_colour, bone_shape = \
                data or (None,)*3

                if coll_target:
                    coll_target.assign(pbone)

                if bone_name.startswith(('C-', 'C_')):
                    map_coll['ctr'].assign(pbone)
                elif bone_name.startswith(('M-', 'M_')):
                    map_coll['mch'].assign(pbone)
                elif bone_name.startswith(('T-', 'T_')):
                    map_coll['twk'].assign(pbone)

                if bone_colour:
                    pbone.color.palette = 'CUSTOM'
                    pbone.color.custom.normal = bone_colour
                    pbone.color.custom.select = (0.6, 0.9, 1.0)
                    pbone.color.custom.active = (0.7, 1.0, 1.0)

                if bone_shape:
                    pbone.custom_shape = bone_shape

                # Lock transforms.
                lock_location, lock_rotation, lock_scale = \
                data_lock or (None,)*3

                if lock_location:
                    pbone.lock_location = lock_location
                if lock_rotation:
                    pbone.lock_rotation = lock_rotation
                    pbone.lock_rotation_w = True
                if lock_scale:
                    pbone.lock_scale = lock_scale

                # Shape data.
                data_shape0, data_shape1 = \
                data_shape or (None, None)

                name_transforms, location, rotation, scale = \
                data_shape0 or (None,)*4

                if name_transforms:
                    pbone.custom_shape_transform = obj.pose.bones.get(name_transforms)

                scale = scale or (1.0, 1.0, 1.0)
                location = location or (0.0, 0.0, 0.0)
                rotation = tuple(i * 0.01745329251 for i in rotation) \
                if rotation else (0.0, 0.0, 0.0) # To radians.

                name_align, use_location, use_rotation, use_scale = \
                data_shape1 or (None,)*4

                x = pbone.bone
                y = obj.pose.bones[name_align].bone if name_align else None

                if y and use_scale:
                    scale = tuple(
                        (y.vector.length / x.vector.length) * scale[i]
                        for i in range(3)
                    )
                if y and use_location:
                    location = tuple(
                        (y.head_local[i] + location[i]) - x.head_local[i]
                        for i in range(3)
                    )
                if y and use_rotation:
                    # There is an issue if x, y and z are used at the same time.
                    # TODO: Find a solution for it.
                    rotation = (
                        x.matrix_local.inverted()
                        @ y.matrix_local
                        @ Matrix.Rotation(rotation[0], 4, 'X')
                        @ Matrix.Rotation(rotation[1], 4, 'Y')
                        @ Matrix.Rotation(rotation[2], 4, 'Z')
                    ).to_euler()

                pbone.custom_shape_scale_xyz = scale
                pbone.custom_shape_translation = location
                pbone.custom_shape_rotation_euler = rotation

                # Constraints.
                for data in data_constraints:
                    new_constraint = pbone.constraints.new(data[0]) # type

                    if hasattr(new_constraint, 'target'):
                        new_constraint.target = obj
                    if hasattr(new_constraint, 'pole_target'):
                        new_constraint.pole_target = obj

                    if hasattr(new_constraint, 'subtarget'):
                        new_constraint.subtarget = data[1] # subtarget

                    for attribute, value in data[2:]:
                        setattr(new_constraint, attribute, value) # hasattr()

            map_pbones.clear()

            return

        #########

        map_bcol = { # pbone.color.custom.normal
            'blue': (0.3, 0.7, 0.9), # (0.1, 0.5, 0.7)
            'blue2': (0.3, 0.9, 0.9),
            'green': (0.1, 0.6, 0.1),
            'pink': (0.96, 0.26, 0.57),
            'purple': (0.9, 0.7, 0.8),
            'red': (1.0, 0.05, 0.1),
            'white': (0.9, 0.9, 0.9),
            'yellow': (1.0, 0.8, 0.1),
        }

        # Read "root" rig type for a detailed syntax.
        map_pbones = [] # setup_pose_bones()

        for bone_name, rig_type in bones_with_rig_type:

            ##################
            # Root.
            # It could be outside the for loop. Aesthetic purpose.

            if bone_name == bones_with_rig_type[0][0]:

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                root_eb = mesh.edit_bones.get('root') or \
                          mesh.edit_bones.get('Root') or \
                          mesh.edit_bones.get('ROOT')

                if root_eb is None:
                    root_eb = mesh.edit_bones.new('Root')
                    root_eb.tail[1] = 1.0
                    root_eb.use_deform = False

                # Save the name since switching modes.
                root_name = root_eb.name

                for eb in mesh.edit_bones:
                    if eb.parent is None:
                        eb.parent = root_eb

                ### Object mode.
                bpy.ops.object.mode_set(mode='OBJECT') # Update mesh.bones.

                bone_names = bone_chain_get_names(root_name)
                if bone_chain_validate(bone_names, 1, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                chain_len = len(ebones)
                root_eb = mesh.edit_bones[root_name]

                for index in range(chain_len):
                    eb = ebones[index]

                    # Force roots to origin.
                    eb.head = (0.0, 0.0, 0.0)
                    eb.tail = (0.0, (1.0 - index / chain_len) * root_eb.length, 0.0)
                    eb.roll = 0.0
                    eb.use_deform = False

                    map_pbones.append((
                        # bone_name
                        eb.name,
                        # [data]
                        # (coll_target, bone_colour, bone_shape)
                        (map_coll['root'], map_bcol['purple'], map_wgt['plane']),
                        # [data_lock]
                        # (lock_location, lock_rotation, lock_scale)
                        (),
                        # [data_shape, data_shape_align]
                        # ((name_transforms, location, rotation(degrees), scale),
                        #  (name_align, use_location, use_rotation, use_scale))
                        ((0, (0.0, eb.length * 0.5, 0.0), 0, (0.5, 1.0, 1.0)), 0),
                        # [pbones_data_constraints]
                        # [(type, subtarget, (attribute, value), (attribute, value)...)]
                        []
                    ))

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                # TODO: Retarget constraints to new/rig_type/tweak bones.
                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                del root_eb, bone_names, ebones, \
                eb, index, chain_len

                print_time(f'Generated root:')

#            ##################
#            # Template.

#            elif rig_type == '':

#                bone_names = bone_chain_get_names(bone_name)
#                if bone_chain_validate(bone_names, 1, 999): return {'FINISHED'}

#                ### Edit mode.
#                bpy.ops.object.mode_set(mode='EDIT')

#                ebones = ebone_get_and_disconnect(bone_names)

#                ebone_setup_tweaks(ebones)

#                ### Pose mode.
#                bpy.ops.object.mode_set(mode='POSE')

#                pbone_clear_constraints(bone_names)
#                pbone_setup_map(map_pbones) # Clears map_pbones.

#                del bone_names, ebones

#                print_time(f'Generated {rig_type}:')
#                continue

            ##################
            # Tweak.

            if rig_type == 'tweak':

                bone_names = bone_chain_get_names(bone_name)
                if bone_chain_validate(bone_names, 1, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                root_eb = mesh.edit_bones[root_name]

                tweak_ebones = ebone_setup_tweaks(
                    ebones,
                    use_average = mesh.bones[bone_name].sei_rig.use_average,
                    return_list = True
                )

                if mesh.bones[bone_name].sei_rig.bbone_segments > 1:
                    chain_len = len(ebones)

                    for index in range(chain_len):
                        eb = ebones[index]

                        # We could use map_pbones names.
                        prev_eb = tweak_ebones[index-1] if index > 0 else \
                                  tweak_ebones[index]

                        next_eb = tweak_ebones[index+1] if eb != ebones[-1] else \
                                  tweak_ebones[-1]

                        new_eb = ebone_new(eb, 'M_bb-', 0.5, root_eb, 0, 0)
                        map_pbones.append((
                            new_eb.name,
                            (),
                            (),
                            (),
                            [(
                                'COPY_LOCATION',
                                prev_eb.name,
                            ), (
                                'DAMPED_TRACK',
                                next_eb.name,
                            ), (
                                'COPY_TRANSFORMS',
                                tweak_ebones[index].name,
                                ('mix_mode', 'BEFORE_FULL'),
                                ('target_space', 'LOCAL_OWNER_ORIENT'),
                                ('owner_space', 'LOCAL')
                            )]
                        ))

                        if eb != ebones[-1]:
                            continue

                        new_eb = ebone_new(eb, 'M_bb_end-', 0.5, root_eb, 0, 0)
                        map_pbones.append((
                            new_eb.name,
                            (),
                            (),
                            (),
                            [(
                                'COPY_LOCATION',
                                tweak_ebones[index].name,
                            ), (
                                'DAMPED_TRACK',
                                next_eb.name,
                            ), (
                                'COPY_TRANSFORMS',
                                next_eb.name,
                                ('mix_mode', 'BEFORE_FULL'),
                                ('target_space', 'LOCAL_OWNER_ORIENT'),
                                ('owner_space', 'LOCAL')
                            )]
                        ))

                    for index in range(chain_len):
                        eb = ebones[index]

                        # We could use map_pbones names.
                        bbone = mesh.edit_bones[f'M_bb-{eb.name}']

                        next_bbone = mesh.edit_bones[f'M_bb-{ebones[index+1].name}'] \
                                     if eb != ebones[-1] else \
                                     mesh.edit_bones[f'M_bb_end-{eb.name}']

                        eb.bbone_segments = mesh.bones[bone_name].sei_rig.bbone_segments
#                        eb.bbone_x = \
#                        eb.bbone_z = new_eb.length * 0.05
                        eb.bbone_handle_type_start = \
                        eb.bbone_handle_type_end = 'TANGENT'
                        eb.bbone_custom_handle_start = bbone
                        eb.bbone_custom_handle_end = next_bbone
#                        eb.bbone_handle_use_ease_start = \
#                        eb.bbone_handle_use_ease_end = True

                    del chain_len, index, eb, tweak_ebones, prev_eb, next_eb, new_eb, \
                    bbone, next_bbone

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                del bone_names, ebones, root_eb

                print_time(f'Generated {rig_type}:')
                continue

            ##################
            # Tentacle.

            elif rig_type == 'tentacle':
                continue

            ##################
            # Finger.

            elif rig_type == 'finger':

                bone_names = bone_chain_get_names(bone_name)
                if bone_chain_validate(bone_names, 2, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                rot_axis = mesh.bones[bone_name].sei_rig.rotation_axis

                cint_eb = ebone_new(ebones[1], 'C-', 1.0, None, 0, 0)
                map_pbones.append((
                    cint_eb.name,
                    (0, map_bcol['yellow'], map_wgt['plane']),
                    (
                        (True, True, True),
                        (False, True, True) if rot_axis == 'x' else (True, True, False),
                        (True, True, True),
                    ),
                    ((0, 0, (-90.0, 0.0, 0.0), (0.75, 0.75, 0.75)), 0),
                    []
                ))

                root_eb = mesh.edit_bones[root_name]

                for eb in ebones:
                    if eb == ebones[0]:
                        parent = eb.parent or root_eb
                        constraints = []
                    else:
                        parent = map_pbones[-1][0]
                        constraints = [(
                            'COPY_ROTATION',
                            cint_eb.name,
                            ('use_y', False),
                            ('use_z', False) if rot_axis == 'x' else ('use_x', False),
                            ('mix_mode', 'ADD'),
                            ('target_space', 'LOCAL'),
                            ('owner_space', 'LOCAL'),
                        )]

                    new_eb = ebone_new(eb, 'C_fk-', 1.0, parent, 0, 0)
                    map_pbones.append((
                        new_eb.name,
                        (map_coll['mch'], map_bcol['pink'], map_wgt['plane']),
                        (0, (False, True, False), 0),
                        ((0, 0, (-90.0, 0.0, 0.0), (0.5, 0.5, 0.5)), 0),
                        constraints
                    ))

                    if eb == ebones[0]:
                        cint_eb.parent = new_eb

                    eb.parent = new_eb

                ebone_setup_tweaks(ebones)

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                del bone_names, ebones, \
                rot_axis, cint_eb, \
                root_eb, eb, parent, constraints, new_eb

                print_time(f'Generated {rig_type}:')
                continue

            ##################
            # Head.

            elif rig_type == 'head':

                bone_names = bone_chain_get_names(bone_name)
                if bone_chain_validate(bone_names, 1, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                # 1. Connect to spine.
                # TODO: Check if it is 100% a spine rig type.
                connect_data = None

                if (eb := ebones[0].parent) \
                and eb.name.startswith('T-') \
                and (eb := eb.parent) \
                and eb.name.startswith('C_fk-'):
                    connect_data = (eb.name[5:], f'T-{ebones[0].name}')
                    mesh.edit_bones[eb.name[5:]].tail = ebones[0].head

                eb = ebones[0]
                root_eb = mesh.edit_bones[root_name]
                parent = ebones[0].parent or root_eb

                if connect_data:
                    parent =  mesh.edit_bones[f'C_fk-{connect_data[0]}']

                mrot_eb = ebone_new(eb, 'M_rot-', 0.5, parent, 0, 1)
                map_pbones.append((
                    mrot_eb.name,
                    (map_coll['ctr'], 0, 0),
                    ((True,)*3,)*3,
                    (),
                    [('COPY_ROTATION', root_name)]
                ))
                chead_eb = ebone_new(eb, 'C_head-', 1.0, mrot_eb, 0, 1)
                map_pbones.append((
                    chead_eb.name,
                    (0, map_bcol['yellow'], map_wgt['plane']),
                    (),
                    ((f'M-{ebones[-1].name}', ebones[-1].vector, (-90., 0., 0.), (1.5,)*3),
                    (ebones[-1].name, 0, 1, 1)),
                    [],
                ))

                chain_len = len(ebones)

                for index in range(chain_len):
                    eb = ebones[index]

                    parent = mrot_eb if index < 1 else map_pbones[-1][0]
                    influence = (2.0 * (index+1)) / (chain_len * (chain_len+1))

                    new_eb = ebone_new(eb, 'M-', 0.5, parent, 0, 1)
                    map_pbones.append((
                        new_eb.name,
                        (),
                        (),
                        (),
                        [(
                            'COPY_TRANSFORMS',
                            chead_eb.name, 
                            ('target_space', 'LOCAL'),
                            ('owner_space', 'LOCAL'),
                            ('influence', influence)
                        )]
                    ))
                    new_eb = ebone_new(eb, 'C_fk-', 1.0, new_eb, 0, 0)
                    map_pbones.append((
                        new_eb.name,
                        (0, map_bcol['pink'], map_wgt['plane']),
                        (),
                        ((0, 0, (-90.0, 0.0, 0.0), (1.5, 1.5, 1.5)), 0),
                        []
                    ))

                    eb.parent = new_eb

                ebone_setup_tweaks(ebones)

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                ### 2. Connect to spine.
                if connect_data:
                    pb = obj.pose.bones[connect_data[0]]

                    # ebone_setup_tweaks() always adds a stretch_to constraint.
                    constraint = pb.constraints[0]
                    subtarget = constraint.subtarget

                    constraint.subtarget = connect_data[1]
                    constraint.rest_length = 0.0 # reset

                    if subtarget and subtarget.startswith('T_end-'):
                        bpy.ops.object.mode_set(mode='EDIT')
                        mesh.edit_bones.remove(mesh.edit_bones[subtarget])

                    del pb, constraint, subtarget

                del bone_names, ebones, \
                eb, root_eb, parent, mrot_eb, chead_eb, \
                chain_len, index, new_eb, influence, \
                connect_data

                print_time(f'Generated {rig_type}:')
                continue

            ##################
            # Spine.

            elif rig_type == 'spine':

                bone_names = bone_chain_get_names(bone_name)
                if bone_chain_validate(bone_names, 2, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                chain_len = len(ebones)
                pivot_index = mesh.bones[bone_name].sei_rig.spine_pivot_index

                if pivot_index > chain_len - 1:
                    return return_error(
                        f'Expected pivot position ({pivot_index}) in "{bone_name}" ' \
                        f'chain to be less than {chain_len}'
                    )

                eb = ebones[pivot_index]
                root_eb = mesh.edit_bones[root_name]

                ctorso_eb = ebone_new(eb, 'C_torso-', 1.5, ebones[0].parent or root_eb, 0, 1)
                map_pbones.append((
                    ctorso_eb.name,
                    (0, map_bcol['purple'], map_wgt['plane']),
                    (),
                    ((0, 0, (-90.0, 0.0, 0.0), (2.,)*3), (eb.name, 0, 1, 0)),
                    []
                ))
                cchest_eb = ebone_new(eb, 'C_chest-', 1.0, ctorso_eb, 0, 1)
                map_pbones.append((
                    cchest_eb.name,
                    (0, map_bcol['yellow'], map_wgt['plane']),
                    (),
                    ((f'M-{ebones[-1].name}', 0, (-90., 0., 0.), (2.5,)*3),
                     (ebones[-1].name, 0, 1, 0)),
                    []
                ))
                chips_eb = ebone_new(eb, 'C_hips-', 1.0, ctorso_eb, 0, 1)
                map_pbones.append((
                    chips_eb.name,
                    (0, map_bcol['yellow'], map_wgt['plane']),
                    (),
                    ((0, 0, (-90.0, 0.0, 0.0), (2.5,)*3), (eb.name, 0, 1, 0)),
                    []
                ))
                mpivot_eb = ebone_new(eb, 'M_pivot-', 0.5, ctorso_eb, 0, 1)
                map_pbones.append((
                    mpivot_eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_TRANSFORMS',
                        f'M_pivot_T-{eb.name}',
                        ('influence', 1.0),
                    ), (                    
                        'COPY_TRANSFORMS',
                        f'M_pivot_B-{eb.name}',
                        ('influence', 0.5)
                    )]
                ))

                for direction in [1, -1]:
                    if direction > 0:
                        prefix = 'M_pivot_T-'
                        subtarget = map_pbones[1][0] # chest
                        influence = 1.0 / (chain_len - pivot_index)
                        stop = chain_len
                    else:
                        prefix = 'M_pivot_B-'
                        subtarget = map_pbones[2][0] # hips
                        influence = 1.0 / pivot_index
                        stop = 0

                    for index in range(pivot_index, stop, direction):
                        eb = ebones[index]

                        if index == pivot_index:
                            new_eb = ebone_new(eb, prefix, 0.5, ctorso_eb, 0, 1)
                            map_pbones.append((
                                new_eb.name,
                                (),
                                (),
                                (),
                                [(
                                    'COPY_TRANSFORMS',
                                    subtarget,
                                    ('target_space', 'LOCAL'),
                                    ('owner_space', 'LOCAL'),
                                    ('influence', influence)
                                )]
                            ))

                            eb.parent = mpivot_eb

                        else:
                            new_eb = ebone_new(eb, 'M-', 0.5, map_pbones[-1][0], 0, 1)
                            map_pbones.append((
                                new_eb.name,
                                (),
                                (),
                                (),
                                [(
                                    'COPY_TRANSFORMS',
                                    subtarget,
                                    ('target_space', 'LOCAL'),
                                    ('owner_space', 'LOCAL'),
                                    ('influence', influence)
                                )]
                            ))
                            new_eb = ebone_new(eb, 'C_fk-', 1.0, new_eb, 0, 0)
                            map_pbones.append((
                                new_eb.name,
                                (0, map_bcol['pink'], map_wgt['plane']),
                                (),
                                ((0, 0, (-90.0, 0.0, 0.0), (1.5, 1.5, 1.5)), 0),
                                []
                            ))

                            eb.parent = new_eb

                ebones[0].parent = new_eb # M_fk-last or M_pivot_B-last

                ebone_setup_tweaks(ebones)

                if pivot_index == chain_len - 1:
                    mesh.edit_bones[f'T_end-{ebones[-1].name}'].parent = \
                    mesh.edit_bones[f'M_pivot_T-{ebones[-1].name}']

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                del bone_names, ebones, chain_len, pivot_index, \
                eb, root_eb, ctorso_eb, cchest_eb, chips_eb, mpivot_eb, \
                direction, prefix, subtarget, influence, stop, index, new_eb

                print_time(f'Generated {rig_type}:')
                continue

            ##################
            # Arm.

            elif rig_type == 'arm':

                bone_names = bone_chain_get_names(bone_name)
                if bone_chain_validate(bone_names, 3, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                ebones2 = ebones[-1:] # Last bone: Hand[0]
                ebones = ebones[:-1] # Limb chain.

                root_eb = mesh.edit_bones[root_name]
                parent = ebones[0].parent or root_eb

                for eb in ebones:
                    new_eb = ebone_new(
                        eb, 'M_ik-', 1.0,
                        parent if eb == ebones[0] else map_pbones[-2][0], 0, 0
                    )
                    map_pbones.append((
                        new_eb.name,
                        (),
                        (),
                        (),
                        []
                    ))
                    new_eb = ebone_new(eb, 'M_scl-', 0.5, map_pbones[-1][0], 0, 0)
                    map_pbones.append((
                        new_eb.name,
                        (),
                        (),
                        (),
                        [('COPY_SCALE', root_name)]
                    ))

                    eb.parent = new_eb

                cik_eb = ebone_new(ebones2[0], 'C_ik-', 1.0, root_eb, 0, 0)
                map_pbones.append((
                    cik_eb.name,
                    (0, map_bcol['yellow'], map_wgt['plane']),
                    (),
                    ((
                        0,
                        (0.0, ebones2[0].length, 0.0),
                        () if mesh.bones[bone_name].sei_rig.rotation_axis == 'x' else \
                        (0.0, -90.0, 0.0),
                        (1.5, 2.0, 1.5)
                    ), 0),
                    []
                ))

                ebones2[0].parent = cik_eb

                # 1. Set up ik.
                eb = ebones[-1]

                elbow_vector = ebone_get_pole_vector(ebones[0], eb)

                if elbow_vector == elbow_vector * 0.0:
                    return return_error(
                        f'Fix bone "{ebones[-1].name}" head position.'
                    )

                pole_eb = ebone_new(eb, f'C_pole-', 0.25, parent, 0, 1)
                pole_eb.head += elbow_vector
                pole_eb.tail += elbow_vector
                pole_eb.roll = 0.0
                map_pbones.append((
                    pole_eb.name,
                    (0, map_bcol['purple'], map_wgt['diamond']),
                    (0, (True,)*3, (True,)*3),
                    (),
                    []
                ))

                line_eb = ebone_new(eb, f'C_line-', 1.0, new_eb, 0, 1) # M_scl-last
                line_eb.head = eb.head
                line_eb.tail = pole_eb.head
                line_eb.roll = 0.0
                line_eb.hide_select = True
                map_pbones.append((
                    line_eb.name,
                    (0, map_bcol['purple'], map_wgt['wire']),
                    ((True,)*3,)*3,
                    (),
                    [('STRETCH_TO', pole_eb.name)]
                ))

                pole_angle = ebone_get_pole_angle(ebones[0], eb, pole_eb)
                map_pbones.append((
                    f'M_ik-{eb.name}',
                    (),
                    (),
                    (),
                    [(
                        'IK',
                        cik_eb.name,
                        ('pole_subtarget', pole_eb.name),
                        ('pole_angle', pole_angle),
                        ('chain_count', len(ebones))
                    )]
                ))

                ebone_setup_tweaks(ebones + ebones2, make_end=False)
                map_pbones.pop(-1) # Remove line if make_end.

                # Helper elbow.
#                eb = ebones[-1]

                eb.head = mesh.edit_bones[f'M_ik-{eb.name}'].tail
                eb.tail = mesh.edit_bones[f'M_ik-{eb.name}'].head

                rot_axis = mesh.bones[bone_name].sei_rig.rotation_axis

                map_pbones.pop(-2) # -2;-4 if make_end.
                map_pbones.append((
                    eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_LOCATION',
                        f'T-{ebones2[0].name}'
                    ), (
                        'STRETCH_TO',
                        f'T-{eb.name}'
                    ), (
                        'TRANSFORM',
                        f'M_ik-{eb.name}',
                        ('target_space', 'LOCAL'),
                        ('owner_space', 'LOCAL'),
                        ('map_from', 'ROTATION'),
                        ('map_to', 'ROTATION'),

                        ('from_min_' + rot_axis + '_rot', -3.141592) \
                        if pole_angle > 0.0 else \
                        ('from_max_' + rot_axis + '_rot', 3.141592),

                        ('to_min_' + rot_axis + '_rot', -0.1570796) \
                        if pole_angle > 0.0 else \
                        ('to_max_' + rot_axis + '_rot', 0.1570796)
                    )]
                ))

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                # 2. Set up ik.
                for name in bone_names[:-1]:
                    pb = obj.pose.bones[f'M_ik-{name}']

                    pb.ik_stretch = 0.1

                    if name != bone_names[-1]:
                        continue

                    if rot_axis == 'x':
                        pb.lock_ik_y = True
                        pb.lock_ik_z = True
                    else:
                        pb.lock_ik_y = True
                        pb.lock_ik_x = True

                del bone_names, ebones, \
                root_eb, parent, eb, new_eb, cik_eb, \
                elbow_vector, pole_eb, line_eb, pole_angle, \
                rot_axis, name, pb

                print_time(f'Generated {rig_type}:')
                continue

            ##################
            # Leg.

            elif rig_type == 'leg':

                bone_names = bone_chain_get_names(bone_name)
                if bone_chain_validate(bone_names, 5, 999): return {'FINISHED'}

                ### Edit mode.
                bpy.ops.object.mode_set(mode='EDIT')

                ebones = ebone_get_and_disconnect(bone_names)

                ebones2 = ebones[-3:] # Last 3 bones: Foot[0] -> Toe[1] -> Heel_Pivots[2]
                ebones = ebones[:-3] # Limb chain.

                root_eb = mesh.edit_bones[root_name]
                parent = ebones[0].parent or root_eb

                for eb in ebones:
                    new_eb = ebone_new(
                        eb, 'M_ik-', 1.0,
                        parent if eb == ebones[0] else map_pbones[-2][0], 0, 0
                    )
                    map_pbones.append((
                        new_eb.name,
                        (),
                        (),
                        (),
                        []
                    ))
                    new_eb = ebone_new(eb, 'M_scl-', 0.5, map_pbones[-1][0], 0, 0)
                    map_pbones.append((
                        new_eb.name,
                        (),
                        (),
                        (),
                        [('COPY_SCALE', root_name)]
                    ))

                    eb.parent = new_eb

                cik_eb = ebone_new(ebones2[0], 'C_ik-', 1.0, root_eb, 0, 0)
                map_pbones.append((
                    cik_eb.name,
                    (0, map_bcol['yellow'], map_wgt['plane']),
                    (),
                    ((
                        0,
                        (0.0, ebones2[0].length, 0.0),
                        () if mesh.bones[bone_name].sei_rig.rotation_axis == 'x' else \
                        (0.0, -90.0, 0.0),
                        (1.5, 2.0, 1.5)
                    ), 0),
                    []
                ))

                # Foot rig.
                cpivot0_eb = ebone_new(ebones2[1], 'C_pivot0-', 1.0, cik_eb, 0, 0)
                map_pbones.append((
                    cpivot0_eb.name,
                    (0, map_bcol['pink'], map_wgt['plane']),
                    ((True, True, True), 0, (True, True, True)),
                    ((0, 0, (90.0, 0.0, 0.0), 0), 0),
                    []
                ))
                cheel_eb = ebone_new(ebones2[2], 'C_heel-', 1.0, cpivot0_eb, 0, 1)
                map_pbones.append((
                    cheel_eb.name,
                    (0, map_bcol['pink'], map_wgt['plane']),
                    ((True, True, True), 0, (True, True, True)),
                    ((0, 0, (90.0, 0.0, 0.0), (0.5, 0.5, 0.5)), 0),
                    []
                ))
                mpivot1_eb = ebone_new(ebones2[2], 'M_pivot1-', 0.5, cpivot0_eb, 0, 1)
                map_pbones.append((
                    mpivot1_eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_ROTATION',
                        cheel_eb.name,
                        ('use_x', False),
                        ('use_z', False),
                        ('target_space', 'LOCAL'),
                        ('owner_space', 'LOCAL')
                    ), (
                        'LIMIT_ROTATION',
                        '',
                        ('use_limit_y', True),
                        ('min_y', -6.28318530718),
                        ('owner_space', 'LOCAL')
                    )]
                ))
                mpivot2_eb = ebone_new(ebones2[2], 'M_pivot2-', 0.5, mpivot1_eb, 1, 1)
                map_pbones.append((
                    mpivot2_eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_ROTATION',
                        cheel_eb.name,
                        ('use_x', False),
                        ('use_z', False),
                        ('target_space', 'LOCAL'),
                        ('owner_space', 'LOCAL')
                    ), (
                        'LIMIT_ROTATION',
                        '',
                        ('use_limit_y', True),
                        ('max_y', 6.28318530718),
                        ('owner_space', 'LOCAL')
                    )]
                ))
                mpivot3_eb = ebone_new(ebones2[2], 'M_pivot3-', 0.5, mpivot2_eb, 0, 1)
                map_pbones.append((
                    mpivot3_eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_ROTATION',
                        cheel_eb.name,
                        ('use_y', False),
                        ('use_z', False),
                        ('target_space', 'LOCAL'),
                        ('owner_space', 'LOCAL')
                    ), (
                        'LIMIT_ROTATION',
                        '',
                        ('use_limit_x', True),
                        ('min_x', -6.28318530718),
                        ('owner_space', 'LOCAL')
                    )]
                ))
                mpivot4_eb = ebone_new(ebones2[1], 'M_pivot4-', 0.5, mpivot3_eb, 0, 1)
                map_pbones.append((
                    mpivot4_eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_ROTATION',
                        cheel_eb.name,
                        ('target_space', 'POSE'),
                        ('owner_space', 'POSE')
                    )]
                ))
                mfoot_eb = ebone_new(ebones2[0], 'M-', 0.5, mpivot4_eb, 0, 0)
                map_pbones.append((
                    mfoot_eb.name,
                    (),
                    (),
                    (),
                    []
                ))
                mrot_eb = ebone_new(ebones2[1], 'M_rot-', 0.5, mfoot_eb, 0, 1)
                map_pbones.append((
                    mrot_eb.name,
                    (),
                    (),
                    (),
                    [('COPY_ROTATION', mpivot3_eb.name)]
                ))

                ebones2[0].parent = mfoot_eb
                ebones2[1].parent = mrot_eb

                cheel_eb.head += ebones2[2].vector * 0.5
                cheel_eb.tail += ebones2[2].vector * 0.5

                mpivot3_eb.head += ebones2[2].vector * 0.5
                mpivot3_eb.tail += ebones2[2].vector * 0.5

                map_coll['ctr'].assign(ebones2[1])
                map_pbones.append((
                    ebones2[1].name,
                    (0, 0, map_wgt['octahedral']),
                    (),
                    (),
                    []
                ))

                mesh.edit_bones.remove(ebones2[2]) # pivots_heel
                ebones2.pop(2)
                bone_names.pop(-1)


                # 1. Set up ik.
                eb = ebones[-1]

                knee_vector = ebone_get_pole_vector(ebones[0], eb)

                if knee_vector == knee_vector * 0.0:
                    return return_error(
                        f'Fix bone "{ebones[-1].name}" head position.'
                    )

                pole_eb = ebone_new(eb, f'C_pole-', 0.25, parent, 0, 1)
                pole_eb.head += knee_vector
                pole_eb.tail += knee_vector
                pole_eb.roll = 0.0
                map_pbones.append((
                    pole_eb.name,
                    (0, map_bcol['purple'], map_wgt['diamond']),
                    (0, (True,)*3, (True,)*3),
                    (),
                    []
                ))

                line_eb = ebone_new(eb, f'C_line-', 1.0, new_eb, 0, 1) # M_scl-last
                line_eb.head = eb.head
                line_eb.tail = pole_eb.head
                line_eb.roll = 0.0
                line_eb.hide_select = True
                map_pbones.append((
                    line_eb.name,
                    (0, map_bcol['purple'], map_wgt['wire']),
                    ((True,)*3,)*3,
                    (),
                    [('STRETCH_TO', pole_eb.name)]
                ))

                pole_angle = ebone_get_pole_angle(ebones[0], eb, pole_eb)
                map_pbones.append((
                    f'M_ik-{eb.name}',
                    (),
                    (),
                    (),
                    [(
                        'IK',
                        cik_eb.name,
                        ('pole_subtarget', pole_eb.name),
                        ('pole_angle', pole_angle),
                        ('chain_count', len(ebones))
                    )]
                ))

                ebone_setup_tweaks(ebones + ebones2, make_end=False)
                map_pbones.pop(-1) # Remove line if make_end.

                # Helper knee.
#                eb = ebones[-1]

                eb.head = mesh.edit_bones[f'M_ik-{eb.name}'].tail
                eb.tail = mesh.edit_bones[f'M_ik-{eb.name}'].head

                rot_axis = mesh.bones[bone_name].sei_rig.rotation_axis

                map_pbones.pop(-4) # -4;-6 if make_end.
                map_pbones.append((
                    eb.name,
                    (),
                    (),
                    (),
                    [(
                        'COPY_LOCATION',
                        f'T-{ebones2[0].name}'
                    ), (
                        'STRETCH_TO',
                        f'T-{eb.name}'
                    ), (
                        'TRANSFORM',
                        f'M_ik-{eb.name}',
                        ('target_space', 'LOCAL'),
                        ('owner_space', 'LOCAL'),
                        ('map_from', 'ROTATION'),
                        ('map_to', 'ROTATION'),

                        ('from_min_' + rot_axis + '_rot', -3.141592) \
                        if pole_angle > 0.0 else \
                        ('from_max_' + rot_axis + '_rot', 3.141592),

                        ('to_min_' + rot_axis + '_rot', -0.1570796) \
                        if pole_angle > 0.0 else \
                        ('to_max_' + rot_axis + '_rot', 0.1570796)
                    )]
                ))

                ### Pose mode.
                bpy.ops.object.mode_set(mode='POSE')

                pbone_clear_constraints(bone_names)
                pbone_setup_map(map_pbones) # Clears map_pbones.

                # 2. Set up ik.
                for name in bone_names[:-2]:
                    pb = obj.pose.bones[f'M_ik-{name}']

                    pb.ik_stretch = 0.1

                    if name != bone_names[-1]:
                        continue

                    if rot_axis == 'x':
                        pb.lock_ik_y = True
                        pb.lock_ik_z = True
                    else:
                        pb.lock_ik_y = True
                        pb.lock_ik_x = True

                del bone_names, ebones, \
                root_eb, parent, eb, new_eb, cik_eb, \
                knee_vector, pole_eb, line_eb, pole_angle, \
                cpivot0_eb, cheel_eb, mpivot1_eb, mpivot2_eb, \
                mpivot3_eb, mpivot4_eb, mfoot_eb, mrot_eb
                rot_axis, name, pb

                print_time(f'Generated {rig_type}:')
                continue

        ###########################
        # 1. Finalize.

        bpy.ops.object.mode_set(mode=active_mode)

#        # Refresh properties UI to display changes (bone collections).
#        [a.tag_redraw() for a in context.screen.areas if a.type == 'PROPERTIES']

        self.report({'INFO'}, f'Successfully updated: "{obj.name}" {time.time() - start_time:.3f} seconds')

        return {'FINISHED'}

class SEI_RIG_OT_armature_metarig_add(SeiOperator, Operator):
    bl_idname = 'sei_rig.armature_metarig_add'
    bl_label = 'Sei Human (Meta-Rig)'
    bl_description = 'Add an armature object to the scene'

    def execute(self, context):

#        def armature_get_data(obj):
#            if obj.type != 'ARMATURE':
#                return

#            # Clear console.
#            from os import system
#            system('cls')

#            mesh = obj.data

#            active_mode = obj.mode
#            bpy.ops.object.mode_set(mode='EDIT')

#            # Edit.
#            for eb in obj.data.edit_bones:
#                msg = \
#                f'b = mesh.edit_bones.new("{eb.name}")\n' \
#                f'b.head = {tuple(round(i, 3) for i in eb.head)}\n' \
#                f'b.tail = {tuple(round(i, 3) for i in eb.tail)}\n' \
#                f'b.roll = {eb.roll}\n'

#                if eb.use_connect:
#                    f'b.use_connect = {eb.use_connect}\n'
#                if eb.parent:
#                    msg += f'b.parent = mesh.edit_bones["{eb.parent.name}"]\n'

#                print(msg)

#            # Object.
#            print(f'bpy.ops.object.mode_set(mode="OBJECT")\n')

#            for b in mesh.bones:
#                msg = \
#                f'b = mesh.bones["{b.name}"]\n'

#                if b.sei_rig.rig_type == 'none':
#                    if b.sei_rig.use_connect:
#                        msg += f'b.sei_rig.use_connect = {b.sei_rig.use_connect}\n'
#                    if b.sei_rig.use_tweakless:
#                        msg += f'b.sei_rig.use_tweakless = {b.sei_rig.use_tweakless}\n'

#                elif b.sei_rig.rig_type in ['arm', 'leg', 'finger']:
#                    msg += \
#                    f'b.sei_rig.rig_type = "{b.sei_rig.rig_type}"\n' \
#                    f'b.sei_rig.rotation_axis = "{b.sei_rig.rotation_axis}"\n'

#                else:
#                    msg += \
#                    f'b.sei_rig.rig_type = "{b.sei_rig.rig_type}"\n'

#                print(msg)

#            print([b.name for b in mesh.bones if b.sei_rig.rig_type != "none"])

#            bpy.ops.object.mode_set(mode=active_mode)
#            return None

        ###########################

        # The menu (VIEW3D_MT_armature_add) takes care of it.
#        if context.active_object:
#            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.armature_add()

        obj = context.active_object
        mesh = obj.data

        obj.name = \
        mesh.name = 'MTA-Armature'

#        obj.show_in_front = True
#        obj.display_type = 'WIRE'

        bpy.ops.object.mode_set(mode='EDIT')

        # Remove the default bone.
        mesh.edit_bones.remove(mesh.edit_bones[0])

        b = mesh.edit_bones.new("root")
        b.head = (0.0, 0.0, 0.0)
        b.tail = (0.0, 1.0, 0.0)
        b.roll = 0.0

        b = mesh.edit_bones.new("pelvis")
        b.head = (0.0, 0.0, 1.02)
        b.tail = (0.0, 0.0, 1.12)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["root"]

        b = mesh.edit_bones.new("waist")
        b.head = (0.0, 0.0, 1.12)
        b.tail = (0.0, 0.0, 1.23)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["pelvis"]

        b = mesh.edit_bones.new("stomach")
        b.head = (0.0, 0.0, 1.23)
        b.tail = (0.0, 0.0, 1.33)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["waist"]

        b = mesh.edit_bones.new("chest")
        b.head = (0.0, 0.0, 1.33)
        b.tail = (0.0, 0.0, 1.47)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["stomach"]

        b = mesh.edit_bones.new("neck")
        b.head = (0.0, 0.0, 1.47)
        b.tail = (0.0, 0.0, 1.53)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["chest"]

        b = mesh.edit_bones.new("head")
        b.head = (0.0, 0.0, 1.53)
        b.tail = (0.0, 0.0, 1.69)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["neck"]

        b = mesh.edit_bones.new("clavicle_L")
        b.head = (0.01, 0.0, 1.45)
        b.tail = (0.12, 0.0, 1.45)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["chest"]

        b = mesh.edit_bones.new("uparm_L")
        b.head = (0.12, 0.0, 1.45)
        b.tail = (0.35, 0.01, 1.45)
        b.roll = 3.1415927410125732
        b.parent = mesh.edit_bones["clavicle_L"]

        b = mesh.edit_bones.new("lowarm_L")
        b.head = (0.35, 0.01, 1.45)
        b.tail = (0.58, 0.0, 1.45)
        b.roll = 3.1415927410125732
        b.parent = mesh.edit_bones["uparm_L"]

        b = mesh.edit_bones.new("hand_L")
        b.head = (0.58, 0.0, 1.45)
        b.tail = (0.68, 0.0, 1.45)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["lowarm_L"]

        b = mesh.edit_bones.new("thumb1_L")
        b.head = (0.6, -0.04, 1.435)
        b.tail = (0.6, -0.04, 1.39)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["hand_L"]

        b = mesh.edit_bones.new("thumb2_L")
        b.head = (0.6, -0.04, 1.39)
        b.tail = (0.6, -0.04, 1.36)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["thumb1_L"]

        b = mesh.edit_bones.new("thumb3_L")
        b.head = (0.6, -0.04, 1.36)
        b.tail = (0.6, -0.04, 1.332)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["thumb2_L"]

        b = mesh.edit_bones.new("index1_L")
        b.head = (0.67, -0.04, 1.435)
        b.tail = (0.715, -0.04, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["hand_L"]

        b = mesh.edit_bones.new("index2_L")
        b.head = (0.715, -0.04, 1.435)
        b.tail = (0.75, -0.04, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["index1_L"]

        b = mesh.edit_bones.new("index3_L")
        b.head = (0.75, -0.04, 1.435)
        b.tail = (0.78, -0.04, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["index2_L"]

        b = mesh.edit_bones.new("middle1_L")
        b.head = (0.675, -0.015, 1.435)
        b.tail = (0.725, -0.015, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["hand_L"]

        b = mesh.edit_bones.new("middle2_L")
        b.head = (0.725, -0.015, 1.435)
        b.tail = (0.765, -0.015, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["middle1_L"]

        b = mesh.edit_bones.new("middle3_L")
        b.head = (0.765, -0.015, 1.435)
        b.tail = (0.8, -0.015, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["middle2_L"]

        b = mesh.edit_bones.new("ring1_L")
        b.head = (0.67, 0.01, 1.435)
        b.tail = (0.715, 0.01, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["hand_L"]

        b = mesh.edit_bones.new("ring2_L")
        b.head = (0.715, 0.01, 1.435)
        b.tail = (0.75, 0.01, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["ring1_L"]

        b = mesh.edit_bones.new("ring3_L")
        b.head = (0.75, 0.01, 1.435)
        b.tail = (0.78, 0.01, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["ring2_L"]

        b = mesh.edit_bones.new("pinky1_L")
        b.head = (0.665, 0.035, 1.435)
        b.tail = (0.7, 0.035, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["hand_L"]

        b = mesh.edit_bones.new("pinky2_L")
        b.head = (0.7, 0.035, 1.435)
        b.tail = (0.725, 0.035, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["pinky1_L"]

        b = mesh.edit_bones.new("pinky3_L")
        b.head = (0.725, 0.035, 1.435)
        b.tail = (0.75, 0.035, 1.435)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["pinky2_L"]

        b = mesh.edit_bones.new("clavicle_R")
        b.head = (-0.01, 0.0, 1.45)
        b.tail = (-0.12, 0.0, 1.45)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["chest"]

        b = mesh.edit_bones.new("uparm_R")
        b.head = (-0.12, 0.0, 1.45)
        b.tail = (-0.35, 0.01, 1.45)
        b.roll = -3.1415929794311523
        b.parent = mesh.edit_bones["clavicle_R"]

        b = mesh.edit_bones.new("lowarm_R")
        b.head = (-0.35, 0.01, 1.45)
        b.tail = (-0.58, 0.0, 1.45)
        b.roll = -3.1415929794311523
        b.parent = mesh.edit_bones["uparm_R"]

        b = mesh.edit_bones.new("hand_R")
        b.head = (-0.58, 0.0, 1.45)
        b.tail = (-0.68, 0.0, 1.45)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["lowarm_R"]

        b = mesh.edit_bones.new("thumb1_R")
        b.head = (-0.6, -0.04, 1.435)
        b.tail = (-0.6, -0.04, 1.39)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["hand_R"]

        b = mesh.edit_bones.new("thumb2_R")
        b.head = (-0.6, -0.04, 1.39)
        b.tail = (-0.6, -0.04, 1.36)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["thumb1_R"]

        b = mesh.edit_bones.new("thumb3_R")
        b.head = (-0.6, -0.04, 1.36)
        b.tail = (-0.6, -0.04, 1.332)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["thumb2_R"]

        b = mesh.edit_bones.new("index1_R")
        b.head = (-0.67, -0.04, 1.435)
        b.tail = (-0.715, -0.04, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["hand_R"]

        b = mesh.edit_bones.new("index2_R")
        b.head = (-0.715, -0.04, 1.435)
        b.tail = (-0.75, -0.04, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["index1_R"]

        b = mesh.edit_bones.new("index3_R")
        b.head = (-0.75, -0.04, 1.435)
        b.tail = (-0.78, -0.04, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["index2_R"]

        b = mesh.edit_bones.new("middle1_R")
        b.head = (-0.675, -0.015, 1.435)
        b.tail = (-0.725, -0.015, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["hand_R"]

        b = mesh.edit_bones.new("middle2_R")
        b.head = (-0.725, -0.015, 1.435)
        b.tail = (-0.765, -0.015, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["middle1_R"]

        b = mesh.edit_bones.new("middle3_R")
        b.head = (-0.765, -0.015, 1.435)
        b.tail = (-0.8, -0.015, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["middle2_R"]

        b = mesh.edit_bones.new("ring1_R")
        b.head = (-0.67, 0.01, 1.435)
        b.tail = (-0.715, 0.01, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["hand_R"]

        b = mesh.edit_bones.new("ring2_R")
        b.head = (-0.715, 0.01, 1.435)
        b.tail = (-0.75, 0.01, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["ring1_R"]

        b = mesh.edit_bones.new("ring3_R")
        b.head = (-0.75, 0.01, 1.435)
        b.tail = (-0.78, 0.01, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["ring2_R"]

        b = mesh.edit_bones.new("pinky1_R")
        b.head = (-0.665, 0.035, 1.435)
        b.tail = (-0.7, 0.035, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["hand_R"]

        b = mesh.edit_bones.new("pinky2_R")
        b.head = (-0.7, 0.035, 1.435)
        b.tail = (-0.725, 0.035, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["pinky1_R"]

        b = mesh.edit_bones.new("pinky3_R")
        b.head = (-0.725, 0.035, 1.435)
        b.tail = (-0.75, 0.035, 1.435)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["pinky2_R"]

        b = mesh.edit_bones.new("upleg_L")
        b.head = (0.1, 0.0, 1.0)
        b.tail = (0.1, -0.01, 0.65)
        b.roll = 1.5707966089248657
        b.parent = mesh.edit_bones["pelvis"]

        b = mesh.edit_bones.new("lowleg_L")
        b.head = (0.1, -0.01, 0.65)
        b.tail = (0.1, 0.0, 0.06)
        b.roll = 1.5707966089248657
        b.parent = mesh.edit_bones["upleg_L"]

        b = mesh.edit_bones.new("foot_L")
        b.head = (0.1, 0.0, 0.06)
        b.tail = (0.1, -0.13, 0.02)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["lowleg_L"]

        b = mesh.edit_bones.new("toe_L")
        b.head = (0.1, -0.13, 0.02)
        b.tail = (0.1, -0.23, 0.02)
        b.roll = 1.5707963705062866
        b.parent = mesh.edit_bones["foot_L"]

        b = mesh.edit_bones.new("pivots_heel_L")
        b.head = (0.05, 0.0, 0.0)
        b.tail = (0.15, 0.0, 0.0)
        b.roll = 1.570796251296997
        b.parent = mesh.edit_bones["toe_L"]

        b = mesh.edit_bones.new("upleg_R")
        b.head = (-0.1, 0.0, 1.0)
        b.tail = (-0.1, -0.01, 0.65)
        b.roll = -1.5707966089248657
        b.parent = mesh.edit_bones["pelvis"]

        b = mesh.edit_bones.new("lowleg_R")
        b.head = (-0.1, -0.01, 0.65)
        b.tail = (-0.1, 0.0, 0.06)
        b.roll = -1.5707966089248657
        b.parent = mesh.edit_bones["upleg_R"]

        b = mesh.edit_bones.new("foot_R")
        b.head = (-0.1, 0.0, 0.06)
        b.tail = (-0.1, -0.13, 0.02)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["lowleg_R"]

        b = mesh.edit_bones.new("toe_R")
        b.head = (-0.1, -0.13, 0.02)
        b.tail = (-0.1, -0.23, 0.02)
        b.roll = -1.5707963705062866
        b.parent = mesh.edit_bones["foot_R"]

        b = mesh.edit_bones.new("pivots_heel_R")
        b.head = (-0.15, 0.0, 0.0)
        b.tail = (-0.05, 0.0, 0.0)
        b.roll = -1.570796251296997
        b.parent = mesh.edit_bones["toe_R"]

        bpy.ops.object.mode_set(mode="OBJECT")

        b = mesh.bones["root"]

        b = mesh.bones["pelvis"]
        b.sei_rig.rig_type = "spine"

        b = mesh.bones["waist"]
        b.sei_rig.use_connect = True

        b = mesh.bones["stomach"]
        b.sei_rig.use_connect = True

        b = mesh.bones["chest"]
        b.sei_rig.use_connect = True

        b = mesh.bones["neck"]
        b.sei_rig.rig_type = "head"

        b = mesh.bones["head"]
        b.sei_rig.use_connect = True

        b = mesh.bones["clavicle_L"]
        b.sei_rig.use_tweakless = True

        b = mesh.bones["uparm_L"]
        b.sei_rig.rig_type = "arm"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["lowarm_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["hand_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["thumb1_L"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["thumb2_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["thumb3_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["index1_L"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["index2_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["index3_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["middle1_L"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["middle2_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["middle3_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["ring1_L"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["ring2_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["ring3_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["pinky1_L"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["pinky2_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["pinky3_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["clavicle_R"]
        b.sei_rig.use_tweakless = True

        b = mesh.bones["uparm_R"]
        b.sei_rig.rig_type = "arm"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["lowarm_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["hand_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["thumb1_R"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["thumb2_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["thumb3_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["index1_R"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["index2_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["index3_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["middle1_R"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["middle2_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["middle3_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["ring1_R"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["ring2_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["ring3_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["pinky1_R"]
        b.sei_rig.rig_type = "finger"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["pinky2_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["pinky3_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["upleg_L"]
        b.sei_rig.rig_type = "leg"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["lowleg_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["foot_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["toe_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["pivots_heel_L"]
        b.sei_rig.use_connect = True

        b = mesh.bones["upleg_R"]
        b.sei_rig.rig_type = "leg"
        b.sei_rig.rotation_axis = "z"

        b = mesh.bones["lowleg_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["foot_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["toe_R"]
        b.sei_rig.use_connect = True

        b = mesh.bones["pivots_heel_R"]
        b.sei_rig.use_connect = True

        for name in [
            'pelvis', 'neck', 'uparm_L', 'thumb1_L', 'index1_L',
            'middle1_L', 'ring1_L', 'pinky1_L', 'uparm_R', 'thumb1_R',
            'index1_R', 'middle1_R', 'ring1_R', 'pinky1_R', 'upleg_L',
            'upleg_R'
        ]:
            b = mesh.bones[name]

            b.color.palette = 'CUSTOM'
            b.color.custom.normal = (0.96, 0.26, 0.57) # pink
            b.color.custom.select = (0.6, 0.9, 1.0)
            b.color.custom.active = (0.7, 1.0, 1.0)

        return {'FINISHED'}

######### OT Bone Tools

def bone_parent_or_unparent(context, parent):

    active_mode = context.object.mode
    bpy.ops.object.mode_set(mode='EDIT') # ".parent" only in edit_bones.

    active_bone = context.active_bone

    if active_bone.parent in context.selected_editable_bones:
        active_bone.parent = None

    for bone in context.selected_editable_bones:
        # "Bone".parent = "Bone" does not produce an error.
        bone.parent = active_bone if parent else None

    bpy.ops.object.mode_set(mode=active_mode)

    return {'FINISHED'}

class SEI_RIG_OT_bone_parent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_parent'
    bl_label = 'Assign Parent'
    bl_description = 'Assign parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=True)

class SEI_RIG_OT_bone_unparent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_unparent'
    bl_label = 'Remove Parent'
    bl_description = 'Remove parent on the selected bones'

    def execute(self, context):
        return bone_parent_or_unparent(context, parent=False)

class SEI_RIG_OT_bone_select_children_recursive(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_select_children_recursive'
    bl_label = 'Select Children Recursive'
    bl_description = 'Select child bones recursively on the active bone'

    def execute(self, context):

        for bone in context.active_bone.children_recursive:
            bone.select = True

            if context.mode == 'EDIT_ARMATURE':
                bone.select_head = bone.select_tail = True

        return {'FINISHED'}

class SEI_RIG_OT_bone_tail_to_head_parent(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_tail_to_head_parent'
    bl_label = 'Tail (Parent) to Head'
    bl_description = 'Move parent tail to child head on the selected bones'

    def execute(self, context):

        active_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        bones = context.selected_editable_bones

        for bone in bones:
            if bone.parent in bones:
                bone.parent.tail = bone.head

        bpy.ops.object.mode_set(mode=active_mode)

        return {'FINISHED'}

class SEI_RIG_OT_bone_align_roll_to_axis(SeiOperator, Operator):
    bl_idname = 'sei_rig.bone_align_roll_to_axis'
    bl_label = 'Align Roll'
    bl_description = 'Align the selected bone(s) roll to the indicated axis'

    def execute(self, context):

        # https://github.com/blender/blender-addons/blob/main/rigify/utils/bones.py
        # TODO: Import original functions?
        def ebones_get_chain_axis(first_ebone, last_ebone, axis='x'):
            """
            Compute the axis of all bones to be perpendicular
            to the primary plane in which the bones lie.
            Must be in edit mode.
            """
            if not isinstance(first_ebone, bpy.types.EditBone):
                return

            # Compute normal to the plane defined by the first bone,
            # and the end of the lsat bone in the chain.

            chain_y_axis = last_ebone.tail - first_ebone.head
            chain_rot_axis = first_ebone.y_axis.cross(chain_y_axis)

            if chain_rot_axis.length < first_ebone.length / 100:
                return getattr(first_ebone, axis + "_axis").normalized()
            else:
                return chain_rot_axis.normalized()

        def ebone_align_axis(ebone, vector, axis='x'):
            """
            Rolls the bone to align its axis as closely as possible to
            the given vector.
            Must be in edit mode.
            """
            if not isinstance(ebone, bpy.types.EditBone):
                return

            if axis == 'x':
                aux_axis = 'z'
                vector = vector.cross(ebone.y_axis) # mathutils.Vector(vector)
            else: # axis == 'z'
                aux_axis = 'x'
                vector = ebone.y_axis.cross(vector)

            dot = max(-1.0, min(1.0, getattr(ebone, aux_axis + '_axis').dot(vector)))
            angle = acos(dot) # math.acos(dot)

            ebone.roll += angle
            dot1 = getattr(ebone, aux_axis + '_axis').dot(vector)

            ebone.roll -= angle * 2.0
            dot2 = getattr(ebone, aux_axis + '_axis').dot(vector)

            if dot1 > dot2:
                ebone.roll += angle * 2.0

        vars = context.active_object.data.sei_rig

        active_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        bones = context.selected_editable_bones

        for bone in bones:
            ebone_align_axis(
                bone,
                ebones_get_chain_axis(bones[0], bones[-1], vars.bone_rot_axis), # axis
                vars.bone_rot_axis
            )

        bpy.ops.object.mode_set(mode=active_mode)

        return {'FINISHED'}

######### PT

class SEI_RIG_PT_rig_tools(SeiPanel, Panel):
    bl_idname = 'SEI_RIG_PT_rig_tools'
    bl_label = ' Rig Tools'

    def draw_header(self, context):
        self.layout.operator('wm.url_open', text='', icon='HELP').url = 'seilotte.github.io'

    def draw(self, context):
        layout = self.layout

        obj = context.active_object

        # Since "bpy.types.Armatures.sei_rig", we need to do this checks.
        # It is also convinient for operators.
        if not obj or obj.type != 'ARMATURE':
            layout.label(text='No active armature.', icon='ERROR')
            return

        vars = obj.data.sei_rig

        # Generate button.
        col = layout.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False # No animation.

        col.operator(
            'sei_rig.generate',
            text = 'Re-Generate Rig' if vars.target_rig else 'Generate Rig',
            icon = 'FILE_REFRESH' if vars.target_rig else 'POSE_HLT'
        )
        col.prop(vars, 'target_rig', text='Target Rig:') # ARMATURE_DATA

        # Options.
        box = layout.box()
        box.label(text='Options:')

        bone = context.active_bone

        if bone is None:
            box.label(text='No Active Bone', icon='INFO')

        elif context.mode != 'POSE':
            box.label(text='Not Pose Mode', icon = 'INFO')

        else:
            col = box.column(align=True)
            col.use_property_split = True
            col.use_property_decorate = False # No animation.

            col.prop(bone.sei_rig, 'rig_type')

            if bone.sei_rig.rig_type == 'none':
                col = col.column(align=True)
                col.enabled = True if bone.parent else False
                col.prop(bone.sei_rig, 'use_connect')
                col.prop(bone.sei_rig, 'use_tweakless')

            elif bone.sei_rig.rig_type == 'tweak':
                col.prop(bone.sei_rig, 'use_average')
                col.prop(bone.sei_rig, 'bbone_segments')

            elif bone.sei_rig.rig_type == 'spine':
                col.prop(bone.sei_rig, 'spine_pivot_index')

            elif bone.sei_rig.rig_type in ['arm', 'finger', 'leg']:
                col.row().prop(bone.sei_rig, 'rotation_axis', expand=True)

        # Subpanel Bone Tools.
        header, panel = layout.panel('SEI_RIG_PT_bone_tools')
        header.label(text='Bone Tools', icon='BONE_DATA')

        if panel:
            if bone is None:
                panel.label(text='No Active Bone', icon='INFO')

            elif context.mode not in ['EDIT_ARMATURE', 'POSE']:
                panel.label(text='Not Pose/Edit Mode', icon='INFO')

            else:
                panel.operator(
                    'sei_rig.bone_select_children_recursive',
                    text='Select Children [All]'
                ) # GROUP_BONE

                panel.separator()

                row = panel.row(align=True)
                row.operator('sei_rig.bone_parent', text='Parent')
                row.operator('sei_rig.bone_unparent', text='Unparent')

                panel.operator('sei_rig.bone_tail_to_head_parent') # BONE_DATA

                row = panel.split(align=True, factor=0.7)
                row.operator('sei_rig.bone_align_roll_to_axis', icon='EMPTY_ARROWS')
                row.prop(vars, 'bone_rot_axis', text='')

                panel.separator()

                col = panel.column_flow(columns=2)
                col.prop(bone, 'use_connect')
                col.prop(bone, 'use_deform')
                col.prop(obj.data, 'show_axes', text='Axes')
                col.prop(obj.data, 'show_names', text='Name')

def SEI_RIG_armature_add_menu_draw(self, context):
    self.layout.operator('sei_rig.armature_metarig_add', icon='OUTLINER_OB_ARMATURE')

#===========================

classes = [
    SEI_RIG_variables,
    SEI_RIG_variables_bones,

    # Main UI
    SEI_RIG_OT_generate,
    SEI_RIG_OT_armature_metarig_add,

    SEI_RIG_OT_bone_parent,
    SEI_RIG_OT_bone_unparent,
    SEI_RIG_OT_bone_select_children_recursive,
    SEI_RIG_OT_bone_tail_to_head_parent,
    SEI_RIG_OT_bone_align_roll_to_axis,

    SEI_RIG_PT_rig_tools,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Armature.sei_rig = PointerProperty(type=SEI_RIG_variables)
    bpy.types.Bone.sei_rig = PointerProperty(type=SEI_RIG_variables_bones)

    cls = bpy.types.VIEW3D_MT_armature_add
    if not hasattr(cls.draw, '_draw_funcs') \
    or not any(f.__name__ == 'SEI_RIG_armature_add_menu_draw' for f in cls.draw._draw_funcs):
        cls.append(SEI_RIG_armature_add_menu_draw)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Armature.sei_rig
    del bpy.types.Bone.sei_rig

    bpy.types.VIEW3D_MT_armature_add.remove(SEI_RIG_armature_add_menu_draw)

if __name__ == "__main__": # debug; live edit
    register()