#!/usr/bin/env python3
"""
Extract INSERT statements for argo_profiles from the SQL dump
"""
import re
import sys
from pathlib import Path

def extract_profile_inserts(dump_file, output_file):
    """Extract INSERT statements for argo_profiles table"""
    print(f"Reading dump file: {dump_file}")
    
    with open(dump_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all INSERT statements for argo_profiles
    pattern = r'INSERT INTO public\.argo_profiles[^;]+;'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    
    print(f"Found {len(matches)} INSERT statements for argo_profiles")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(match + '\n')
    
    print(f"Extracted INSERT statements to: {output_file}")

if __name__ == "__main__":
    dump_file = Path(__file__).parent / "temp_argo_dump.sql"
    output_file = Path(__file__).parent / "profile_inserts.sql"
    
    if not dump_file.exists():
        print(f"Error: Dump file not found: {dump_file}")
        sys.exit(1)
    
    extract_profile_inserts(dump_file, output_file)
