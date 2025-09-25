#!/usr/bin/env python3
"""
ARGO FloatChat Setup Script
Comprehensive setup script for the ARGO FloatChat platform
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def setup_backend():
    """Set up the backend environment"""
    print("\n🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Create virtual environment
    if not run_command("python -m venv venv", cwd=backend_dir):
        return False
    
    # Determine activation script based on OS
    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_script = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install --upgrade pip", cwd=backend_dir):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=backend_dir):
        return False
    
    print("✅ Backend setup complete")
    return True

def setup_frontend():
    """Set up the frontend environment"""
    print("\n🎨 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Create virtual environment
    if not run_command("python -m venv venv", cwd=frontend_dir):
        return False
    
    # Determine activation script based on OS
    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_script = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install --upgrade pip", cwd=frontend_dir):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=frontend_dir):
        return False
    
    print("✅ Frontend setup complete")
    return True

def create_env_file():
    """Create environment file from template"""
    print("\n📝 Creating environment file...")
    
    backend_dir = Path("backend")
    env_template = backend_dir / "env_template.txt"
    env_file = backend_dir / ".env"
    
    if env_template.exists() and not env_file.exists():
        with open(env_template, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Environment file created")
        print("⚠️  Please edit backend/.env with your configuration")
        return True
    else:
        print("⚠️  Environment file already exists or template not found")
        return True

def main():
    """Main setup function"""
    print("🌊 ARGO FloatChat Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Set up backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)
    
    # Set up frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit backend/.env with your configuration")
    print("2. Set up your PostgreSQL database")
    print("3. Run: cd backend && python scripts/setup_database.py")
    print("4. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
    print("5. Start the frontend: cd frontend && source venv/bin/activate && streamlit run floatchat_app.py")
    print("\nFor detailed instructions, see README.md")

if __name__ == "__main__":
    main()
