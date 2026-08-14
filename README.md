# blender-voxel-island-generator
Blender plugin for procedurally generating voxel-based floating islands. Inspired by Minecraft.
# Voxel Island Generator for Blender (Voxel Mesh Pro)

Voxel Island Generator es un addon gratuito para Blender 2.80+ que permite generar mallas voxelizadas procedurales 3D directamente en la vista.
![Texto alternativo del GIF](media/IslaGenerator.gif)

## Características
* **Generación procedural:** Genera islas completas basadas en rejillas 3D de vóxeles.
* **Ruido Perlin 3D:** Crea huecos y formas orgánicas de manera matemática.
* **Deformaciones:** Incluye herramientas integradas de redondeo de esquinas y esferizado de mallas.
* **Huecos Planos (Planar Holes):** Corta secciones completas de la isla introduciendo coordenadas o usando objetos *Empty* interactivos en la escena.
* **Slots de Materiales:** Asigna materiales diferentes de Blender de manera automática a la parte superior (césped), inferior (base/tierra), laterales y aristas.

## Instalación
1. Descarga el archivo `voxel_island_generator.py` de este repositorio.
2. Abre Blender y ve a `Edit > Preferences > Add-ons` (o *Extensions* en Blender 4.2+).
3. Haz clic en **Install...** (o *Install from Disk*).
4. Selecciona el archivo descargado y asegúrate de marcar la casilla para activarlo.
5. Abre la barra lateral (`N`) en el Viewport 3D y busca la pestaña **Voxel Mesh Pro**.

## Créditos
* Este addon es un port a Blender de la herramienta *VoxelMeshPro* para Unity de Hectoranpe Software.