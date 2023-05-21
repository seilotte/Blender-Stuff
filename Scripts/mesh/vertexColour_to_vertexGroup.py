import bpy

# Not mine, from Aerthas Veras. I modified it.

vertexgroup_name = '_VertexAlpha'
vertexcolour_channel = 3 # 0-3

all = bpy.context.selected_objects

for obj in all:
    hasAlpha = False
    if obj.type != 'MESH':
        continue
    
    if obj.data.vertex_colors:
        print(f'{obj.name}: Checking for {vertexgroup_name} vertex group...')
        hasAlpha = False
        for i in obj.vertex_groups:
            if i.name == vertexgroup_name:
                print(f'Has {vertexgroup_name} vertex group. Ignoring mesh.')
                hasAlpha = True
                break

        if hasAlpha:
            print(f'{obj.name}: No vertex colours found. Exiting.')
        else:
            print(f'No Vertex Alpha vertex group found. Creating {vertexgroup_name}.')
            vert_val = [ [0.0, 0] for i in range(0, len(obj.data.vertices)) ]
            for loop_index, loop in enumerate(obj.data.loops):
                vi = loop.vertex_index
                vert_val[vi][0] += obj.data.vertex_colors[0].data[loop_index].color[vertexcolour_channel]
                vert_val[vi][1] += 1
                
            group = obj.vertex_groups.new(name=vertexgroup_name)
            
            for i in range(0, len(obj.data.vertices)):
                cnt = vert_val[i][1]
                weight = 0.0 if cnt == 0.0 else vert_val[i][0] / cnt
                group.add([i], weight, 'REPLACE')