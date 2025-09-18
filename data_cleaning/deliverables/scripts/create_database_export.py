"""
Database export utility - Creates compressed PostgreSQL dumps
"""

import subprocess
import gzip
import os
from datetime import datetime

def create_database_export():
    """Create compressed PostgreSQL database export with timestamp"""
    # Database configuration
    DATABASE_NAME = "argo_database"
    
    timestamp = datetime.now().strftime('%Y%m%d')
    export_filename = f"data/exports/argo_database_{timestamp}.sql.gz"
    
    # Ensure export directory exists
    os.makedirs("data/exports", exist_ok=True)
    
    # PostgreSQL dump command - use environment variables
    db_user = os.getenv('DB_USER', 'username')
    db_host = os.getenv('DB_HOST', 'localhost')
    
    cmd = [
        'pg_dump',
        '-U', db_user,
        '-h', db_host,
        'argo_database',
        '--clean', '--create', '--verbose'
    ]
    
    print(f"🔄 Exporting database: {DATABASE_NAME}")
    print(f"📄 Output file: {export_filename}")
    
    try:
        # Create compressed export
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            stdout, stderr = proc.communicate()
            
            if proc.returncode == 0:
                # Compress the output
                with gzip.open(export_filename, 'wt') as f:
                    f.write(stdout)
                
                print(f"✅ Database exported successfully to: {export_filename}")
                
                # Check file size
                size_mb = os.path.getsize(export_filename) / (1024 * 1024)
                print(f"📏 File size: {size_mb:.1f} MB")
                
                return export_filename
            else:
                print(f"❌ Export failed!")
                print(f"Error: {stderr}")
                return None
                
    except Exception as e:
        print(f"❌ Export failed with exception: {e}")
        return None

if __name__ == "__main__":
    create_database_export()
