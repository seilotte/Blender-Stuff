# ApexTools

Random collection of tools for Apex Legends models.

https://github.com/seilotte/Blender-Stuff/assets/133937845/4dec3ab1-94e6-4e32-98d7-97ff806bbeb6

## Installation
1. Download the `ApexTools_v1.1.zip` from above.
1. Open blender and select `Edit -> Preferences -> Add-ons -> Install...`
1. Locate the `.zip` file, `Install Add-on -> Enable it`.
1. If you installed it successfully, it will be in the "n" panel with the name "Apex".

## Comments
- Tested on blender 3.4.1.
- The shader should work on blender versions below 3.4.
- Buttons, have descriptions.
- There's a README.txt inside the .zip.

## Limitations
- It will only attempt to generate a face metarig if the armature has a jaw bone.

## Known issues
- Even if it has a jaw bone, the face rig might generate incorrectly and display an error.
- If you want to generate only a body rig, go where your blender addons get installed. `ApexTools -> apex_rig -> delete "7generate_fix_face_rig", "a0fix_face_metarig_apex_legends", "a1face_metarig"`. Start over and attempt to generate the metarig.
- Auto Texture might not work.

## Credits
- Aerthas Veras (Shaders, Init Rigify script, and others.) // I modified them.
- llennoco (Auto Texture script) // I modified it.
