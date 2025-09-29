#!/usr/bin/env python3
"""
Cleanup Script - Remove temporary and unnecessary files
"""

import os
import sys
from pathlib import Path
import glob

def cleanup_pipeline():
    """Clean up temporary files and cache"""
    print("🧹 Cleaning up pipeline...")
    
    # Remove Python cache
    cache_dirs = glob.glob("**/__pycache__", recursive=True)
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            os.system(f"rmdir /s /q {cache_dir}")
            print(f"  ✅ Removed {cache_dir}")
    
    # Remove temporary files
    temp_files = glob.glob("**/*.tmp", recursive=True)
    temp_files.extend(glob.glob("**/*.temp", recursive=True))
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"  ✅ Removed {temp_file}")
    
    # Remove state files for completed years
    state_files = glob.glob("*_state_*.json")
    state_files.extend(glob.glob("*_verification_*.json"))
    state_files.extend(glob.glob("deliverables_state_*.json"))
    
    for state_file in state_files:
        if os.path.exists(state_file):
            os.remove(state_file)
            print(f"  ✅ Removed state file: {state_file}")
    
    print("✅ Cleanup completed!")

if __name__ == "__main__":
    cleanup_pipeline()
