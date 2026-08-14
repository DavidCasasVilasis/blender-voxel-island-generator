import bpy
import mathutils
from mathutils import Vector, noise
import random
import os

# ==============================================================================
#                  VOXEL MESH PRO - BLENDER ADDON / SCRIPT
# Replicates the VoxelMeshPro C# class for Unity inside Blender.
# Includes 3D Perlin Noise, custom holes, rounding, and spherizing.
# Loads materials dynamically from voxel_island_generator.blend.
# ==============================================================================

bl_info = {
    "name": "Voxel Island Generator (Voxel Mesh Pro)",
    "author": "Antigravity AI Port",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Voxel Mesh Pro",
    "description": "Procedural voxel island generator loading assets from voxel_island_generator.blend",
    "category": "Mesh",
}

# --- Paths & Asset Library Setup ---

def get_blend_library_path():
    # 1. Try to find it in the same directory as the script (when run as a ZIP addon)
    try:
        addon_dir = os.path.dirname(__file__)
        path = os.path.join(addon_dir, "voxel_island_generator.blend")
        if os.path.exists(path):
            return path
    except NameError:
        pass
        
    # 2. Fallback to the project directory (when executed as a script or single-file addon)
    fallback_dir = r"F:\OneDrive - UAB\1. Kosmikal\Tareas Universidad\4o\Integración de objetos\Modelos\Escenario\Islas\blender-voxel-island-generator"
    path = os.path.join(fallback_dir, "voxel_island_generator.blend")
    if os.path.exists(path):
        return path
        
    return ""

def import_material_from_library(material_name):
    # If the material already exists in the current Blender file, reuse it
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]
        
    blend_path = get_blend_library_path()
    
    # Import the material from voxel_island_generator.blend
    if blend_path and os.path.exists(blend_path):
        try:
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                if material_name in data_from.materials:
                    data_to.materials = [material_name]
            
            # Return the newly imported material
            if material_name in bpy.data.materials:
                return bpy.data.materials[material_name]
        except Exception as e:
            print(f"[VoxelMeshPro] Failed to import {material_name} from blend library: {e}")
            
    return None

# --- Noise Helpers ---

def lerp(a, b, t):
    return a + (b - a) * t

def perlin_2d(x, y):
    val = noise.noise(Vector((x, y, 0.0)))
    val = (val + 1.0) * 0.5
    return max(0.0, min(1.0, val))

def perlin_3d(x, y, z):
    xy = perlin_2d(x, y)
    yz = perlin_2d(y, z)
    xz = perlin_2d(x, z)
    
    y1 = lerp(xy, yz, 0.5)
    y2 = lerp(xz, yz, 0.5)
    
    return lerp(y1, y2, 0.5)

# --- Geometry & Grid Helpers ---

def is_solid_block(x, y, z, world_data, size_x, size_y, size_z):
    if x < 0 or x >= size_x or y < 0 or y >= size_y or z < 0 or z >= size_z:
        return False
    return world_data[x][y][z] == 1

def is_adjacent_to_top_face(x, y, z, normal, world_data, size_x, size_y, size_z):
    if normal[1] == 1.0 or normal[1] == -1.0:
        return False
    if not is_solid_block(x, y + 1, z, world_data, size_x, size_y, size_z):
        return False
    return True

def get_target_material_index(x, y, z, normal, world_data, size_x, size_y, size_z):
    if normal[1] == -1.0: # Down
        return 0
    if normal[1] == 1.0: # Up
        return 2
    if is_adjacent_to_top_face(x, y, z, normal, world_data, size_x, size_y, size_z):
        return 1
    else:
        return 3

def to_blender_coords(v_unity):
    return Vector((v_unity[0], v_unity[2], v_unity[1]))

def add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal_unity, material_index):
    half = 0.5
    face_vertices_unity = []
    if normal_unity == (0, 1, 0): # Up (+Y)
        face_vertices_unity = [
            voxel_center_unity + Vector((-half, half, -half)),
            voxel_center_unity + Vector((half, half, -half)),
            voxel_center_unity + Vector((half, half, half)),
            voxel_center_unity + Vector((-half, half, half))
        ]
    elif normal_unity == (0, -1, 0): # Down (-Y)
        face_vertices_unity = [
            voxel_center_unity + Vector((-half, -half, half)),
            voxel_center_unity + Vector((half, -half, half)),
            voxel_center_unity + Vector((half, -half, -half)),
            voxel_center_unity + Vector((-half, -half, -half))
        ]
    elif normal_unity == (1, 0, 0): # Right (+X)
        face_vertices_unity = [
            voxel_center_unity + Vector((half, -half, half)),
            voxel_center_unity + Vector((half, half, half)),
            voxel_center_unity + Vector((half, half, -half)),
            voxel_center_unity + Vector((half, -half, -half))
        ]
    elif normal_unity == (-1, 0, 0): # Left (-X)
        face_vertices_unity = [
            voxel_center_unity + Vector((-half, -half, -half)),
            voxel_center_unity + Vector((-half, half, -half)),
            voxel_center_unity + Vector((-half, half, half)),
            voxel_center_unity + Vector((-half, -half, half))
        ]
    elif normal_unity == (0, 0, 1): # Forward (+Z)
        face_vertices_unity = [
            voxel_center_unity + Vector((-half, -half, half)),
            voxel_center_unity + Vector((-half, half, half)),
            voxel_center_unity + Vector((half, half, half)),
            voxel_center_unity + Vector((half, -half, half))
        ]
    elif normal_unity == (0, 0, -1): # Back (-Z)
        face_vertices_unity = [
            voxel_center_unity + Vector((half, -half, -half)),
            voxel_center_unity + Vector((half, half, -half)),
            voxel_center_unity + Vector((-half, half, -half)),
            voxel_center_unity + Vector((-half, -half, -half))
        ]
        
    start_idx = len(vertices)
    for v in face_vertices_unity:
        vertices.append(to_blender_coords(v))
        
    faces.append((start_idx, start_idx + 1, start_idx + 2, start_idx + 3))
    material_assignments.append(material_index)

# --- Modification Logic (Holes, Rounding, Spherize) ---

def aplicar_huecos_planos(world_data, size_x, size_y, size_z, huecos_planos):
    for hueco in huecos_planos:
        centro_x = int(round(hueco['posicion'][0] + size_x * 0.5))
        centro_y = int(round(hueco['posicion'][1] + size_y * 0.5))
        centro_z = int(round(hueco['posicion'][2] + size_z * 0.5))
        
        tam_x = max(1, hueco['tamaño_x'])
        tam_y = max(1, hueco['tamaño_y'])
        tam_z = max(1, hueco['tamaño_z'])
        
        min_x = centro_x - tam_x // 2
        max_x = centro_x + tam_x // 2
        min_y = centro_y - tam_y // 2
        max_y = centro_y + tam_y // 2
        min_z = centro_z - tam_z // 2
        max_z = centro_z + tam_z // 2
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    if 0 <= x < size_x and 0 <= y < size_y and 0 <= z < size_z:
                        world_data[x][y][z] = 0

def esta_cerca_de_esquina(x, y, z, sizeX, sizeY, sizeZ):
    esquinasX = [0, sizeX - 1]
    esquinasY = [0, sizeY - 1]
    esquinasZ = [0, sizeZ - 1]
    for ex in esquinasX:
        for ey in esquinasY:
            for ez in esquinasZ:
                distancia = abs(x - ex) + abs(y - ey) + abs(z - ez)
                if distancia == 1:
                    return True
    return False

def esta_cerca_de_esquina_o_arista(x, y, z, sizeX, sizeY, sizeZ):
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            for dz in range(-1, 2):
                nx = x + dx
                ny = y + dy
                nz = z + dz
                if 0 <= nx < sizeX and 0 <= ny < sizeY and 0 <= nz < sizeZ:
                    carasExpuestas = 0
                    if nx == 0 or nx == sizeX - 1: carasExpuestas += 1
                    if ny == 0 or ny == sizeY - 1: carasExpuestas += 1
                    if nz == 0 or nz == sizeZ - 1: carasExpuestas += 1
                    if carasExpuestas >= 3:
                        return True
    return False

def esta_en_radio_de_esquina(x, y, z, sizeX, sizeY, sizeZ, radio):
    esquinasX = [0, sizeX - 1]
    esquinasY = [0, sizeY - 1]
    esquinasZ = [0, sizeZ - 1]
    for ex in esquinasX:
        for ey in esquinasY:
            for ez in esquinasZ:
                distancia = abs(x - ex) + abs(y - ey) + abs(z - ez)
                if distancia <= radio:
                    return True
    return False

def es_voxel_en_esquina_o_arista(x, y, z, sizeX, sizeY, sizeZ, intensidad):
    carasExpuestas = 0
    if x == 0 or x == sizeX - 1: carasExpuestas += 1
    if y == 0 or y == sizeY - 1: carasExpuestas += 1
    if z == 0 or z == sizeZ - 1: carasExpuestas += 1
    
    if intensidad == 1:
        return carasExpuestas >= 3
    elif intensidad == 2:
        return carasExpuestas >= 3 or (carasExpuestas >= 2 and esta_cerca_de_esquina(x, y, z, sizeX, sizeY, sizeZ))
    elif intensidad == 3:
        return carasExpuestas >= 2 or (carasExpuestas >= 1 and esta_cerca_de_esquina_o_arista(x, y, z, sizeX, sizeY, sizeZ))
    elif intensidad >= 4:
        radio = intensidad - 2
        return esta_en_radio_de_esquina(x, y, z, sizeX, sizeY, sizeZ, radio)
    return False

def redondear_esquinas(world_data, sizeX, sizeY, sizeZ, intensidad):
    for x in range(sizeX):
        for y in range(sizeY):
            for z in range(sizeZ):
                if world_data[x][y][z] == 1:
                    if es_voxel_en_esquina_o_arista(x, y, z, sizeX, sizeY, sizeZ, intensidad):
                        world_data[x][y][z] = 0

def esferizar_malla(world_data, sizeX, sizeY, sizeZ, intensidad):
    centroX = sizeX * 0.5
    centroY = sizeY * 0.5
    centroZ = sizeZ * 0.5
    
    radioBase = min(sizeX, sizeY, sizeZ) * 0.5
    radioEsfera = radioBase / intensidad
    radioCuadrado = radioEsfera * radioEsfera
    
    for x in range(sizeX):
        for y in range(sizeY):
            for z in range(sizeZ):
                if world_data[x][y][z] == 1:
                    distX = (x + 0.5) - centroX
                    distY = (y + 0.5) - centroY
                    distZ = (z + 0.5) - centroZ
                    distCuadrada = distX*distX + distY*distY + distZ*distZ
                    if distCuadrada > radioCuadrado:
                        world_data[x][y][z] = 0

# --- Materials Setup ---

def setup_materials_on_mesh(mesh, settings):
    mats = [
        settings.bottom_material,
        settings.general_material,
        settings.top_material,
        settings.adjacent_material
    ]
    
    # Names of materials expected to be inside voxel_island_generator.blend
    blend_configs = [
        ("Voxel_Bottom", (0.35, 0.23, 0.15, 1.0)),      # Bottom face: soil
        ("Voxel_General", (0.45, 0.75, 0.35, 1.0)),     # Adjacent to top: light grass/dirt
        ("Voxel_Top", (0.3, 0.8, 0.2, 1.0)),            # Top face: bright grass
        ("Voxel_Adjacent", (0.4, 0.4, 0.4, 1.0))        # Other sides: grey rock
    ]
    
    mesh.materials.clear()
        
    for i, mat in enumerate(mats):
        if mat is not None:
            mat_to_assign = mat
        else:
            name, color = blend_configs[i]
            # Try to load the material from the external blend file library
            mat_library = import_material_from_library(name)
            if mat_library is not None:
                mat_to_assign = mat_library
            else:
                # Fallback to local procedural material if blend is missing or doesn't have it
                mat_default = bpy.data.materials.get(name)
                if mat_default is None:
                    mat_default = bpy.data.materials.new(name=name)
                    mat_default.use_nodes = True
                    principled = mat_default.node_tree.nodes.get("Principled BSDF")
                    if principled:
                        principled.inputs['Base Color'].default_value = color
                    mat_default.diffuse_color = color
                mat_to_assign = mat_default
            
        mesh.materials.append(mat_to_assign)

# --- Main Generation Function ---

def generate_voxel_mesh(context):
    settings = context.scene.voxel_settings
    
    sizeX = settings.size_x
    sizeY = settings.size_z # Y is vertical (height) in Unity coordinates
    sizeZ = settings.size_y # Z is depth (length) in Unity coordinates
    
    world_data = [[[0 for z in range(sizeZ)] for y in range(sizeY)] for x in range(sizeX)]
    
    # 1. Populate initial voxel grid
    if settings.use_perlin_noise:
        for x in range(sizeX):
            for y in range(sizeY):
                for z in range(sizeZ):
                    p_val = perlin_3d(
                        (x + settings.perlin_offset[0]) * settings.perlin_scale,
                        (y + settings.perlin_offset[1]) * settings.perlin_scale,
                        (z + settings.perlin_offset[2]) * settings.perlin_scale
                    )
                    world_data[x][y][z] = 1 if p_val > settings.perlin_threshold else 0
    elif settings.random_fill:
        for x in range(sizeX):
            for y in range(sizeY):
                for z in range(sizeZ):
                    world_data[x][y][z] = 1 if random.random() < settings.fill_probability else 0
    else:
        for x in range(sizeX):
            for y in range(sizeY):
                for z in range(sizeZ):
                    world_data[x][y][z] = 1
                    
    # 2. Planar Holes (both from UI list and from scene Empties)
    huecos = []
    
    # A. Holes from the UI list (manually typed coordinates)
    for h in settings.holes:
        huecos.append({
            'posicion': Vector((h.pos_x, h.pos_z, h.pos_y)), # Map Blender (x, y, z) to Unity (x, z, y)
            'tamaño_x': h.size_x,
            'tamaño_y': h.size_z, # Blender Z is Unity Y
            'tamaño_z': h.size_y  # Blender Y is Unity Z
        })
        
    # B. Holes from Empty Objects in the scene named "Hole..."
    active_obj = context.active_object
    parent_pos = active_obj.location if active_obj else Vector((0,0,0))
    for o in context.scene.objects:
        if o.name.startswith("Hole") and o.type == 'EMPTY':
            rel_pos = o.location - parent_pos
            unity_pos = Vector((rel_pos.x, rel_pos.z, rel_pos.y))
            size_blender = o.scale * 2.0
            unity_size_x = int(max(1.0, round(size_blender.x)))
            unity_size_y = int(max(1.0, round(size_blender.z)))
            unity_size_z = int(max(1.0, round(size_blender.y)))
            
            huecos.append({
                'posicion': unity_pos,
                'tamaño_x': unity_size_x,
                'tamaño_y': unity_size_y,
                'tamaño_z': unity_size_z
            })
            
    aplicar_huecos_planos(world_data, sizeX, sizeY, sizeZ, huecos)
    
    # 3. Corner rounding
    if settings.redondear_esquinas:
        redondear_esquinas(world_data, sizeX, sizeY, sizeZ, settings.intensidad_redondeo)
        
    # 4. Spherizing
    if settings.esferizar_malla:
        esferizar_malla(world_data, sizeX, sizeY, sizeZ, settings.intensidad_esferizado)
        
    # 5. Build vertices and faces
    vertices = []
    faces = []
    material_assignments = []
    
    for x in range(sizeX):
        for y in range(sizeY):
            for z in range(sizeZ):
                if world_data[x][y][z] == 1:
                    voxel_center_unity = Vector((x - sizeX * 0.5, y - sizeY * 0.5, z - sizeZ * 0.5))
                    
                    # Check 6 faces for solid neighbors
                    # Left (-X)
                    if not is_solid_block(x - 1, y, z, world_data, sizeX, sizeY, sizeZ):
                        normal = (-1, 0, 0)
                        mat_idx = get_target_material_index(x, y, z, normal, world_data, sizeX, sizeY, sizeZ)
                        add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal, mat_idx)
                    # Right (+X)
                    if not is_solid_block(x + 1, y, z, world_data, sizeX, sizeY, sizeZ):
                        normal = (1, 0, 0)
                        mat_idx = get_target_material_index(x, y, z, normal, world_data, sizeX, sizeY, sizeZ)
                        add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal, mat_idx)
                    # Down (-Y)
                    if not is_solid_block(x, y - 1, z, world_data, sizeX, sizeY, sizeZ):
                        normal = (0, -1, 0)
                        mat_idx = get_target_material_index(x, y, z, normal, world_data, sizeX, sizeY, sizeZ)
                        add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal, mat_idx)
                    # Up (+Y)
                    if not is_solid_block(x, y + 1, z, world_data, sizeX, sizeY, sizeZ):
                        normal = (0, 1, 0)
                        mat_idx = get_target_material_index(x, y, z, normal, world_data, sizeX, sizeY, sizeZ)
                        add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal, mat_idx)
                    # Back (-Z)
                    if not is_solid_block(x, y, z - 1, world_data, sizeX, sizeY, sizeZ):
                        normal = (0, 0, -1)
                        mat_idx = get_target_material_index(x, y, z, normal, world_data, sizeX, sizeY, sizeZ)
                        add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal, mat_idx)
                    # Forward (+Z)
                    if not is_solid_block(x, y, z + 1, world_data, sizeX, sizeY, sizeZ):
                        normal = (0, 0, 1)
                        mat_idx = get_target_material_index(x, y, z, normal, world_data, sizeX, sizeY, sizeZ)
                        add_cube_face(vertices, faces, material_assignments, voxel_center_unity, normal, mat_idx)
                        
    # 6. Create mesh
    mesh_name = "VoxelIslandMesh"
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(vertices, [], faces)
    
    # Assign materials to the mesh BEFORE assigning face material indices.
    setup_materials_on_mesh(mesh, settings)
    
    # Assign material index per face (now safe, won't be clamped to 0)
    for i, face in enumerate(mesh.polygons):
        if i < len(material_assignments):
            face.material_index = material_assignments[i]
            
    # 1. Update the mesh first to ensure all loops are initialized in Blender's memory
    mesh.update()
            
    # 2. Create the UV Map and make it active
    uv_layer = mesh.uv_layers.new(name="UVMap")
    mesh.uv_layers.active = uv_layer
    
    # 3. Assign UV coordinates to each face loop
    for face in mesh.polygons:
        for loop_idx, loop in enumerate(face.loop_indices):
            if loop_idx == 0:
                uv_layer.data[loop].uv = (0.0, 0.0)
            elif loop_idx == 1:
                uv_layer.data[loop].uv = (1.0, 0.0)
            elif loop_idx == 2:
                uv_layer.data[loop].uv = (1.0, 1.0)
            elif loop_idx == 3:
                uv_layer.data[loop].uv = (0.0, 1.0)
                
    # 4. Final update to register the UV map coordinates
    mesh.update()
    
    # Store active object reference and deselect all to avoid editing other meshes
    active_obj = context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    
    target_obj_name = "VoxelIslandObj"
    if active_obj and active_obj.name.startswith("VoxelIslandObj"):
        target_obj_name = active_obj.name
        
    old_obj = context.scene.objects.get(target_obj_name)
    if old_obj:
        old_location = old_obj.location.copy()
        old_rotation = old_obj.rotation_euler.copy()
        old_mesh = old_obj.data
        bpy.data.objects.remove(old_obj, do_unlink=True)
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)
    else:
        old_location = Vector((0, 0, 0))
        old_rotation = Vector((0, 0, 0))
        
    # Create brand new object to ensure material slots are clean and uncorrupted
    obj = bpy.data.objects.new(target_obj_name, mesh)
    context.collection.objects.link(obj)
    
    # Restore transform coordinates
    obj.location = old_location
    obj.rotation_euler = old_rotation
    
    obj.select_set(True)
    context.view_layer.objects.active = obj
    
    # Force slots to link to DATA (Mesh) to align with our setup
    for slot in obj.material_slots:
        slot.link = 'DATA'
    
    # Recalculate normals to face outward
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return obj

# --- Blender UI Panel & Operator Classes ---

class VOXEL_OT_GenerateVoxelMesh(bpy.types.Operator):
    bl_idname = "voxel.generate_mesh"
    bl_label = "Generate Voxel Island"
    bl_description = "Generate voxel mesh from current settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            generate_voxel_mesh(context)
            self.report({'INFO'}, "Island generated successfully!")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to generate: {str(e)}")
        return {'FINISHED'}

class VOXEL_OT_RandomizeSettings(bpy.types.Operator):
    bl_idname = "voxel.randomize_settings"
    bl_label = "Randomize Parameters"
    bl_description = "Randomize noise offset and parameters"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.voxel_settings
        settings.random_fill = False
        settings.use_perlin_noise = True
        settings.perlin_scale = random.uniform(0.05, 0.2)
        settings.perlin_threshold = random.uniform(0.2, 0.5)
        settings.perlin_offset = (
            random.uniform(0.0, 100.0),
            random.uniform(0.0, 100.0),
            random.uniform(0.0, 100.0)
        )
        self.report({'INFO'}, "Parameters randomized!")
        return {'FINISHED'}

class VOXEL_PT_GeneratorPanel(bpy.types.Panel):
    bl_label = "Voxel Island Settings"
    bl_idname = "VOXEL_PT_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Voxel Mesh Pro"
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.voxel_settings
        
        layout.label(text="Grid Dimensions:")
        row = layout.row(align=True)
        row.prop(settings, "size_x", text="Width X")
        row.prop(settings, "size_y", text="Length Y")
        row.prop(settings, "size_z", text="Height Z")
        
        layout.separator()
        
        layout.label(text="Noise / Generation Mode:")
        layout.prop(settings, "use_perlin_noise", text="Use Perlin Noise")
        if settings.use_perlin_noise:
            box = layout.box()
            box.prop(settings, "perlin_scale")
            box.prop(settings, "perlin_threshold")
            box.prop(settings, "perlin_offset")
        else:
            layout.prop(settings, "random_fill", text="Random Fill")
            if settings.random_fill:
                box = layout.box()
                box.prop(settings, "fill_probability")
        
        layout.separator()
        
        layout.label(text="Deformations:")
        layout.prop(settings, "redondear_esquinas", text="Round Corners")
        if settings.redondear_esquinas:
            box = layout.box()
            box.prop(settings, "intensidad_redondeo")
            
        layout.prop(settings, "esferizar_malla", text="Spherize Mesh")
        if settings.esferizar_malla:
            box = layout.box()
            box.prop(settings, "intensidad_esferizado")
            
        layout.separator()
        
        layout.label(text="Material Slots (Asignar Materiales):")
        box_mat = layout.box()
        box_mat.prop(settings, "top_material", text="Top (Suelo/Hierba)")
        box_mat.prop(settings, "bottom_material", text="Bottom (Suelo/Base)")
        box_mat.prop(settings, "adjacent_material", text="Adjacent (Lados Bloque Superior)")
        box_mat.prop(settings, "general_material", text="General (Lados Bloques Inferiores/Roca)")
        
        layout.separator()
        
        layout.label(text="Planar Holes (Huecos Planos):")
        box_holes = layout.box()
        row = box_holes.row(align=True)
        row.operator("voxel.add_hole", text="Add Hole", icon='ADD')
        row.operator("voxel.remove_hole", text="Remove Active", icon='REMOVE')
        
        if len(settings.holes) > 0:
            box_holes.prop(settings, "active_hole_index", text="Selected")
            idx = settings.active_hole_index
            if 0 <= idx < len(settings.holes):
                hole = settings.holes[idx]
                col = box_holes.column(align=True)
                col.label(text="Relative Position:")
                col.prop(hole, "pos_x", text="X (Width)")
                col.prop(hole, "pos_y", text="Y (Length)")
                col.prop(hole, "pos_z", text="Z (Height)")
                
                col.separator()
                col.label(text="Hole Size (Voxel dimensions):")
                col.prop(hole, "size_x", text="Size X")
                col.prop(hole, "size_y", text="Size Y")
                col.prop(hole, "size_z", text="Size Z")
        
        layout.separator()
        
        layout.operator("voxel.randomize_settings", icon='FILE_REFRESH')
        layout.operator("voxel.generate_mesh", icon='MESH_DATA')
        
        layout.separator()
        layout.label(text="Note: You can also use Empties named 'Hole*'", icon='INFO')

# --- Voxel Hole Property Group & Operators ---

class VoxelHoleProperty(bpy.types.PropertyGroup):
    pos_x: bpy.props.FloatProperty(name="Pos X", default=0.0)
    pos_y: bpy.props.FloatProperty(name="Pos Y", default=0.0)
    pos_z: bpy.props.FloatProperty(name="Pos Z", default=0.0)
    
    size_x: bpy.props.IntProperty(name="Size X", default=1, min=1)
    size_y: bpy.props.IntProperty(name="Size Y", default=1, min=1)
    size_z: bpy.props.IntProperty(name="Size Z", default=1, min=1)

class VOXEL_OT_AddHole(bpy.types.Operator):
    bl_idname = "voxel.add_hole"
    bl_label = "Add Voxel Hole"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.voxel_settings
        settings.holes.add()
        settings.active_hole_index = len(settings.holes) - 1
        return {'FINISHED'}

class VOXEL_OT_RemoveHole(bpy.types.Operator):
    bl_idname = "voxel.remove_hole"
    bl_label = "Remove Voxel Hole"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.voxel_settings
        if len(settings.holes) > 0:
            idx = settings.active_hole_index
            settings.holes.remove(idx)
            settings.active_hole_index = max(0, idx - 1)
        return {'FINISHED'}

# --- Properties Registration ---

class VoxelSettings(bpy.types.PropertyGroup):
    size_x: bpy.props.IntProperty(name="Width X", default=10, min=1)
    size_y: bpy.props.IntProperty(name="Length Y", default=10, min=1)
    size_z: bpy.props.IntProperty(name="Height Z", default=10, min=1)
    
    random_fill: bpy.props.BoolProperty(name="Random Fill", default=False)
    fill_probability: bpy.props.FloatProperty(name="Fill Probability", default=0.5, min=0.0, max=1.0)
    
    use_perlin_noise: bpy.props.BoolProperty(name="Use Perlin Noise", default=True)
    perlin_scale: bpy.props.FloatProperty(name="Perlin Scale", default=0.1, min=0.01)
    perlin_threshold: bpy.props.FloatProperty(name="Perlin Threshold", default=0.3, min=-1.0, max=1.0)
    perlin_offset: bpy.props.FloatVectorProperty(name="Perlin Offset", default=(0.0, 0.0, 0.0))
    
    redondear_esquinas: bpy.props.BoolProperty(name="Round Corners", default=False)
    intensidad_redondeo: bpy.props.IntProperty(name="Rounding Intensity", default=1, min=1, max=10)
    
    esferizar_malla: bpy.props.BoolProperty(name="Spherize Mesh", default=False)
    intensidad_esferizado: bpy.props.IntProperty(name="Spherize Intensity", default=1, min=1)
    
    bottom_material: bpy.props.PointerProperty(
        name="Bottom Material",
        type=bpy.types.Material
    )
    general_material: bpy.props.PointerProperty(
        name="General Material",
        type=bpy.types.Material
    )
    top_material: bpy.props.PointerProperty(
        name="Top Material",
        type=bpy.types.Material
    )
    adjacent_material: bpy.props.PointerProperty(
        name="Adjacent Material",
        type=bpy.types.Material
    )
    
    holes: bpy.props.CollectionProperty(type=VoxelHoleProperty)
    active_hole_index: bpy.props.IntProperty(name="Active Hole Index", default=0)

classes = (
    VoxelHoleProperty,
    VOXEL_OT_AddHole,
    VOXEL_OT_RemoveHole,
    VoxelSettings,
    VOXEL_OT_GenerateVoxelMesh,
    VOXEL_OT_RandomizeSettings,
    VOXEL_PT_GeneratorPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.voxel_settings = bpy.props.PointerProperty(type=VoxelSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.voxel_settings

if __name__ == "__main__":
    register()
