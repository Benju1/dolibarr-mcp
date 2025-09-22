#!/usr/bin/env python3
"""Environment setup script for Dolibarr MCP development."""

import os
import subprocess
import sys
import platform
import shutil

def run_command(command, shell=False):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        command_str = ' '.join(command) if isinstance(command, list) else command
        print(f"✓ {command_str}")
        return True
    except subprocess.CalledProcessError as e:
        command_str = ' '.join(command) if isinstance(command, list) else command
        print(f"✗ {command_str}")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        return False

def setup_environment():
    """Set up the development environment."""
    print("\n" + "="*50)
    print("Dolibarr MCP Development Environment Setup")
    print("="*50 + "\n")
    
    # Determine platform-specific paths
    if platform.system() == "Windows":
        venv_name = "venv_dolibarr"
        python_exe = os.path.join(venv_name, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_name, "Scripts", "pip.exe")
        activate_script = os.path.join(venv_name, "Scripts", "activate.bat")
    else:
        venv_name = "venv_dolibarr"
        python_exe = os.path.join(venv_name, "bin", "python")
        pip_exe = os.path.join(venv_name, "bin", "pip")
        activate_script = f"source {os.path.join(venv_name, 'bin', 'activate')}"
    
    # Create virtual environment
    print("1. Creating virtual environment...")
    if not run_command([sys.executable, "-m", "venv", venv_name]):
        print("Failed to create virtual environment!")
        return False
    
    # Ensure pip is installed
    print("\n2. Ensuring pip is installed...")
    run_command([python_exe, "-m", "ensurepip", "--upgrade"])
    
    # Upgrade pip
    print("\n3. Upgrading pip, setuptools, and wheel...")
    if not run_command([python_exe, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]):
        print("Failed to upgrade pip!")
        return False
    
    # Install requirements
    print("\n4. Installing requirements...")
    if os.path.exists("requirements.txt"):
        if not run_command([pip_exe, "install", "-r", "requirements.txt"]):
            print("Failed to install requirements!")
            return False
    
    # Install package in editable mode
    print("\n5. Installing dolibarr-mcp package...")
    if not run_command([pip_exe, "install", "-e", "."]):
        print("Failed to install package!")
        return False
    
    # Create .env file if it doesn't exist
    print("\n6. Setting up configuration...")
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ Created .env from .env.example")
        else:
            with open(".env", "w") as f:
                f.write("# Dolibarr MCP Configuration\n")
                f.write("DOLIBARR_URL=https://your-dolibarr-instance.com/api/index.php\n")
                f.write("DOLIBARR_API_KEY=your_api_key_here\n")
                f.write("LOG_LEVEL=INFO\n")
            print("✓ Created default .env file")
        print("  ⚠ Please edit .env with your Dolibarr credentials")
    else:
        print("✓ .env file already exists")
    
    # Test import
    print("\n7. Testing installation...")
    test_command = [python_exe, "-c", "from dolibarr_mcp.config import Config; print('✓ Import test passed')"]
    if run_command(test_command):
        print("\n" + "="*50)
        print("✓ Setup Complete!")
        print("="*50)
        print(f"\nVirtual environment: {os.path.abspath(venv_name)}")
        print(f"\nTo activate the environment:")
        print(f"  {activate_script}")
        print(f"\nTo run the server:")
        print(f"  python -m dolibarr_mcp")
        return True
    else:
        print("\n✗ Installation test failed!")
        return False

if __name__ == "__main__":
    if setup_environment():
        sys.exit(0)
    else:
        sys.exit(1)
