#!/usr/bin/env python3
"""Setup script for Dolibarr MCP development environment."""

import os
import subprocess
import sys
import platform

def run_command(command, shell=False):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        print(f"✅ {' '.join(command) if isinstance(command, list) else command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(command) if isinstance(command, list) else command}")
        print(f"Error: {e.stderr}")
        return None

def setup_development_environment():
    """Set up the development environment for Dolibarr MCP."""
    print("🚀 Setting up Dolibarr MCP Development Environment...")
    
    # Determine platform-specific paths
    if platform.system() == "Windows":
        venv_name = "venv_dolibarr"
        python_exe = os.path.join(venv_name, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_name, "Scripts", "pip.exe")
    else:
        venv_name = "venv_dolibarr"
        python_exe = os.path.join(venv_name, "bin", "python")
        pip_exe = os.path.join(venv_name, "bin", "pip")
    
    # Create virtual environment
    print(f"📦 Creating virtual environment: {venv_name}")
    if run_command([sys.executable, "-m", "venv", venv_name]):
        print(f"Virtual environment created at: {os.path.abspath(venv_name)}")
    
    # Upgrade pip
    print("⬆️  Upgrading pip...")
    run_command([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        print("📋 Installing requirements from requirements.txt...")
        run_command([pip_exe, "install", "-r", "requirements.txt"])
    
    # Install package in development mode
    print("🔧 Installing package in development mode...")
    run_command([pip_exe, "install", "-e", "."])
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("📝 Creating .env file from template...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("⚠️  Please edit .env file with your Dolibarr credentials")
        else:
            with open(".env", "w") as f:
                f.write("# Dolibarr MCP Configuration\n")
                f.write("DOLIBARR_URL=https://your-dolibarr-instance.com/api/index.php\n")
                f.write("DOLIBARR_API_KEY=your_api_key_here\n")
                f.write("LOG_LEVEL=INFO\n")
            print("⚠️  Please edit .env file with your Dolibarr credentials")
    
    print("\n✅ Development environment setup complete!")
    print(f"🐍 Python executable: {os.path.abspath(python_exe)}")
    print(f"📁 Virtual environment: {os.path.abspath(venv_name)}")
    print("\n🔧 Next steps:")
    print("1. Edit .env file with your Dolibarr instance details")
    print("2. Test the connection: python -m dolibarr_mcp.dolibarr_mcp_server")
    print("3. Or run with Docker: docker-compose up")

def test_installation():
    """Test if the installation works."""
    print("\n🧪 Testing installation...")
    
    # Determine platform-specific python path
    if platform.system() == "Windows":
        python_exe = os.path.join("venv_dolibarr", "Scripts", "python.exe")
    else:
        python_exe = os.path.join("venv_dolibarr", "bin", "python")
    
    # Test import
    test_command = [python_exe, "-c", "from dolibarr_mcp.config import Config; print('✅ Import test passed')"]
    if run_command(test_command):
        print("✅ Installation test passed!")
        return True
    else:
        print("❌ Installation test failed!")
        return False

if __name__ == "__main__":
    setup_development_environment()
    test_installation()
