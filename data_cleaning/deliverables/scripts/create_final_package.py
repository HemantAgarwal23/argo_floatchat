"""
Final package creation utility - Creates delivery ZIP with all components
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_final_package():
    """Create complete delivery package with all ARGO database components"""
    timestamp = datetime.now().strftime('%Y%m%d')
    package_name = f"argo_database_delivery_{timestamp}"
    
    print(f"📦 Creating final delivery package: {package_name}")
    
    # Create package directory
    os.makedirs(f"deliverables/{package_name}", exist_ok=True)
    
    # Copy essential files
    files_to_include = [
        "data/exports/argo_database_20250914.sql.gz",
        "data/exports/argo_metadata_summaries.json"
    ]
    
    copied_files = []
    for file_path in files_to_include:
        if os.path.exists(file_path):
            shutil.copy2(file_path, f"deliverables/{package_name}/")
            copied_files.append(os.path.basename(file_path))
            print(f"✅ Included: {os.path.basename(file_path)}")
        else:
            print(f"⚠️ Missing: {file_path}")
    
    # Create simple README
    readme = f"""# ARGO Database Delivery Package

**Delivered:** {datetime.now().strftime('%Y-%m-%d')}
**For:** Chatbot Team
**From:** Database Team

## Files Included
- `argo_database_20250914.sql.gz` - Complete PostgreSQL database (747.5 MB)
- `argo_metadata_summaries.json` - Profile summaries for vector search (2,000 summaries)

## Quick Start
1. Restore database: `gunzip -c argo_database_20250914.sql.gz | psql -d argo_database`
2. Load summaries: `python -c "import json; print(len(json.load(open('argo_metadata_summaries.json'))['summaries']))"`

## Database Stats  
- **122,215+ ARGO profiles**
- **Indian Ocean coverage (2019-2025)**
- **Quality-controlled oceanographic data**
- **Ready for chatbot integration**

## Support
Contact the database team for any questions about the data structure.
"""
    
    with open(f"deliverables/{package_name}/README.md", 'w') as f:
        f.write(readme)
    
    # Create ZIP
    zip_filename = f"deliverables/{package_name}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(f"deliverables/{package_name}"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, f"deliverables/{package_name}")
                zipf.write(file_path, arcname)
    
    # Clean up temp directory
    shutil.rmtree(f"deliverables/{package_name}")
    
    # Get package size
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print(f"\n✅ FINAL PACKAGE READY!")
    print(f"📦 Package: {zip_filename}")  
    print(f"📏 Size: {size_mb:.1f} MB")
    print(f"📋 Contains: {len(copied_files)} essential files")
    print(f"🎯 Ready to deliver to Medhul & Hemant!")
    
    return zip_filename

if __name__ == "__main__":
    create_final_package()
