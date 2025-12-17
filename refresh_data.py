import os
import shutil
import subprocess
import sys
from pathlib import Path
import json

def main():
    print("Refresh Data Script")
    print("-------------------")
    
    # 1. Run the pipeline
    print("1. Running Python Pipeline...")
    ret = subprocess.call([sys.executable, "run_pipeline_new.py"])
    
    if ret != 0:
        print("Error: Pipeline execution failed.")
        sys.exit(ret)
        
    # 2. Copy output to client/public/data
    print("\n2. Copying results to client...")
    
    src = Path("output/pipeline_results_new.json")
    dest_dir = Path("client/public/data")
    dest_file = dest_dir / "pipeline_results.json"
    
    if not src.exists():
        print(f"Error: Source file {src} not found!")
        sys.exit(1)
        
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_file)
    
    print(f"Copied {src} to {dest_file}")
    
    # Verify content
    try:
        data = json.loads(dest_file.read_text(encoding='utf-8'))
        print(f"Success! Data loaded for tender: {data.get('processing', {}).get('selected_rfp', {}).get('tender_id')}")
    except Exception as e:
        print(f"Warning: Could not verify JSON content: {e}")

if __name__ == "__main__":
    main()
