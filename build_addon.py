import os
import zipfile

# Configuration
addon_folder_name = "voxel_island_generator"
zip_filename = f"{addon_folder_name}.zip"

source_py = "voxel_island_generator.py"
source_blend = "voxel_island_generator.blend"

def build_zip():
    # Verify files exist
    if not os.path.exists(source_py):
        print(f"Error: Source file '{source_py}' not found in the current directory.")
        return
        
    print(f"Creating installable Blender addon ZIP: {zip_filename}...")
    
    try:
        # Create ZIP file
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Package the main python file, renaming it to __init__.py inside the addon folder
            zipf.write(source_py, os.path.join(addon_folder_name, "__init__.py"))
            print(f" -> Added {source_py} as {addon_folder_name}/__init__.py")
            
            # 2. Package the material library blend file inside the addon folder
            if os.path.exists(source_blend):
                zipf.write(source_blend, os.path.join(addon_folder_name, source_blend))
                print(f" -> Added {source_blend} as {addon_folder_name}/{source_blend}")
            else:
                print(f"Warning: {source_blend} not found! The zip will build without it (fallbacks will be used).")
                
        print("\nBuild complete! You can now distribute or install 'voxel_island_generator.zip' directly in Blender.")
        
    except Exception as e:
        print(f"Error during packaging: {e}")

if __name__ == "__main__":
    build_zip()
