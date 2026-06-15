import os
import shutil
import argparse

def create_release():
    source_dir = r"F:\progetti antigravity\wan2gp Davinci"
    release_dir = r"F:\progetti antigravity\Wan2GP_DaVinci_Release"
    
    # Items to include in the release
    include_items = [
        "src",
        "README.md",
        "requirements.txt",
        "start_wangp_services.bat",
        "spike_resolve.py" # just in case
    ]
    
    # Clear the release directory if it exists
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
        
    os.makedirs(release_dir)
    print(f"Created release directory at {release_dir}")
    
    for item in include_items:
        src_path = os.path.join(source_dir, item)
        dst_path = os.path.join(release_dir, item)
        
        if os.path.exists(src_path):
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'node_modules'))
            else:
                shutil.copy2(src_path, dst_path)
            print(f"Copied {item}")
        else:
            print(f"Warning: {item} not found in source directory.")
            
    # Copy plugin script separately (it needs to be in a specific format for distribution)
    plugin_release_dir = os.path.join(release_dir, "DaVinci_Plugin")
    os.makedirs(plugin_release_dir, exist_ok=True)
    plugin_src = os.path.join(source_dir, "src", "resolve_plugin")
    if os.path.exists(plugin_src):
        shutil.copytree(plugin_src, os.path.join(plugin_release_dir, "com.antigravity.wangp"), dirs_exist_ok=True)
        print("Packaged DaVinci Resolve plugin.")
        
    print("Release package created successfully!")

if __name__ == "__main__":
    create_release()
