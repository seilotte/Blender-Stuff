'''
# Credits:
- @AerthasVeras - https://github.com/Aerthas/
- @GanonMaster - https://github.com/Ganonmaster/
- Original Files: https://github.com/Ganonmaster/Blender-Scripts/tree/master/ue4map-tools
- License: https://github.com/Ganonmaster/Blender-Scripts/blob/master/LICENSE

## Comments:
- The script needs .gltf files.
- It assumes everything will be inside the Base Directory.
- Fix Materials will likely change every material in the scene, be careful!


## TODO:
- Find a way to optimize the code and mantain readability.

### Umap import
- Use instances.
- Proper light support.
- Unreal particle systems? // I don't even know if it's possible.

### Fix materials
- Find a better way to read .props.txt files.
- Check for parent materials in .props.txt files.
- Add more "print()" for errors or to have a better understanding of what happened.
- Add more consistency to the code?
- Find a way to auto set-up the material? // It seems impossible, it defers a a lot from game to game.
                                            Even from maps from the same game is quite challenging.

### UI
- Add more settings. Example: Attempt to add normal map; invert y channel?

'''

import bpy
from bpy.types import Operator, Panel
from bpy.props import PointerProperty, StringProperty, BoolProperty
from bl_ui.generic_ui_list import draw_ui_list

import os
import json
from mathutils import Euler
from math import radians
import glob

# AGS = Aerthas Veras, Ganonmaster, Seilotte.
class AGS_variables(bpy.types.PropertyGroup): # It needs to be first; Custom variables.
    dir_base: StringProperty(name='Base', default='//', subtype='DIR_PATH', description='This is the base directory that contains all the unpacked assets - unpack using the latest ACL compatible build UE Viewer')
#    dir_sub: StringProperty(name='Sub', subtype='DIR_PATH', description='This is a subdirectory where you can insert additional parts of the path to the assets')
    dir_json: StringProperty(name='JSON', subtype='DIR_PATH', description='This is the path to the JSON file that contains the map data - you can extract this from .umap files using FModel.exe')

    import_static: BoolProperty(name='Static Meshes', default=True)
    import_lights: BoolProperty(name='Lights', default=False)

#    import_params_texture: BoolProperty(name='Texture Parameters', default=True)
#    import_params_vector: BoolProperty(name='Vector Parameters', default=True)


class AGS_OT_umap_import(Operator):
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    bl_idname = 'ags.umap_import'
    bl_label = 'Import Umap'
    bl_description = 'Import the indicated ".umap" file'

    @classmethod
    def poll(cls, context):
        vars = context.scene.ags_variables
        return vars.dir_base and vars.dir_json

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        vars = context.scene.ags_variables

        # Import types supported by the script
        static_mesh_types = [
            'StaticMeshComponent',
#            'InstancedStaticMeshComponent' # buggy, positions wrong, seems to be used with splines as well
        ]
        light_types = [
            'SpotLightComponent',
            'AnimatedLightComponent',
            'PointLightComponent'
        ]

#===

        class StaticMesh:
            entity_name = ''
            import_path = ''
            pos = [0, 0, 0]
            rot = [0, 0, 0]
            scale = [1, 1, 1]

            # These are just properties to help with debugging.
            no_entity = False
            no_mesh = False
            no_path = False
            base_shape = False
            no_file = False

            def __init__(self, json_entity, base_dir):
                self.entity_name = json_entity.get('Outer', 'Error')

                props = json_entity.get('Properties', None)

                if not props:
                    print('Invalid Entity: Lacking property.')
                    self.no_entity = True
                    return None

                if not props.get('StaticMesh', None):
                    print('Invalid Property: It does not contain a static mesh.')
                    self.no_mesh = True
                    return None

                object_path = props.get('StaticMesh').get('ObjectPath', None)

                if not object_path or object_path == '':
                    print('Invalid StaticMesh: It does not contatin an object path.')
                    self.no_path = True
                    return None

                if 'BasicShapes' in object_path:
                    # What is a BasicShape? Do we need these?
                    print('This is a BasicShape - skipping for now.')
                    self.base_shape = True
                    return None


                # Get the file name; EX/AM/ple.3 -> ple.3 -> ple -> ple.gltf
                obj_path_name = object_path.split('/')[-1].split('.')[0] + '.gltf'

                # Search for GLTF files in the Base directory.
                obj_path = glob.glob(os.path.join(vars.dir_base, '**', obj_path_name), recursive=True)
                obj_path = obj_path[0] if obj_path else None # Use the first match.

                self.import_path = obj_path

                if not obj_path:
                    print(f'{obj_path_name} not found in {vars.dir_base}.')
                    print('Mesh Path', object_path)
                    self.no_file = True
                    return None


                if props.get('RelativeLocation', False):
                    pos = props.get('RelativeLocation')
                    self.pos = [pos.get('X')/100, pos.get('Y')/-100, pos.get('Z')/100]

                if props.get('RelativeRotation', False):
                    rot = props.get('RelativeRotation')
                    self.rot = [rot.get('Roll'), rot.get('Pitch')*-1, rot.get('Yaw')*-1]

                if props.get('RelativeScale3D', False):
                    scale = props.get('RelativeScale3D')
                    self.scale = [scale.get('X', 1), scale.get('Y', 1), scale.get('Z', 1)]

                return None


            @property
            def invalid(self):
                return self.no_entity or self.no_mesh or self.no_path or self.base_shape or self.no_file

            def import_staticmesh(self, collection):
                if self.invalid:
                    print('Refusing to import due to failed checks.')
                    return False

                # Import the file and apply transforms.
                bpy.ops.import_scene.gltf(filepath=self.import_path)
                imported_obj = context.object

                imported_obj.name = self.entity_name
                imported_obj.location = (self.pos[0], self.pos[1], self.pos[2])
                imported_obj.rotation_mode = 'XYZ'
                imported_obj.rotation_euler = Euler((radians(self.rot[0]), radians(self.rot[1]), radians(self.rot[2])), 'XYZ')
                imported_obj.scale = (self.scale[0], self.scale[1], self.scale[2])

                collection.objects.link(imported_obj)
                context.scene.collection.objects.unlink(imported_obj)

                print('StaticMesh imported:', self.entity_name)
                return imported_obj


        class GameLight:
            entity_name = ""
            type = ""

            pos = [0, 0, 0]
            rot = [0, 0, 0]
            scale = [1, 1, 1]

            energy = 1000

            # These are just properties to help with debugging.
            no_entity = False

            def __init__(self, json_entity):
                self.entity_name = json_entity.get('Outer', 'Error')
                self.type = json_entity.get('SpotLightComponent', 'SpotLightComponent')

                props = json_entity.get('Properties', None)

                if not props:
                    print('Invalid Entity: Lacking property.')
                    self.no_entity = True
                    return None


                if props.get('RelativeLocation', False):
                    pos = props.get('RelativeLocation')
                    self.pos = [pos.get('X')/100, pos.get('Y')/-100, pos.get('Z')/100]

                if props.get('RelativeRotation', False):
                    rot = props.get('RelativeRotation')
                    self.rot = [rot.get('Roll'), rot.get('Pitch')*-1, rot.get('Yaw')*-1]

                if props.get('RelativeScale3D', False):
                    scale = props.get('RelativeScale3D')
                    self.scale = [scale.get('X', 1), scale.get('Y', 1), scale.get('Z', 1)]

                #TODO: expand this method with more properties for the specific light types
                # Problem: I don't know how values for UE lights map to Blender's light types.


            def import_light(self, collection):
                if self.no_entity:
                    print('Refusing to import due to failed checks.')
                    return False

                if self.type == 'SpotLightComponent':
                    light_data = bpy.data.lights.new(name=self.entity_name, type='SPOT')
                if self.type == 'PointLightComponent':
                    light_data = bpy.data.lights.new(name=self.entity_name, type='POINT')
                
                imported_light = bpy.data.objects.new(name=self.entity_name, object_data=light_data)

                imported_light.location = (self.pos[0], self.pos[1], self.pos[2])
                imported_light.rotation_mode = 'XYZ'
                imported_light.rotation_euler = Euler((radians(self.rot[0]), radians(self.rot[1]), radians(self.rot[2])), 'XYZ')
                imported_light.scale = (self.scale[0], self.scale[1], self.scale[2])

                collection.objects.link(imported_light)
                context.scene.collection.objects.link(imported_light)

                print('Light imported:', self.entity_name)
                return imported_light

#===

        # Search for JSON files in the JSON directory.
        map_json = glob.glob(os.path.join(vars.dir_json, '**/*.json'), recursive=True)

        if not map_json:
            self.report({'WARNING'}, f'No JSON file found in "{vars.dir_json}".')
        else:

            # SCRIPT STARTS DOING STUFF HERE.
            for map in map_json:
                print('Processing file', map)

                if not os.path.exists(map):
                    print('File not found, skipping.', map)
                    continue

                json_filename = os.path.basename(map)
                import_collection = bpy.data.collections.new(json_filename[:-5])

                context.scene.collection.children.link(import_collection)

                with open(map) as file:
                    json_object = json.load(file)
                    print('-------------===========================-------------')

                    # Handle the different entity types.
                    for entity in json_object:
                        if not entity.get('Type', None):
                            continue

                        if vars.import_lights and entity.get('Type') in light_types:
#                            print(entity)
                            light = GameLight(entity)
                            light.import_light(import_collection)

                        if vars.import_static and entity.get('Type') in static_mesh_types:
                            static_mesh = StaticMesh(entity, vars.dir_base)
                            # TODO: optimize by instancing certain meshes
                            static_mesh.import_staticmesh(import_collection)
                            continue

            self.report({'INFO'}, 'Import umap: Done.')
        return {'FINISHED'}

class AGS_OT_fix_materials(Operator):
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    bl_idname = 'ags.fix_materials'
    bl_label = 'Fix Materials'
    bl_description = 'Remove duplicated materials from the file and attempt to auto set-up the materials'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        vars = context.scene.ags_variables

        ### Dedup materials.
        for obj in context.scene.objects:
            if obj.type != 'MESH': continue

            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    mat = mat_slot.material

                    # Specific to the Harry Potter game?
                    if 'WorldGridMaterial' in mat.name:
                        bpy.data.materials.remove(mat, do_unlink=True)
                        bpy.data.objects.remove(obj, do_unlink=True) # This will likely produce an error.
                        continue

                    split_mat_name = mat.name.split('.')
                    if len(split_mat_name) < 2: continue

                    org_mat = bpy.data.materials.get(split_mat_name[0])
                    if org_mat:
                        mat_slot.material = org_mat
                        print(f'Replaced material "{mat.name}" in object "{obj.name}".')
                        bpy.data.materials.remove(mat, do_unlink=True)


        ### Attempt to auto set-up the material.
        # Search for PROPS.TXT files in the Base directory.
        props_files_path = glob.glob(os.path.join(vars.dir_base, '**/*.props.txt'), recursive=True)

        texture_params = []
        texture_lines_after = []
        streaming_params = []
        streaming_lines_after = []
        vector_params = []
        vector_lines_after = []

        processed_materials = set()

        for obj in context.scene.objects:
            if obj.type != 'MESH': continue

            for mat in obj.data.materials:
                if mat in processed_materials: continue
                processed_materials.add(mat)

                ## Get parameters for lists from .props.txt.
                # Hardcoding stuff since .props.txt follows certain rules.
                for file_path in props_files_path:
                    file_name = os.path.basename(file_path)

                    if mat.name != file_name[:-10]: continue # [:-10] -> Remove .props.txt.

                    with open(file_path) as prop_file:
                        for line in prop_file:

                            # Get every Textures.
                            if 'Texture2D' in line:
                                texture_name = line.split('/')[-1].split('.')[0]
                                texture_params = list(set( texture_params + [(texture_name, None)] )) # Avoid dupped strings.

                            # Get Collected Texture Parameters.
                            if 'CollectedTextureParameters[' in line:
                                if not line.startswith("    "): continue
                                texture_lines_after.append(line)

                            elif texture_lines_after:
                                texture_lines_after.append(line)

                                if len(texture_lines_after) > 4:
                                    texture_name = texture_lines_after[2].split('/')[-1].split('.')[0]
                                    name = texture_lines_after[3].split('=')[1].strip()

                                    for i, param in enumerate(texture_params): # Avoid dupped strings.
                                        if param[0] == texture_name:
                                            texture_params[i] = (texture_name, name)
                                            break
                                    else:
                                        texture_params.append((texture_name, name))

                                    texture_lines_after = []

                            # Get Texture Streaming Data.
                            elif 'TextureStreamingData[' in line:
                                if not line.startswith("    "): continue
                                streaming_lines_after.append(line)

                            elif streaming_lines_after:
                                streaming_lines_after.append(line)

                                if len(streaming_lines_after) > 4:
                                    uv_scale = streaming_lines_after[2].split('=')[1].strip()
                                    uv_index = streaming_lines_after[3].split('=')[1].strip()
                                    texture_name = streaming_lines_after[4].split('=')[1].strip()

                                    streaming_params.append((float(uv_scale), int(uv_index), texture_name))

                                    streaming_lines_after = []

                            # Get Collected Vector Parameters.
                            elif 'CollectedVectorParameters[' in line:
                                if not line.startswith("    "): continue
                                vector_lines_after.append(line)

                            elif vector_lines_after:
                                vector_lines_after.append(line)

                                if len(vector_lines_after) > 4:
                                    string = vector_lines_after[2].split('=')
                                    rgba = (string[2][0], string[3][0], string[4][0], string[5][0])
                                    name = vector_lines_after[3].split('=')[1].strip()

                                    vector_params.append((rgba, name))

                                    vector_lines_after = []


                ## Set-up material settings and the tree.
                mat.use_nodes = True
#                mat.use_backface_culling = True
                tree = mat.node_tree
                tree.nodes.clear()

                # Search for the texture file in the Base directory.
                texture_information = {}
                for subdir, dirs, files in os.walk(vars.dir_base):
                    for file in files:
                        texture_information[file[:-4]] = {  # .tga and .png have the same length.
                            'name': file,
                            'path': os.path.join(subdir, file),
                        }

                # Load textures.
                for i, (texture, texture_name) in enumerate(texture_params):
                    texture_info = texture_information.get(texture, None)
                    if not texture_info:
                        print(f'"{texture}" not found in "{vars.dir_base}".')
                    else:
                        image = bpy.data.images.get(texture_info['name']) or bpy.data.images.load(texture_info['path'])

                        image.colorspace_settings.name = 'Non-Color'
#                        image.alpha_mode = 'CHANNEL_PACKED' # Non-Color does it by default.

                        # Add texture nodes from "texture_params".
                        texture_node = tree.nodes.new('ShaderNodeTexImage')
                        texture_node.location = (-300, -300 * (i - 1))
                        texture_node.image = image
                        if texture_name:
                            texture_node.label = texture_name
#                            texture_node.name = texture_name

                        # Add uv settings from "streaming_params"-
                        for uv_scale, uv_index, tex_name in streaming_params:
                            if image.name[:-4] == tex_name:
                                uv_node = tree.nodes.new('ShaderNodeUVMap')
                                uv_node.location = (-700, -300 * (i - 1))
                                uv_node.uv_map = obj.data.uv_layers[uv_index].name

                                vector_node = tree.nodes.new('ShaderNodeVectorMath')
                                vector_node.location = (-500, -300 * (i - 1))
                                vector_node.operation = 'MULTIPLY_ADD'
                                vector_node.inputs[1].default_value = (uv_scale, uv_scale, 0) # 1/uv_scale?

                                tree.links.new(uv_node.outputs['UV'], vector_node.inputs['Vector'])
                                tree.links.new(vector_node.outputs['Vector'], texture_node.inputs['Vector'])

                # Add rgb nodes from "vector_params".
                for i, (vector, vector_name) in enumerate(vector_params):
                    rgb_node = tree.nodes.new('ShaderNodeRGB')
                    rgb_node.location = (-900, -200 * (i - 1))
                    rgb_node.outputs['Color'].default_value = tuple(map(float, vector))
                    rgb_node.label = vector_name
#                    rgb_node.name = vector_name

                # Add material/shader nodes.
                output_node = tree.nodes.new('ShaderNodeOutputMaterial')
                output_node.location = (300, 300)

#                pbsdf_node = tree.nodes.new('ShaderNodeBsdfPrincipled') # ShaderNodeBsdfPrincipled:ShaderNodeBsdfDiffuse
#                pbsdf_node.location = (10, 300)

#                normal_map_node = tree.nodes.new('ShaderNodeNormalMap')
#                normal_map_node.location = (-200, 100)

                # Add links to nodes.
#                tree.links.new(pbsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

                if tree.nodes.get('Image Texture'):
                    tree.links.new(tree.nodes['Image Texture'].outputs['Color'], output_node.inputs['Surface'])


                # Reset the lists for the next material.
                texture_params = []
                texture_lines_after = []
                streaming_params = []
                streaming_lines_after = []
                vector_params = []
                vector_lines_after = []

                print(f'Modified material: {mat.name}')

        self.report({'INFO'}, 'Fix materials: Done.')
        return {'FINISHED'}


class AGS_PT_umap_tools(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AGS Umap'

    bl_idname = 'AGS_PT_umap_tools'
    bl_label = 'Umap Tools'

#    def draw_header(self, context):
#        self.layout.label(icon='BLENDER')

    def draw(self, context):
        vars = context.scene.ags_variables
        layout = self.layout

        col = layout.column(align=True)
        col.label(text='Directories:', icon='FILE_FOLDER')
        col.prop(vars, 'dir_base')
#        col.prop(vars, 'dir_sub')
#        col.separator()
        col.prop(vars, 'dir_json')


        layout.separator()
        col = layout.column()
        col.label(text='Import Settings:', icon='SETTINGS')

        col_box = col.box().column(align=True)

        def box_row(property, icon='DOT'):
            row = col_box.split(factor=0.85)
            row.prop(vars, property)
            row.label(icon=icon)

        box_row('import_static', 'MESH_DATA')
        box_row('import_lights', 'LIGHT_DATA')
#        col_box.separator(factor=2)
#        col_box.label(text='Fix Materials:')
#        box_row('import_params_texture', 'IMAGE_DATA')
#        box_row('import_params_vector')


        layout.separator()
        col = layout.column()
        col.scale_y = 1.3
        col.operator('ags.umap_import', text='Import') # icon=IMPORT
        col.operator('ags.fix_materials') # icon=MATERIAL

#===========================

classes = [
    AGS_variables, # It needs to be first; Custom variables.
    AGS_OT_umap_import,
    AGS_OT_fix_materials,
    AGS_PT_umap_tools,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.ags_variables = PointerProperty(type=AGS_variables)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.ags_variables

if __name__ == "__main__": # debug; live edit
    register()