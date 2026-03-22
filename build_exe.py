#!/usr/bin/env python3
"""
Build script for Pro_Browser to create a standalone EXE file
"""

import os
import sys
import subprocess
import shutil

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import PyQt6
        import PyQt6.QtWebEngineWidgets
        print("✓ PyQt6 and QtWebEngineWidgets are installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install: pip install PyQt6 PyQt6-WebEngine")
        return False
    return True

def create_build_script():
    """Create the PyInstaller build script"""
    
    # Files to include
    additional_files = [
        "Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png",
        "youtube pro_browser background theme.png",
        "users.json"
    ]
    
    # Build command
    cmd = [
        "pyinstaller",
        "--name=Pro_Browser",
        "--windowed",  # No console window
        "--onefile",   # Single executable
        "--clean",     # Clean PyInstaller cache
        "--icon=Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png",
        "--add-data=Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png:.",
        "--add-data=youtube pro_browser background theme.png:.",
        "--add-data=users.json:.",
        "--hidden-import=PyQt6.QtWebEngineWidgets",
        "--hidden-import=PyQt6.QtWebEngineCore",
        "--hidden-import=hashlib",
        "--hidden-import=json",
        "--hidden-import=random",
        "--hidden-import=os",
        "--hidden-import=sys",
        "--hidden-import=socket",
        "--hidden-import=threading",
        "--hidden-import=time",
        "--hidden-import=platform",
        "--hidden-import=shutil",
        "--hidden-import=tempfile",
        "--hidden-import=subprocess",
        "--hidden-import=datetime",
        "--hidden-import=QApplication",
        "--hidden-import=QMainWindow",
        "--hidden-import=QWidget",
        "--hidden-import=QTabWidget",
        "--hidden-import=QVBoxLayout",
        "--hidden-import=QHBoxLayout",
        "--hidden-import=QPushButton",
        "--hidden-import=QLineEdit",
        "--hidden-import=QDialog",
        "--hidden-import=QLabel",
        "--hidden-import=QComboBox",
        "--hidden-import=QTableWidget",
        "--hidden-import=QTableWidgetItem",
        "--hidden-import=QHeaderView",
        "--hidden-import=QSlider",
        "--hidden-import=QFrame",
        "--hidden-import=QGridLayout",
        "--hidden-import=QMessageBox",
        "--hidden-import=QToolBar",
        "--hidden-import=QMenu",
        "--hidden-import=QInputDialog",
        "--hidden-import=QFileDialog",
        "--hidden-import=QScrollArea",
        "--hidden-import=QCheckBox",
        "--hidden-import=QTextEdit",
        "--hidden-import=QSize",
        "--hidden-import=QUrl",
        "--hidden-import=Qt",
        "--hidden-import=QTimer",
        "--hidden-import=QSettings",
        "--hidden-import=QEvent",
        "--hidden-import=pyqtSignal",
        "--hidden-import=QPoint",
        "--hidden-import=QMimeData",
        "--hidden-import=QDrag",
        "--hidden-import=QPainter",
        "--hidden-import=QColor",
        "--hidden-import=QPen",
        "--hidden-import=QAction",
        "--hidden-import=QKeySequence",
        "--hidden-import=QPixmap",
        "--hidden-import=QIcon",
        "--hidden-import=QFont",
        "--hidden-import=QWebEngineView",
        "--collect-all=PyQt6",
        "Pro_Browser.py"
    ]
    
    return cmd

def run_build():
    """Run the PyInstaller build process"""
    print("🚀 Starting Pro_Browser EXE build process...")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Running in virtual environment")
    else:
        print("⚠ Warning: Not running in virtual environment")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Create build command
    cmd = create_build_script()
    
    print("\n📋 Build command:")
    print(" ".join(cmd))
    
    # Run the build
    print("\n🔨 Building EXE file...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Build completed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Build failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_distribution_package():
    """Create a distribution package with all necessary files"""
    print("\n📦 Creating distribution package...")
    
    # Check if dist directory exists
    if not os.path.exists("dist"):
        print("✗ No dist directory found. Build may have failed.")
        return False
    
    # Check if executable exists
    exe_name = "Pro_Browser.exe" if os.name == 'nt' else "Pro_Browser"
    exe_path = os.path.join("dist", exe_name)
    
    if not os.path.exists(exe_path):
        print(f"✗ Executable not found at {exe_path}")
        return False
    
    # Create distribution directory
    dist_dir = "Pro_Browser_Distribution"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copy executable
    shutil.copy2(exe_path, os.path.join(dist_dir, exe_name))
    
    # Create README
    readme_content = """# Pro_Browser Distribution

This is a standalone executable of Pro_Browser.

## Requirements
- Windows 10/11 (for .exe version)
- 64-bit system recommended
- At least 512MB RAM
- Internet connection for browsing

## Usage
Simply run Pro_Browser.exe to start the browser.

## Features
- User account system with admin privileges
- Tab management with drag & drop
- Programming environment with VSCode-like features
- Task manager integration
- Bookmark management
- Settings customization
- Password manager
- System information

## Notes
- First run will create a users.json file for account management
- Default admin account: admin@probrowser.com / admin123
- Profile pictures are stored in the avatars/ directory
- Settings are saved in the application data directory

## Troubleshooting
If the application doesn't start:
1. Make sure you have the latest Windows updates
2. Try running as administrator
3. Check if your antivirus is blocking the application
4. Ensure you have enough disk space (at least 100MB free)
"""
    
    with open(os.path.join(dist_dir, "README.txt"), "w") as f:
        f.write(readme_content)
    
    # Create license file
    license_content = """MIT License

Copyright (c) 2026 Pro_Browser

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open(os.path.join(dist_dir, "LICENSE.txt"), "w") as f:
        f.write(license_content)
    
    print(f"✓ Distribution package created in '{dist_dir}'")
    print(f"✓ Executable size: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
    
    return True

def main():
    """Main build process"""
    print("🎯 Pro_Browser EXE Builder")
    print("=" * 50)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Run build process
    if run_build():
        if create_distribution_package():
            print("\n🎉 Build and packaging completed successfully!")
            print("\n📁 Files created:")
            print("  - dist/Pro_Browser.exe (main executable)")
            print("  - Pro_Browser_Distribution/ (complete package)")
            print("\n🚀 You can now distribute the Pro_Browser_Distribution folder!")
        else:
            print("\n⚠ Build succeeded but packaging failed.")
    else:
        print("\n❌ Build process failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())