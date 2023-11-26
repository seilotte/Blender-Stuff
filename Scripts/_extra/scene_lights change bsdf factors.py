import bpy

for light in bpy.data.lights:
    if light.name == '_Sun [DO NOT DELETE]': continue
    light.diffuse_factor = 1.0
    light.specular_factor = 0.0
    light.volume_factor = 0.0