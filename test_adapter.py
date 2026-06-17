import json
import os
from src.orchestrator.adapters.wangp_adapter import WanGPAdapter

manifest_path = r"F:\progetti antigravity\wan2gp Davinci\data\cache\job_76e3eced-56bf-4deb-a581-4d205acf2d8a_settings.json"
with open(manifest_path, 'r') as f:
    settings = json.load(f)
    
# Wait, the settings json is the WanGP settings, NOT the manifest!
# We need the manifest from the `job_..._manifest.json`!
