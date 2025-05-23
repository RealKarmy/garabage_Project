#!/usr/bin/env python3
import os
import subprocess
import sys

def create_project():
    print("🚀 Setting up Egyptian Donation Platform...")
    
    # Create directory structure
    if not os.path.exists('egyptian-donation-platform'):
        os.makedirs('egyptian-donation-platform/frontend')
        print("✅ Created project directories")
    
    os.chdir('egyptian-donation-platform')
    
    # Create virtual environment
    subprocess.run([sys.executable, '-m', 'venv', 'venv'])
    print("✅ Created virtual environment")
    
    # Activate and install packages
    if os.name == 'nt':  # Windows
        pip_path = 'venv\\Scripts\\pip.exe'
    else:  # Linux/Mac
        pip_path = 'venv/bin/pip'
    
    subprocess.run([pip_path, 'install', 'Flask==2.3.3', 'Flask-CORS==4.0.0'])
    print("✅ Installed dependencies")
    
    print("\n🎉 Setup complete!")
    print("📁 Now copy the files to:")
    print("   - app.py → egyptian-donation-platform/")
    print("   - requirements.txt → egyptian-donation-platform/")
    print("   - frontend files → egyptian-donation-platform/frontend/")
    print("\n🚀 Then run: python app.py")

if __name__ == "__main__":
    create_project()