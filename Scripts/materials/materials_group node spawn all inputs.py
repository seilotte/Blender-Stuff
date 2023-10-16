import bpy

# https://docs.blender.org/api/current/bpy.types.NodeSocketStandard.html
# Blender 3.5.1 Python API.
NodeSocketStandard_subclasses = [
    'Bool',
    'Collection',
    'Color',
    'Float',
    'FloatAngle',
    'FloatDistance',
    'FloatFactor',
    'FloatPercentage',
    'FloatTime',
    'FloatTimeAbsolute',
    'FloatUnsigned',
    'Geometry',
    'Image',
    'Int',
    'IntFactor',
    'IntPercentage',
    'IntUnsigned',
    'Material',
    'Object',
    'Shader',
    'String',
    'Texture',
    'Vector',
    'VectorAcceleration',
    'VectorDirection',
    'VectorEuler',
    'VectorTranslation',
    'VectorVelocity',
    'VectorXYZ',
    'Virtual',
]
def add_inputs(socket_name):
    obj = bpy.context.active_object
    active_node = obj.active_material.node_tree.nodes.active

    kawaii_name = socket_name + '.kawai'
    socket_name = 'NodeSocket' + socket_name
    active_node.node_tree.inputs.new(socket_name, kawaii_name)

for i in NodeSocketStandard_subclasses:
    add_inputs(i)