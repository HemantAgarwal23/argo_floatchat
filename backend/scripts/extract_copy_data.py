#!/usr/bin/env python3
"""
Extract COPY data for argo_profiles from the SQL dump
"""
import sys
from pathlib import Path

def extract_copy_data(dump_file, output_file):
    """Extract COPY data for argo_profiles table"""
    print(f"Reading dump file: {dump_file}")
    
    copy_started = False
    copy_lines = []
    
    with open(dump_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Check if this is the start of COPY for argo_profiles
            if 'COPY public.argo_profiles' in line:
                copy_started = True
                print("Found COPY statement for argo_profiles")
                continue
            
            # If we're in the COPY data section
            if copy_started:
                # Check if this is the end of COPY data
                if line == '\\.' or line == '\\.':
                    break
                # Add data lines
                if line and not line.startswith('--'):
                    copy_lines.append(line)
    
    print(f"Extracted {len(copy_lines)} data lines")
    
    # Write the COPY statement and data
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("COPY public.argo_profiles (profile_id, float_id, cycle_number, latitude, longitude, profile_date, profile_time, julian_day, position_qc, pressure, depth, temperature, salinity, temperature_qc, salinity_qc, dissolved_oxygen, ph_in_situ, nitrate, chlorophyll_a, dissolved_oxygen_qc, ph_qc, nitrate_qc, chlorophyll_qc, platform_number, project_name, institution, data_mode, n_levels, max_pressure, created_at) FROM stdin;\n")
        for line in copy_lines:
            f.write(line + '\n')
        f.write('\\.\n')
    
    print(f"Extracted COPY data to: {output_file}")

if __name__ == "__main__":
    dump_file = Path(__file__).parent / "temp_argo_dump.sql"
    output_file = Path(__file__).parent / "profile_copy_data.sql"
    
    if not dump_file.exists():
        print(f"Error: Dump file not found: {dump_file}")
        sys.exit(1)
    
    extract_copy_data(dump_file, output_file)
