import bpy
import bmesh

all = bpy.context.selected_objects

remove_mat_names = [
    'outline', 'shadow', 'uniqueb',
]

for obj in all:
    if obj.type != 'MESH':
        continue
    
    # Create a bmesh from the mesh data.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    for mat_slot in obj.material_slots:
        
        # Remove duplicated materials.
        split_mat_name = mat_slot.name.split('.')
        if len(split_mat_name) > 1:
            duped_mat_name = mat_slot.name
            
            # Change duplicated material with original mat.
            mat_slot.material = obj.material_slots[split_mat_name[0]].material
            print(f'Replaced: "{duped_mat_name}" with "{split_mat_name[0]}"')
            
            # Remove duplicated material from .blend file.
            bpy.data.materials.remove(bpy.data.materials[duped_mat_name])
        
        
        # Search for wanted materials.
        for i, n in enumerate(remove_mat_names): # i = numbers; n = name
            if i<2 and f'{i+1}' in mat_slot.name.lower() or n in mat_slot.name.lower():
                mat_index = obj.material_slots.find(mat_slot.name)
                
                # Remove vertices.
                for face in bm.faces:
                    if face.material_index == mat_index:
                        for loop in face.loops:
                            bm.verts.remove(loop.vert)
        
    # Update the mesh data with the modified bmesh.
    bm.to_mesh(obj.data)
    obj.data.update()