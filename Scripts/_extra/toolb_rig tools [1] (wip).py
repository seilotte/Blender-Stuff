# Convert to functions and import normally when it is done.
# Passed "self", "context" from dictionary.

'''
1. Remove old target armature.
1. [OBJECT MODE] Create new armature.
-. Set parameters.
1. Create sei_rig_id property.
1. Check that bones exist.
1. Create widgets.

2. Create bone collections.
2. [EDIT MODE] Save ebones.use_connect. // Prevents issues.
-. Rig types utils. // Create bones, assign to collections, assign bone colours, shapes...
2. Rig types;[EDIT MODE] [POSE MODE] -> Per rig type.
2. [EDIT MODE] Restore ebones.use_connect.

3. [POSE MODE] Rotation mode to XYZ.


Prefixes meanings:
    MTA- = Metarig  // "Unmodified"/Original armature.
    RIG- = Rig      // Armature with all the "rig" bones.

    C- = CTR- = Controllers
    M- = MCH- = Mechanical; M_fk-
    H- = HLP- = Helpers
    T- = TWK- = Tweaks; T_end- = Tweak, end of chain.
    W- = WGT- = Widgets

Code meanings:
    map_[var] = mappping_[variables]
    map_wgt = sei_widgets_mapping
    map_bcol = sei_bone_colours_mapping
    ebone = edit_bone
    pbone = pose_bone
'''

import bpy
import bmesh
import time

from mathutils import Matrix # setup_pose_bones(), head_rig
from math import acos # ebone_align_axis()

###########################
# Utils.

def create_mesh(name='Mesh', vertices=None, edges=None, faces=None):
    obj = bpy.data.objects.get(name)

    if not obj and vertices and edges:
        mesh = bpy.data.meshes.new(name=name)

        bm = bmesh.new()
        verts = [bm.verts.new((x, y, z)) for x, y, z in vertices]

        for edge_index in edges:
            bm.edges.new([verts[i] for i in edge_index])

#        for face_index in faces:
#            bm.faces.new([verts[i] for i in face_index])

#        # Clear faces, keep edges and vertices.
#        for face in bm.faces:
#            bm.faces.remove(face)

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)

    return obj

#def create_mesh_get_data(mesh):
#    '''
#    Debug function to get lists for "create_mesh()" from an object/mesh.
#    Prints vertices and edges lists.
#    '''
#    vertices = [(round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3)) for v in mesh.vertices]

#    edges = []
#    for edge in mesh.edges:
#        edges.append(list(edge.vertices))

#    print(f'\nvertices = {vertices},\nedges = {edges}')

##    faces = []
##    for face in mesh.polygons:
##        faces.append(list(face.vertices))

##    print(f'\nvertices = {vertices},\nfaces = {faces}')


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

#########

# https://github.com/blender/blender-addons/blob/main/rigify/utils/bones.py
# TODO: Import original funcitons?
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

def bones_get_pole_angle(bone, ik_bone, target_bone):
    ''' Credit: https://blender.stackexchange.com/questions/19754/how-to-set-calculate-pole-angle-of-ik-constraint-so-the-chain-does-not-move
        Assume pose_bones or edit_bones. '''

    if isinstance(bone, bpy.types.EditBone):
        pole_normal = (ik_bone.tail - bone.head).cross(target_bone.head - bone.head)
    else:
        bone = bone.bone                # First bone; Last boen of the ik chain.
        ik_bone = ik_bone.bone          # Last bone; Bone with the ik constraint.
        target_bone = target_bone.bone  # Pole target bone.

        pole_normal (ik_bone.tail_local - bone.head_local).cross(target_bone.head_local - bone.head_local)

    projected_pole_axis = pole_normal.cross(bone.vector)

    # Normal specifies the orientation; normal = bone.vector = bone.tail - bone.head
    angle = bone.x_axis.angle(projected_pole_axis)

    if bone.x_axis.cross(projected_pole_axis).angle(bone.vector) < 1:
        angle = -angle

#    print(round(angle * 57.2957795131, 3)) # debug

    return angle


###########################
# Main function.

def sei_generate_rig():

    start_time = time.time()

    def print_time(string):
        print(f'{string} {time.time() - start_time:.3f} seconds.')

    # We have already checked if the object exists, is armature, sei_collection exists,
    # check SEI_RIG_PT_rig_tools for more details.
    vars = context.active_object.data.sei_rig_variables

    ###########################
    # 1. Remove old target armature.
    if vars.target_rig: # Check SEI_RIG_OT_generate for more details.
        bpy.data.armatures.remove(vars.target_rig, do_unlink=True)

    active_mode = context.active_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # 1. Create new armature.
    # NOTE: I had issues when creating edit bones without .select_set() and
    # view_layer.object.active; I was using .copy().
    org_obj = context.active_object

    for layer_obj in context.view_layer.objects:
        layer_obj.select_set(False)

    org_obj.select_set(True)
    context.view_layer.objects.active = org_obj

    # Makes the dup active, assigns to collections. Needs object mode.
    bpy.ops.object.duplicate()

    org_obj.hide_viewport = org_obj.hide_render = True

    #########
    # Set object paramaters.
    obj = context.active_object # Object data.
    mesh = obj.data # Mesh/Armature data.

    if org_obj.name.startswith('MTA-'):
        obj.name = org_obj.name.replace('MTA-', 'RIG-')
    else:
        obj.name = f'RIG-{org_obj.name}' if not org_obj.name.startswith('RIG-') else org_obj.name

    mesh.name = obj.name

    obj.display_type = 'WIRE'
    obj.show_in_front = True
    mesh.display_type = 'OCTAHEDRAL' # WIRE;STICK;OCTAHEDRAL;BBONE;ENVELOPE

    mesh.sei_rig_variables.collections.clear() # Clear sei collections.
    vars.target_rig = mesh

    ###########################
    # 1. Create sei_rig_id property.
    if not mesh.get('sei_rig_id'):
        mesh['sei_rig_id'] = obj.name

    ###########################
    # 1. Check that bones exist; This is convinient for preveneting undesired behavior.
    missing_sei_bones = [
        f'{collection.name}: "{sei_bone.name}"'
        for collection in vars.collections
        for sei_bone in collection.bones
        if not mesh.bones.get(sei_bone.name)
    ]

    if missing_sei_bones:
        # TODO: Use raise ValueError() in order to use Try Except.
        self.report({'ERROR'}, f'Stopping... Bones not found. Remove or update them: \n{", ".join(missing_sei_bones)}')
        return

    del missing_sei_bones

    ###########################
    # 1. Widgets, create meshes.
    plane = create_mesh( # Returns obj.
        name = 'WGT-Plane',
        vertices = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (-0.5, 0.5, 0.0), (0.5, 0.5, 0.0)],
        edges = [[2, 0], [0, 1], [1, 3], [3, 2]]
    )
    cube = create_mesh(
        name = 'WGT-Cube',
        vertices = [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)],
        edges = [[2, 0], [0, 1], [1, 3], [3, 2], [6, 2], [3, 7], [7, 6], [4, 6], [7, 5], [5, 4], [0, 4], [5, 1]]
    )
    diamond = create_mesh(
        name = 'WGT-Diamond',
        vertices = [(-0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.5, 0.0, 0.0), (0.0, -0.5, 0.0), (0.0, 0.0, -0.5), (0.0, 0.0, 0.5)],
        edges = [[3, 0], [0, 4], [4, 3], [5, 0], [3, 5], [0, 1], [1, 4], [5, 1], [4, 2], [2, 3], [2, 5], [1, 2]]
    )
    diamond_arrows = create_mesh(
        name = "WGT-Diamond_arrows",
        vertices = [(-0.25, 0.0, 0.0), (0.0, 0.0, -0.25), (0.25, 0.0, 0.0), (0.0, 0.0, 0.25), (0.0, -0.25, 0.0), (0.0, 0.25, 0.0), (1.5, 0.25, -0.5), (2.0, 0.25, 0.0), (1.5, 0.25, 0.5), (-2.0, 0.25, 0.0), (-1.5, 0.25, -0.5), (-1.5, 0.25, 0.5)],
        edges = [[0, 4], [4, 3], [3, 0], [3, 5], [5, 0], [0, 1], [1, 4], [5, 1], [2, 3], [4, 2], [2, 5], [1, 2], [7, 8], [6, 7], [11, 9], [9, 10], [5, 7], [5, 9]]
    )
    line = create_mesh(
        name = 'WGT-Line',
        vertices = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        edges = [[0, 1]]
    )
    wireframe = create_mesh(
        name = 'WGT-Wire',
        vertices = [(-0.05, 0.0, 0.0), (0.0, 0.05, 0.0), (0.05, 0.0, 0.0), (0.0, -0.05, 0.0), (0.0, 0.0, -0.05), (0.0, 0.0, 0.05), (-0.1, 0.1, -0.1), (0.0, 1.0, 0.0), (0.1, 0.1, 0.1), (0.0, 0.0, 0.0), (0.1, 0.1, -0.1), (-0.1, 0.1, 0.1), (-0.05, 1.0, 0.0), (0.0, 1.05, 0.0), (0.05, 1.0, 0.0), (0.0, 0.95, 0.0), (0.0, 1.0, -0.05), (0.0, 1.0, 0.05)],
        edges = [[3, 0], [0, 4], [4, 3], [5, 0], [3, 5], [0, 1], [1, 4], [5, 1], [4, 2], [2, 3], [2, 5], [1, 2], [9, 6], [6, 10], [10, 9], [11, 6], [9, 11], [6, 7], [7, 10], [11, 7], [10, 8], [8, 9], [8, 11], [7, 8], [15, 12], [12, 16], [16, 15], [17, 12], [15, 17], [12, 13], [13, 16], [17, 13], [16, 14], [14, 15], [14, 17], [13, 14]]
    )

    # Widgets, TODO: Don't create all meshes.
    map_wgt = { # map_wgt = sei_widgets_mapping; Same as bone_shapes in SEI_RIG_variables_collection_item.
        'none': None, # .get does this.
        'plane': plane,
        'cube': cube,
        'diamond': diamond,
        'diamond_arrows': diamond_arrows,
        'line': line,
        'wireframe': wireframe,
    }
    del plane, cube, diamond, diamond_arrows, line, wireframe

    # Widgets, create collection, hide it and link objects.
#    wgt_collection = bpy.data.collections.get(f'WGT {org_obj.name}')
    wgt_collection = bpy.data.collections.get(f'WGT Widgets')

    if not wgt_collection:
#        wgt_collection = bpy.data.collections.new(f'WGT {org_obj.name}')
        wgt_collection = bpy.data.collections.new(f'WGT Widgets')
        find_object_collection(obj).children.link(wgt_collection)

    find_layer_collection(wgt_collection).exclude = True

    for widget in map_wgt.values(): # "in" = O(n); .items(), .values()
        if widget is None: continue

        if not wgt_collection.objects.get(widget.name): # "get" or "set()" = O(1).
            wgt_collection.objects.link(widget)

    ###########################
    # 2. Create bone collections.
    # TODO: Use sei collections or adapt it to layers for backward compatibility.
    # https://wiki.blender.org/wiki/Reference/Release_Notes/4.0/Animation_Rigging/Bone_Collections_%26_Colors_Upgrading
    coll_bones = mesh.collections.get('Bones') or mesh.collections.new(name='Bones')

    for bone in mesh.bones:
        coll_bones.assign(bone)

    coll_root = mesh.collections.get('Root') or mesh.collections.new(name='Root')
    coll_ctr = mesh.collections.get('Controllers') or mesh.collections.new(name='Controllers')
    coll_mch = mesh.collections.get('Mechanicals') or mesh.collections.new(name='Mechanicals')
    coll_twk = mesh.collections.get('Tweaks') or mesh.collections.new(name='Tweaks')

    for coll in mesh.collections:
        if coll in [coll_root, coll_ctr]:
            coll.is_visible = True
        else:
            coll.is_visible = True # True for debugging.

    ###########################
    # 2. Save ebone.use_connect.
    # This prevents future issues like pose bones not being found, parenting issues, etc.
    bpy.ops.object.mode_set(mode='EDIT')

    save_ebones_use_connect = set()

    for ebone in mesh.edit_bones:
        if ebone.use_connect:
            save_ebones_use_connect.add(ebone.name)
            ebone.use_connect = False

    #########


    print_time('Preparations completed:')


    ###########################
    # Rig types utils.
    def sei_validate_collection(sei_collection, minimum_bones, maximum_bones):
        if not sei_collection.bones or not minimum_bones <= len(sei_collection.bones) <= maximum_bones:
            self.report({'ERROR'}, f'Expected between {minimum_bones} and {maximum_bones} bone(s) in "{sei_collection.name} - {sei_collection.rig_types}".')
            return False
        return True

    def setup_edit_bones(mesh, ebones_mapping, pbones_mapping):
        ''' Create and set up blender edit bones parameters.

        Note:
            The function requieres that parents in "bone_mapping" are set in the correct order.
            If parent(str): It won't assign a parent that has not been previously specified.
            Parent can be the index of "bones_mapping" or an edit_bone.    

            If use_align(bool): Aligns "new_bone" to "bone" (head, tail, roll),
            else mantains alignment to Y world axis, "length" and adds "bone" location. '''

        # Syntax: ([ebones_data], [pbones_data], [pbones_data_shape], [pbones_data_constraints])
        for i in ebones_mapping:
            bone, prefix, length_percentage, parent, use_align, use_tail = i[0] # i[0] = ebones_data

            new_name = f'{prefix}{bone.name}'

            # Create bone; Align to Y world axis.
            new_bone = mesh.edit_bones.new(new_name)
            new_bone.tail[1] = round(bone.length, 3) * length_percentage

            new_bone.use_deform = False
    #        new_bone.use_deform = new_bone.use_connect = False

            if use_align:
                new_bone.head = bone.head
                new_bone.tail = bone.tail
                new_bone.roll = bone.roll
            else:
                if use_tail:
                    new_bone.head += bone.tail
                    new_bone.tail += bone.tail
                else:
                    new_bone.head += bone.head
                    new_bone.tail += bone.head

            # Assign parent.
            if isinstance(parent, int):
                # We reset the list on every rig type, therefore we can use pbones_mapping.
                # ! Error if parent has not been previously specified in the lists.
                parent = mesh.edit_bones[pbones_mapping[parent][0]]

            new_bone.parent = parent

            # Assign to pose bones list.
            pbones_mapping.append((new_name,) + i[1:])

        return

    def setup_pose_bones(obj, pbones_mapping):
        ''' Read pbones_mapping that was created from setup_edit_bones().
        To assign bone colours, bone shapes and bone constraints.

        Note: We could fill the values with None but... Just type it.
        TODO: Use ebones/pbones.foreach_set() for better perfomance. '''

        # Syntax: (bone_name, [pbones_data], [pbones_data_shape], [pbones_data_constraints])
        for bone_name, pbones_data, pbones_data_shape, pbones_data_constraints in pbones_mapping:
            pbone = obj.pose.bones[bone_name]

            if pbones_data:
                target_collection, bone_colour, lock_loc, lock_rot, lock_scl, = pbones_data

                # Assign to bone collection(s).
                # Note: It can be done in any mode.
                if target_collection:
                    target_collection.assign(pbone)

                if bone_name.startswith(('C-', 'C_')):
                    coll_ctr.assign(pbone)
                elif bone_name.startswith(('M-', 'M_')):
                    coll_mch.assign(pbone)
                elif bone_name.startswith(('T-', 'T_')):
                    coll_twk.assign(pbone)

                # Assign bone colour.
                if bone_colour:
                    pbone.color.palette = 'CUSTOM'
                    pbone.color.custom.normal = bone_colour
                    pbone.color.custom.select = (0.6, 0.9, 1.0)
                    pbone.color.custom.active = (0.7, 1.0, 1.0)

                # Lock transforms.
                if lock_loc:
                    pbone.lock_location = lock_loc
                if lock_rot:
                    pbone.lock_rotation = lock_rot
                    pbone.lock_rotation_w = True
                if lock_scl:
                    pbone.lock_scale = lock_scl


            if pbones_data_shape:
                bone_shape, transform_name, align_data, location, rotation, scale = pbones_data_shape

                pbone.custom_shape = bone_shape

                if transform_name:
                    pbone.custom_shape_transform = obj.pose.bones[transform_name]

                scale = scale if scale else (1.0, 1.0, 1.0)
                location = location if location else (0.0, 0.0, 0.0)
                # In degrees; To radians -> x * (pi/180)
                rotation = tuple(i * 0.01745329251 for i in rotation) if rotation else (0.0, 0.0, 0.0)

                # Syntax: (align_name, use_loc, use_rot, use_scl)
                if align_data:
                    x = pbone.bone
                    y = obj.pose.bones[align_data[0]].bone

                    use_loc, use_rot, use_scl = align_data[1:]

                    if use_scl:
                        scale = tuple(
                            (y.vector.length / x.vector.length) * scale[i]
                            for i in range(3)
                        )
                    if use_loc:
                        location = tuple(
                            (y.head_local[i] + location[i]) - x.head_local[i]
                            for i in range(3)
                        )
                    if use_rot:
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


            # Constraints data/list.
            # Syntax: (type, (attribute, value), (attribute, value)...)
            for constraint_data in pbones_data_constraints:
                new_constraint = pbone.constraints.new(constraint_data[0])

                if hasattr(new_constraint, 'target'):
                    new_constraint.target = obj
                if hasattr(new_constraint, 'pole_target'):
                    new_constraint.pole_target = obj

                for attribute, value in constraint_data[1:]:
                    if hasattr(new_constraint, attribute):
                        setattr(new_constraint, attribute, value)

        return

    def setup_edit_tweak_bones(mesh, map_ebones, map_pbones, ebones, make_end=True, subdiv=0):
        ''' - Needs edit mode.
            - Assumes ebones were aligned, mantained the order (sei_colleciton)
            and have the proper bone_parent (rig_type).
            - Create/Map tweak bones; Connect chains.
            - Parent; Assign constaints. '''

        # Reset lists.
        map_ebones.clear()
#        map_pbones.clear()

        # Create the bones.
        # Subdivide bones; Subdiv = Number_of_Cuts
        subdiv_ebones = []

        for index, ebone in enumerate(ebones):
            subdiv_ebones.append(ebone)

            # map_pbones needs degrees.
#            align_rot = ebone.matrix.to_euler()
            align_rot = tuple(i * 57.2957795131 for i in ebone.matrix.to_euler())

            map_ebones.append((
                (ebone, 'T-', 0.3, ebone.parent, False, False),
                (coll_twk, map_bcol['blue'], False, False, False),
                (map_wgt['diamond'], None, (), None, align_rot, None),
                [],
            ))

            if ebone == ebones[-1]:
                next_ebone_name = f'T_end-{ebone.name}' if make_end else ""
            else:
                next_ebone_name = f'T-{ebones[index+1].name}'

            for i in range(subdiv):
                i += 1

                new_bone = mesh.edit_bones.new(str(i) + ebone.name)

                new_bone.use_deform = False
#                new_bone.use_deform = new_bone.use_connect = False

                new_bone.head = ebone.head
                new_bone.tail = ebone.tail
                new_bone.roll = ebone.roll

                new_bone.parent = ebone.parent

                new_bone.length /= subdiv + 1

                new_bone.head += ebone.vector * (i / (subdiv + 1))
                new_bone.tail += ebone.vector * (i / (subdiv + 1))

                subdiv_ebones.append(new_bone)

                map_ebones.append((
                    (new_bone, 'T-', 0.3, ebone.parent, False, False),
                    (coll_twk, map_bcol['blue2'], False, False, False),
                    (map_wgt['diamond'], None, (), None, align_rot, None),
                    [('COPY_LOCATION', ('subtarget', f'T-{ebone.name}'), ('use_offset', True), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', 1 - (i/(subdiv+1)) )),
                    ('COPY_LOCATION', ('subtarget', next_ebone_name), ('use_offset', True), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', i/(subdiv+1) ))],
                ))

            ebone.length /= subdiv + 1

            if make_end and ebone == ebones[-1]:
                map_ebones.append((
                    (ebone, 'T_end-', 0.3, ebone.parent, False, True),
                    (coll_twk, map_bcol['blue'], False, False, False),
                    (map_wgt['diamond'], None, (), None, align_rot, None),
                    [],
                ))

        setup_edit_bones(mesh, map_ebones, map_pbones)

        # Fix end_tweak, length changed.
        if make_end:
            end_tweak = mesh.edit_bones[f'T_end-{ebones[-1].name}']
            end_tweak.tail = (subdiv_ebones[-1].tail[0], subdiv_ebones[-1].tail[1] + end_tweak.length, subdiv_ebones[-1].tail[2]) 
            end_tweak.head = subdiv_ebones[-1].tail

        # Parent.
        # Assign constraints.
        for index, ebone in enumerate(subdiv_ebones):
            ebone.parent = mesh.edit_bones[f'T-{ebone.name}']

            if ebone == subdiv_ebones[-1]:
                subtarget = end_tweak.name if make_end else ""
            else:
                subtarget = f'T-{subdiv_ebones[index+1].name}'

            map_pbones.append((
                ebone.name,
                (coll_bones, None, False, False, False),
                (),
                [('STRETCH_TO', ('subtarget', subtarget))]
            ))

        return subdiv_ebones

    #########
    # 2. Rig types. IMPORTANT PART.
    map_bcol = { # map_bcol = sei_bone_colour_mapping; pbone.color.custom.normal
        'blue': (0.3, 0.7, 0.9), # (0.1, 0.5, 0.7)
        'blue2': (0.3, 0.9, 0.9),
        'green': (0.1, 0.6, 0.1),
        'pink': (0.96, 0.26, 0.57),
        'purple': (0.9, 0.7, 0.8),
        'red': (1.0, 0.05, 0.1),
        'white': (0.9, 0.9, 0.9),
        'yellow': (1.0, 0.8, 0.1),
    }

    # Explanation: "new_bone_name" from "ebones_data" gets added to **map_pbones**
    # alongside "[pbones_data]" when using *setup_edit_bones()*.
    #
    # Read root rig type for a detailed syntax (lines 451, 488).
    #
    # [Edit mode] Used to create edit bones.
    # Syntax: ([ebones_data], [pbones_data], [pbones_data_shape], [pbones_data_constraints])
    map_ebones = []
    # [Pose mode] Used to assign bone colours, bone shapes and bone constraints.
    # Syntax: (bone_name, [pbones_data], [pbones_data_shape], [pbones_data_constraints])
    map_pbones = []

    for coll_index, coll in enumerate(vars.collections):
        #########
        # Root.
        if coll_index < 1:
            if not sei_validate_collection(coll, 1, 999): return # Min, max items.

            if coll.name.lower() != 'root':
                self.report({'ERROR'}, f'The first collection should be named "Root" or "root".')
                return

            if coll.rig_types != 'none':
                self.report({'ERROR'}, f'The first collection rig type should be set to "None".')
                return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########

            # Create the bones.
            ebone = mesh.edit_bones[coll.bones[0].name]

            # Force mroot to origin.
            ebone.head = (0.0, 0.0, 0.0)

            map_ebones.append((
                # [ebones_data]:
                # bone, prefix, length%, parent(lst_idx or ebone), use_align, use_tail
                (ebone, 'M-', 0.1, ebone, False, False),
                # [pbones_data]:
                # target_collection, bone_colour, lock_loc, lock_rot, lock_scl
                (coll_root, None, (True,)*3, (True,)*3, (True,)*3),
                # [pbones_data_shape]:
                # bone_shape, transform_name, (align_name, use_loc, use_rot, use_scl), location, rotation(degrees), scale
                # (map_wgt[sei_bone.bone_shapes], None, (0, ebone.length * 0.5, 0), None, (0.5, 1.0, 1.0)),
                (),
                # [pbones_data_constraints]:
                # [(type, (attribute, value), (attribute, value)...)]
                [],
            ))

            setup_edit_bones(mesh, map_ebones, map_pbones)

            # Cannot save edit_bone since switching modes.
            mroot_name = map_pbones[0][0]

            # Retarget root children.
            for child_ebone in ebone.children:
                child_ebone.parent = mesh.edit_bones[mroot_name]

            # Parent, align (Y world) bones.
            # Assign bone_col, wgt_shape.
            coll_len = len(coll.bones)

            for index, sei_bone in enumerate(coll.bones):
                bone = mesh.edit_bones[sei_bone.name]

                if index > 0:
                    bone.parent = mesh.edit_bones[coll.bones[index-1].name]

                # Force bone to origin and align to Y world axis.
                bone.head = (0.0, 0.0, 0.0)
                bone.tail = (0.0, (1.0 - index / coll_len) * ebone.length, 0.0)
                bone.roll = 0.0

                map_pbones.append((
                    # bone_name
                    bone.name,
                    # [pbones_data]:
                    # target_collection, bone_colour, lock_loc, lock_rot, lock_scl
                    (coll_root, map_bcol['purple'], False, False, False),
                    # [pbones_data_shape]:
                    # bone_shape, transform_name, (align_name, use_loc, use_rot, use_scl), location, rotation(degrees), scale
                    (
                        map_wgt[sei_bone.bone_shapes],
                        None,
                        (),
                        (0.0, bone.length * 0.5, 0.0),
                        None,
                        (0.5, 1.0, 1.0)
                    ),
                    # [pbones_data_constraints]:
                    # [(type, (attribute, value), (attribute, value)...)]
                    [],
                ))

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            setup_pose_bones(obj, map_pbones)

            print_time(f'Successfully generated root: "{coll.name}"')
            continue

        #########
        # None.
        if not coll.bones or coll.rig_types == 'none':

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            for sei_bone in coll.bones:
                pbone = obj.pose.bones[sei_bone.name]
                pbone.custom_shape = map_wgt[sei_bone.bone_shapes]

#            print(f'Skipping... No bones or rig type found in "{coll.name}"')
            print_time(f'Skipped (no bones) or Assigned shapes: "{coll.name}"')
            continue


        ###########################
        # Tweak.
        elif coll.rig_types == 'tweak':
            if not sei_validate_collection(coll, 1, 999): return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########
            bpy.ops.object.mode_set(mode='EDIT')

            mroot_ebone = mesh.edit_bones[mroot_name]
            ebones = [mesh.edit_bones[sb.name] for sb in coll.bones]

            # Parent, align (tail to head) bones.
            # setup_edit_tweak_bones() needs this.
            previous_bone = None

            for ebone in ebones:
                if not ebone.parent or ebone.parent in ebones:
                    ebone.parent = mroot_ebone

                if previous_bone:
                    previous_bone.tail = ebone.head

                previous_bone = ebone

            ### Tweak bones; map_ebones resets!
            setup_edit_tweak_bones(mesh, map_ebones, map_pbones, ebones)

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            setup_pose_bones(obj, map_pbones)

            print_time(f'Successfully generated tweak: "{coll.name}"')
            continue
        
        #########
        # Tentacle.


        ###########################
        # Head.
        elif coll.rig_types == 'head':
            if not sei_validate_collection(coll, 1, 999): return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########
            bpy.ops.object.mode_set(mode='EDIT')

            mroot_ebone = mesh.edit_bones[mroot_name]
            ebones = [mesh.edit_bones[sb.name] for sb in coll.bones]

            # Create the bones.
            parent = ebones[0].parent if ebones[0].parent else mroot_ebone

            map_ebones.extend((
                (
                    (ebones[0], 'M_rot-', 0.5, parent, False, False),
                    (coll_ctr, None, (True,)*3, (True,)*3, (True,)*3),
                    (),
                    [('COPY_ROTATION', ('subtarget', mroot_name))]
                ),
                (
                    (ebones[0], 'C_head-', 1.0, 0, False, False),
                    (coll_ctr, map_bcol['yellow'], False, False, False),
                    (
                        map_wgt['plane'],
                        f'M_fk-{ebones[-1].name}',
                        (ebones[-1].name, False, True, False),
                        ebones[-1].vector,
                        (-90.0, 0.0, 0.0),
                        None
                    ),
                    [],
                ),
            ))

            subtarget = f'C_head-{ebones[0].name}'
            influence = 1 / len(coll.bones)

            for ebone in ebones:
                parent = 0 if ebone == ebones[0] else -1

                map_ebones.append((
                    (ebone, 'M_fk-', 0.75, parent, False, False),
                    (coll_ctr, map_bcol['pink'], False, False, False),
                    (
                        map_wgt['plane'],
                        None,
                        (ebone.name, False, True, False),
                        None, # ebone.vector if ebone == ebones[-1] else None
                        (-90.0, 0.0, 0.0),
                        None,
                    ),
                    [('COPY_TRANSFORMS', ('subtarget', subtarget), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', influence))],
                ))

            setup_edit_bones(mesh, map_ebones, map_pbones)

            # Parent, align (tail to head) bones.
            previous_bone = None

            for ebone in ebones:
                ebone.parent = mesh.edit_bones[f'M_fk-{ebone.name}']

                if previous_bone:
                    previous_bone.tail = ebone.head

                previous_bone = ebone

            ### Tweak bones; map_ebones resets!
            setup_edit_tweak_bones(mesh, map_ebones, map_pbones, ebones)

            ### Connect to spine.
            # TODO: Make a variable "use_connect"?
            previous_coll = vars.collections[coll_index - 1] # Root ensures there is always a previous collection.
            pbone = None
            align_rot = None

            if previous_coll.rig_types == 'spine':
                # "pivot" variable in memory.
                ebone = mesh.edit_bones[f'M_rot-{ebones[0].name}']
                ebone.parent = mesh.edit_bones[f'C_chest-{previous_coll.bones[pivot].name}']

                ebone = mesh.edit_bones[previous_coll.bones[-1].name]
                ebone.tail = ebones[0].head

                # Re-target/Reset stretch to constraints.
                bpy.ops.object.mode_set(mode='POSE')

                pbone = obj.pose.bones[previous_coll.bones[-1].name]

                for constraint in pbone.constraints:
                    if constraint.type != 'STRETCH_TO':
                        continue

                    subtarget = constraint.subtarget

                    if subtarget and subtarget == f'T_end-{pbone.name}':
                        constraint.subtarget = f'T-{coll.bones[0].name}'

                        # TODO: Avoid multiple bpy.ops.object.mode_set().
                        bpy.ops.object.mode_set(mode='EDIT')
                        mesh.edit_bones.remove(mesh.edit_bones[subtarget])
                        bpy.ops.object.mode_set(mode='POSE')

                    constraint.rest_length = 0.0

                # Fix bone_shapes orientation.
                align_rot = (
                    pbone.bone.matrix_local
                    @ Matrix.Rotation(-1.5707963259, 4, 'X')
                ).to_euler()

                pbone = obj.pose.bones[f'M_fk-{pbone.name}']
                pbone.custom_shape_rotation_euler = align_rot

                pbone = obj.pose.bones[f'C_chest-{previous_coll.bones[pivot].name}']
                pbone.custom_shape_rotation_euler = align_rot

            del previous_coll, pbone, align_rot

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            setup_pose_bones(obj, map_pbones)

            print_time(f'Successfully generated head: "{coll.name}"')
            continue

        #########
        # Torso/Spine.
        elif coll.rig_types == 'spine':
            if not sei_validate_collection(coll, 2, 999): return

            coll_len = len(coll.bones)
            pivot = coll.spine_pivot_index

            if pivot > coll_len - 1:
                self.report({'ERROR'}, f'Expected "Pivot Position {pivot}" to be less than {coll_len} in "{coll.name}".')
                return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########
            bpy.ops.object.mode_set(mode='EDIT')

            mroot_ebone = mesh.edit_bones[mroot_name]
            ebones = [mesh.edit_bones[sb.name] for sb in coll.bones]

            parent = ebones[0].parent if ebones[0].parent else mroot_ebone

            # Create the bones.
            map_ebones.extend((
                (
                    (ebones[pivot], 'C_torso-', 1.25, parent, False, False),
                    (coll_ctr, map_bcol['purple'], False, False, False),
                    (
                        map_wgt['plane'],
                        None,
                        (ebones[pivot].name, False, True, False),
                        None,
                        (-90.0, 0.0, 0.0),
                        None
                    ),
                    [],
                ),
                (
                    (ebones[pivot], 'C_chest-', 1.0, 0, False, False),
                    (coll_ctr, map_bcol['yellow'], False, False, False),
                    (
                        map_wgt['plane'],
                        f'M_pivot-{ebones[-1].name}' if pivot == coll_len-1 else f'M_fk-{ebones[-1].name}',
                        (ebones[-1].name, False, True, False),
                        None,
                        (-90.0, 0.0, 0.0),
                        None
                    ),
                    [],
                ),
                (
                    (ebones[pivot], 'C_hips-', 1.0, 0, False, False),
                    (coll_ctr, map_bcol['yellow'], False, False, False),
                    (
                        map_wgt['plane'],
                        None,
                        (ebones[pivot].name, False, True, False),
                        None,
                        (-90.0, 0.0, 0.0),
                        None
                    ),
                    [],
                ),
                (
                    (ebones[pivot], 'M_pivot-', 0.5, 0, False, False),
                    (coll_mch, None, False, False, False),
                    (),
                    [('COPY_TRANSFORMS', ('subtarget', f'M_pivot_T-{ebones[pivot].name}'), ('influence', 1.0)),
                    ('COPY_TRANSFORMS', ('subtarget', f'M_pivot_B-{ebones[pivot].name}'), ('influence', 0.5))],
                ),
            ))

            for direction in [1, -1]:
                if direction > 0:
                    prefix = 'M_pivot_T-'
                    subtarget = f'C_chest-{ebones[pivot].name}'
                    influence = 1 / (coll_len - pivot)
                else:
                    prefix = 'M_pivot_B-'
                    subtarget = f'C_hips-{ebones[pivot].name}'
                    influence = 1 / pivot

                # range(start, stop, step)
                for index in range(pivot, coll_len if direction > 0 else 0, direction):
                    ebone = ebones[index]

                    if index == pivot: # Map top/bottom bones.
                        map_ebones.append((
                            (ebone, prefix, 0.5, 0, False, False),
                            (coll_mch, None, False, False, False),
                            (),
                            [('COPY_TRANSFORMS', ('subtarget', subtarget), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', influence))],
                        ))
                    else: # Map mch bones.
                        # Parent to previous bone in list "-1".
                        map_ebones.append((
                            (ebone, 'M_fk-', 0.75, -1, False, False),
                            (coll_ctr, map_bcol['pink'], False, False, False),
                            (
                                map_wgt['plane'],
                                None,
                                (ebone.name, False, True, False),
                                None,
                                (-90.0, 0.0, 0.0),
                                None
                            ),
                            [('COPY_TRANSFORMS', ('subtarget', subtarget), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', influence))],
                        ))

            setup_edit_bones(mesh, map_ebones, map_pbones)

            # Parent, align (tail to head) bones.
            previous_bone = None

            for ebone in ebones:
                if mesh.edit_bones.get(f'M_fk-{ebone.name}'):
                    ebone.parent = mesh.edit_bones[f'M_fk-{ebone.name}']
                elif ebone == ebones[pivot]:
                    ebone.parent = mesh.edit_bones[f'M_pivot-{ebone.name}']
                elif ebone == ebones[-1]:
                    ebone.parent = mesh.edit_bones[f'M_pivot_T-{ebone.name}']
                else: # ebone == ebones[0]
                    ebone.parent = mesh.edit_bones[f'M_pivot_B-{ebones[1].name}']

                if previous_bone:
                    previous_bone.tail = ebone.head

                previous_bone = ebone

            ### Tweak bones; map_ebones resets!
            setup_edit_tweak_bones(mesh, map_ebones, map_pbones, ebones)

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            setup_pose_bones(obj, map_pbones)

            print_time(f'Successfully generated spine: "{coll.name}"')
            continue

        #########
        # Arm.
        elif coll.rig_types == 'arm':
            if not sei_validate_collection(coll, 3, 999): return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########
            bpy.ops.object.mode_set(mode='EDIT')

            mroot_ebone = mesh.edit_bones[mroot_name]
            ebones = [mesh.edit_bones[sb.name] for sb in coll.bones]

            # Align (tail to head) bones.
            # Some new bones need this.
            previous_bone = None

            for ebone in ebones:
                if previous_bone:
                    previous_bone.tail = ebone.head

                previous_bone = ebone

            # Align (to axis) if automatic.
            axis = ebones_get_chain_axis(ebones[0], ebones[-2], coll.rotation_axis)

            for ebone in ebones[:-1]:
                ebone_align_axis(ebone, axis, coll.rotation_axis)

            # If auto align extremity; Orient hand.
            # axis is mathutils.Vector()
            axis[:] = ebones[-1].z_axis.x, ebones[-1].z_axis.y, 0.0

            ebone_align_axis(ebones[-1], axis, coll.rotation_axis)

            del axis

            # Create the bones.
            parent = ebones[0].parent if ebones[0].parent else mroot_ebone

            for ebone in ebones[:-1]:
                map_ebones.append((
                    (ebone, 'M-', 0.5, parent if ebone == ebones[0] else -1, True, False),
                    (coll_mch, None, False, False, False),
                    (),
                    [],
                ))

                if ebone != ebones[-2]:
                    continue

                map_ebones.extend((
                    (
                        (ebone, 'C_ik-', 1.0, parent, False, True),
                        (coll_ctr, map_bcol['yellow'], False, False, False),
                        (
                            (map_wgt['plane']),
                            None,
                            (ebones[-1].name, False, True, True),
                            ebones[-1].vector * 0.75,
#                            (0.0, -90.0, 0.0) if abs(ebones[-1].vector.x) > abs(ebones[-1].vector.y) else (0.0, 0.0, -90.0), # x or -x else y or -y
#                            None if coll.rotation_axis == 'x' else (0.0, -90.0, 0.0),
                            (0.0, -90.0, 0.0),
#                            (1.0, 1.5, 0.5) if abs(ebones[-1].vector.x) > abs(ebones[-1].vector.y) else (1.0, 0.5, 1.5)
                            (1.0, 1.5, 0.5)
                        ),
                        [],
                    ),
                    (
                        (ebone, 'C_pole-', 0.3, parent, False, False),
                        (coll_ctr, map_bcol['purple'], False, (True,)*3, (True,)*3),
                        (map_wgt['diamond'], None, (), None, None, None),
                        [],
                    ),
                    (
                        (ebone, 'C_line-', 1.0, parent, False, False),
                        (coll_ctr, map_bcol['purple'], (True,)*3, (True,)*3, (True,)*3),
                        (map_wgt['line'], None, (), None, None, None),
                        [('STRETCH_TO', ('subtarget', f'C_pole-{ebone.name}'))]
                    ),
                    (
                        (ebone, 'M_hel-', 1.0, ebone, True, False),
                        (coll_bones, None, False, False, False),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'M-{ebone.name}'), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', 0.033333))],
                    ),
                ))

            setup_edit_bones(mesh, map_ebones, map_pbones)

            # Parent.
            for ebone in ebones:
                if ebone == ebones[-1]:
                    ebone.parent = mesh.edit_bones[f'C_ik-{ebones[-2].name}']
                else:
                    ebone.parent = mesh.edit_bones[f'M-{ebone.name}']

            # Helper elbow.
            ebone = mesh.edit_bones[f'M_hel-{ebones[-2].name}']

            ebone.head = ebone.tail
            ebone.tail = ebones[-3].tail # Previously aligned.

            # Pole.
            # compute_elbow_vector(); https://github.com/blender/blender-addons/blob/main/rigify/rigs/limbs/limb_rigs.py
            lo_vector = ebones[-2].vector
            tot_vector = ebones[-2].tail - ebones[0].head
            elbow_vector = (lo_vector.project(tot_vector) - lo_vector).normalized() * tot_vector.length

            if elbow_vector == elbow_vector * 0.0:
                self.report({'ERROR'}, f'Fix bone "{ebones[-2].name}" head position.')
                return

            pole_ebone = mesh.edit_bones[f'C_pole-{ebones[-2].name}']

            pole_ebone.head += elbow_vector
            pole_ebone.tail += elbow_vector

            # Pole line.
            ebone = mesh.edit_bones[f'C_line-{ebones[-2].name}']

            ebone.tail = pole_ebone.head
            ebone.parent = mesh.edit_bones[f'M-{ebones[-2].name}']
            ebone.hide_select = True # armature.bones or armature.edit_bones

            # Ik consrtaint; We can duplicate in map_pbones.
            map_pbones.append((
                f'M-{ebones[-2].name}',
                (),
                (),
                [(
                    'IK',
                    ('subtarget', f'C_ik-{ebones[-2].name}'),
                    ('pole_subtarget', pole_ebone.name),
                    ('pole_angle', bones_get_pole_angle(ebones[0], ebones[-2], pole_ebone)),
                    ('chain_count', len(ebones[:-1]))
                )],
            ))

            ### Tweak bones; map_ebones resets!
            setup_edit_tweak_bones(mesh, map_ebones, map_pbones, ebones, make_end=False)

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            setup_pose_bones(obj, map_pbones)

            pbones = [obj.pose.bones[sb.name] for sb in coll.bones]

            # Ik settings.
            for pbone in pbones[:-1]:
                pbone = obj.pose.bones[f'M-{pbone.name}']

                pbone.ik_stretch = 0.1

                if coll.rotation_axis == 'x':
                    pbone.lock_ik_z = True
                else: # rotation_axis == 'z'
                    pbone.lock_ik_x = True

                pbone.lock_ik_y = True

            # Tweaks stretch_to. Hand.
            pbones[-1].constraints.remove(pbones[-1].constraints[0])

            del pbones

            print_time(f'Successfully generated arm: "{coll.name}"')
            continue

        #########
        # Leg.
        elif coll.rig_types == 'leg':
            if not sei_validate_collection(coll, 5, 999): return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########
            bpy.ops.object.mode_set(mode='EDIT')

            mroot_ebone = mesh.edit_bones[mroot_name]
            # For leg rig.
            ebones = [mesh.edit_bones[sb.name] for sb in coll.bones[:-3]]
            # For foot rig; Last 3 bones are: Foot[0] -> Toe[1] -> Heel_Pivots[2]
            ebones2 = [mesh.edit_bones[sb.name] for sb in coll.bones[-3:]]

            # Align (tail to head) bones.
            # Some new bones need this.
            previous_bone = None

            for ebone in ebones + ebones2[:-1]:
                if previous_bone:
                    previous_bone.tail = ebone.head

                previous_bone = ebone

            # Align (to axis) if automatic.
            axis = ebones_get_chain_axis(ebones[0], ebones[-1], coll.rotation_axis)

            for ebone in ebones:
                ebone_align_axis(ebone, axis, coll.rotation_axis)

            # If auto align extremity; Orient foot, toe, heel.
            # axis is mathutils.Vector()
            axis[:] = -ebones2[0].y_axis.x, -ebones2[1].y_axis.y, -0
            axis = axis.cross((0, 0, 1))

            ebone_align_axis(ebones2[0], axis, coll.rotation_axis)
            ebone_align_axis(ebones2[1], -axis, coll.rotation_axis)

            axis[:] = 0, 0, 1

            ebone_align_axis(ebones2[2], axis, coll.rotation_axis)

            del axis

            # Create the bones.
            parent = ebones[0].parent if ebones[0].parent else mroot_ebone

            for ebone in ebones:
                map_ebones.append((
                    (ebone, 'M-', 0.5, parent if ebone == ebones[0] else -1, True, False),
                    (coll_mch, None, False, False, False),
                    (),
                    [],
                ))

                if ebone != ebones[-1]:
                    continue

                map_ebones.extend((
                    (
                        (ebone, 'C_ik-', 1.0, parent, False, True),
                        (coll_ctr, map_bcol['yellow'], False, False, False),
                        (
                            map_wgt['plane'],
                            None,
                            (ebones2[0].name, True, True, True),
                            ebones2[0].vector * 0.75,
                            None if coll.rotation_axis == 'x' else (0.0, -90.0, 0.0),
                            (1.0, 1.5, 0.5)
                        ),
                        [],
                    ),
                    (
                        (ebone, 'C_pole-', 0.3, parent, False, False),
                        (coll_ctr, map_bcol['purple'], False, (True,)*3, (True,)*3),
                        (map_wgt['diamond'], None, (), None, None, None),
                        [],
                    ),
                    (
                        (ebone, 'C_line-', 1.0, parent, False, False),
                        (coll_ctr, map_bcol['purple'], (True,)*3, (True,)*3, (True,)*3),
                        (map_wgt['line'], None, (), None, None, None),
                        [('STRETCH_TO', ('subtarget', f'C_pole-{ebone.name}'))],
                    ),
                    (
                        (ebone, 'M_hel-', 1.0, ebone, True, False),
                        (coll_bones, None, False, False, False),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'M-{ebone.name}'), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL'), ('influence', 0.033333))],
                    ),
                    # Foot rig.
                    (
                        (ebones2[1], 'C_pivot0-', 0.5, -4, False, False), # -4 = C_ik-
                        (coll_ctr, map_bcol['pink'], (True,)*3, False, (True,)*3),
                        (
                            map_wgt['plane'],
                            None,
                            (ebones2[2].name, False, True, False),
                            None,
                            None if coll.rotation_axis == 'x' else (0.0, -90.0, 0.0),
                            None
                        ),
                        [],
                    ),
                    (
                        (ebones2[2], 'C_heel-', 0.5, -1, False, False),
                        (coll_ctr, map_bcol['pink'], (True,)*3, False, (True,)*3),
                        (
                            map_wgt['plane'],
                            None,
                            (ebones2[2].name, False, True, False),
                            None,
                            None if coll.rotation_axis == 'x'else (0.0, -90.0, 0.0),
                            None
                        ),
                        [],
                    ),
                    (
                        (ebones2[2], 'M_pivot1-', 0.5, -2, False, False),
                        (coll_mch, None, False, False, False),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'C_heel-{ebones2[2].name}'), ('use_x', False), ('use_z', False), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL')),
                        ('LIMIT_ROTATION', ('use_limit_y', True), ('min_y', -6.28318530718), ('owner_space', 'LOCAL'))],
                    ),
                    (
                        (ebones2[2], 'M_pivot2-', 0.5, -1, False, True),
                        (coll_mch, None, False, False, False),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'C_heel-{ebones2[2].name}'), ('use_x', False), ('use_z', False), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL')),
                        ('LIMIT_ROTATION', ('use_limit_y', True), ('max_y', 6.28318530718), ('owner_space', 'LOCAL'))],
                    ),
                    (
                        (ebones2[2], 'M_pivot3-', 0.5, -1, False, False),
                        (coll_mch, None, False, False, False),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'C_heel-{ebones2[2].name}'), ('use_y', False), ('use_z', False), ('target_space', 'LOCAL'), ('owner_space', 'LOCAL')),
                        ('LIMIT_ROTATION', ('use_limit_x', True), ('min_x', -6.28318530718), ('owner_space', 'LOCAL'))],
                    ),
                    (
                        (ebones2[1], 'M_pivot4-', 0.5, -1, False, False),
                        (coll_mch, None, False, False, False),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'C_heel-{ebones2[2].name}'), ('target_space', 'POSE'), ('owner_space', 'POSE'))],
                    ),
                    (
                        (ebones2[0], 'M-', 0.5, -1, True, False),
                        (coll_mch, None, False, False, False),
                        (),
                        [],
                    ),
                    (
                        (ebones2[1], 'M_rot-', 0.5, -1, False, False),
                        (coll_ctr, None, (True,)*3, (True,)*3, (True,)*3),
                        (),
                        [('COPY_ROTATION', ('subtarget', f'M_pivot3-{ebones2[2].name}'))],
                    ),
                ))

            setup_edit_bones(mesh, map_ebones, map_pbones)

            # Parent.
            for ebone in ebones:
                ebone.parent = mesh.edit_bones[f'M-{ebone.name}']

            # Helper knee.
            ebone = mesh.edit_bones[f'M_hel-{ebones[-1].name}']

            ebone.head = ebone.tail
            ebone.tail = ebones[-2].tail # Previously aligned.

#            for child in ebones[-1].children:
#                child.parent = ebone

            # Pole.
            # compute_elbow_vector(); https://github.com/blender/blender-addons/blob/main/rigify/rigs/limbs/limb_rigs.py
            lo_vector = ebones[-1].vector
            tot_vector = ebones[-1].tail - ebones[0].head
            knee_vector = (lo_vector.project(tot_vector) - lo_vector).normalized() * tot_vector.length

            if knee_vector == knee_vector * 0.0:
                self.report({'ERROR'}, f'Fix bone "{ebones[-1].name}" head position.')
                return

            pole_ebone = mesh.edit_bones[f'C_pole-{ebones[-1].name}']

            pole_ebone.head += knee_vector
            pole_ebone.tail += knee_vector

            # Pole line.
            ebone = mesh.edit_bones[f'C_line-{ebones[-1].name}']

            ebone.tail = pole_ebone.head
            ebone.parent = mesh.edit_bones[f'M-{ebones[-1].name}']
            ebone.hide_select = True # armature.bones or armature.edit_bones

            # Ik constraint; We can duplicate in map_pbones.
            map_pbones.append((
                f'M-{ebones[-1].name}',
                (),
                (),
                [(
                    'IK',
                    ('subtarget', f'M-{ebones2[0].name}'),
                    ('pole_subtarget', pole_ebone.name),
                    ('pole_angle', bones_get_pole_angle(ebones[0], ebones[-1], pole_ebone)),
                    ('chain_count', len(ebones))
                )],
            ))

            # Parent
            ebones2[0].parent = mesh.edit_bones[f'M-{ebones2[0].name}']
            ebones2[1].parent = mesh.edit_bones[f'M_rot-{ebones2[1].name}']

            # Heel, pivot3.
            ebone = mesh.edit_bones[f'C_heel-{ebones2[2].name}']
            ebone.head += ebones2[2].vector * 0.5
            ebone.tail += ebones2[2].vector * 0.5

            ebone = mesh.edit_bones[f'M_pivot3-{ebones2[2].name}']
            ebone.head += ebones2[2].vector * 0.5
            ebone.tail += ebones2[2].vector * 0.5

#            mesh.edit_bones.remove(ebones2[2]) # Heel_Pivots.

            ### Tweak bones; map_ebones resets!
            setup_edit_tweak_bones(mesh, map_ebones, map_pbones, ebones + ebones2[:-1], make_end=False)

            del ebones2, lo_vector, tot_vector, knee_vector, pole_ebone

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            setup_pose_bones(obj, map_pbones)

            pbones = [obj.pose.bones[sb.name] for sb in coll.bones[:-1][:-2]]
            pbones2 = [obj.pose.bones[sb.name] for sb in coll.bones[:-1][-2:]]

            # Ik settings.
            for pbone in pbones:
                pbone = obj.pose.bones[f'M-{pbone.name}']

                pbone.ik_stretch = 0.1

                if coll.rotation_axis == 'x':
                    pbone.lock_ik_z = True
                else: # rotation_axis == 'z'
                    pbone.lock_ik_x = True

                pbone.lock_ik_y = True

            # Helper knee.
            pbone = obj.pose.bones[f'M_hel-{pbones[-1].name}']

            if coll.rotation_axis == 'x':
                pbone.constraints[0].use_z = False
            else: # rotation_axis == 'z'
                pbone.constraints[0].use_x = False

            pbone.constraints[0].use_y = False

            pbones[-1].name = f'M_helper-{pbones[-1].name}'
            pbone.name = pbone.name[6:]

            # Tweaks stretch_to. Foot -> Toe.
            pbones2[0].constraints[0].subtarget = pbones2[1].name

            coll_ctr.assign(pbones2[1]) # Toe.

            del pbones, pbones2, pbone

            # Delete heel_pivots.
            bpy.ops.object.mode_set(mode='EDIT')
            mesh.edit_bones.remove(mesh.edit_bones[coll.bones[-1].name])

            print_time(f'Successfully generated leg: "{coll.name}"')
            continue

        #########
        # Finger.
        elif coll.rig_types == 'finger':
            if not sei_validate_collection(coll, 1, 999): return

            # Reset lists.
            map_ebones.clear()
            map_pbones.clear()

            ######### Edit Mode #########
            bpy.ops.object.mode_set(mode='EDIT')

            ######### Pose Mode #########
            bpy.ops.object.mode_set(mode='POSE')

            print_time(f'Successfully generated finger: "{coll.name}"')
            continue

    ###########################
    # 2. Restore ebone.use_connect.
    bpy.ops.object.mode_set(mode='EDIT')

    sei_bones = [
        sei_bone.name
        for collection in vars.collections
        for sei_bone in collection.bones
    ]

    for ebone_name in save_ebones_use_connect:
        if ebone_name in sei_bones: continue

        mesh.edit_bones[ebone_name].use_connect = True

    del save_ebones_use_connect, sei_bones

    ###########################
    # 3. Rotation mode to XYZ; It is at the end because we created new bones.
    # TODO: Just bones that need it.
    if vars.use_xyz_euler:
        obj.rotation_mode = 'XYZ'

        bpy.ops.object.mode_set(mode='POSE')

        for pbone in obj.pose.bones:
            pbone.rotation_mode = 'XYZ'

    ###########################
    # Finalize.
    bpy.ops.object.mode_set(mode=active_mode)

    # Refresh properties UI to display changes (bone collections).
    [a.tag_redraw() for a in context.screen.areas if a.type == 'PROPERTIES']

    self.report({'INFO'}, f'Successfully updated: "{obj.name}" {time.time() - start_time:.3f} seconds')


#===========================

sei_generate_rig()