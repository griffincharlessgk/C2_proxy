#!/usr/bin/env python3
"""
Script to test and validate dependencies
"""

import sys
import subprocess
import importlib
from pathlib import Path

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        return True, "OK"
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {e}"

def get_package_version(module_name):
    """Get version of installed package"""
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, '__version__'):
            return module.__version__
        elif hasattr(module, 'VERSION'):
            return str(module.VERSION)
        elif hasattr(module, 'version'):
            return str(module.version)
        else:
            return "Unknown"
    except:
        return "Not installed"

def test_core_dependencies():
    """Test core dependencies"""
    print("🧪 TESTING CORE DEPENDENCIES")
    print("-" * 50)
    
    core_deps = [
        ('requests', 'requests'),
        ('bs4', 'beautifulsoup4'),
        ('urllib3', 'urllib3'),
        ('socks', 'PySocks'),
        ('cryptography', 'cryptography'),
        ('jwt', 'PyJWT'),
        ('pymysql', 'PyMySQL'),
        ('psutil', 'psutil'),
        ('colorama', 'colorama'),
        ('future', 'future')
    ]
    
    results = []
    for module, package in core_deps:
        success, msg = test_import(module)
        version = get_package_version(module) if success else "Not installed"
        status = "✅" if success else "❌"
        
        print(f"{status} {package:20} | {version:15} | {msg}")
        results.append((package, success, version))
    
    return results

def test_web_dependencies():
    """Test web interface dependencies"""
    print("\n🌐 TESTING WEB INTERFACE DEPENDENCIES")
    print("-" * 50)
    
    web_deps = [
        ('flask', 'Flask'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('socketio', 'python-socketio'),
        ('engineio', 'python-engineio'),
        ('werkzeug', 'Werkzeug'),
        ('jinja2', 'Jinja2')
    ]
    
    results = []
    for module, package in web_deps:
        success, msg = test_import(module)
        version = get_package_version(module) if success else "Not installed"
        status = "✅" if success else "❌"
        
        print(f"{status} {package:20} | {version:15} | {msg}")
        results.append((package, success, version))
    
    return results

def test_optional_dependencies():
    """Test optional dependencies"""
    print("\n🔧 TESTING OPTIONAL DEPENDENCIES")
    print("-" * 50)
    
    optional_deps = [
        ('kamene', 'kamene'),
        ('scapy', 'scapy'),
        ('dns', 'dnspython'),
        ('stem', 'stem'),
        ('tldextract', 'tldextract'),
        ('xtelnet', 'xtelnet'),
        ('jsbeautifier', 'jsbeautifier'),
        ('pwinput', 'pwinput'),
        ('tabulate', 'tabulate'),
        ('google', 'google')
    ]
    
    results = []
    for module, package in optional_deps:
        success, msg = test_import(module)
        version = get_package_version(module) if success else "Not available"
        status = "✅" if success else "⚠️ "
        
        print(f"{status} {package:20} | {version:15} | {'Optional' if not success else 'Available'}")
        results.append((package, success, version))
    
    return results

def test_system_packages():
    """Test system-level packages"""
    print("\n🖥️  TESTING SYSTEM PACKAGES")
    print("-" * 50)
    
    # Check if system packages are available
    system_commands = [
        ('python3-flask', 'python3 -c "import flask"'),
        ('python3-socketio', 'python3 -c "import socketio"'),
        ('python3-socks', 'python3 -c "import socks"')
    ]
    
    for package, test_cmd in system_commands:
        try:
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
            success = result.returncode == 0
            status = "✅" if success else "❌"
            print(f"{status} {package:20} | {'Available' if success else 'Not installed'}")
        except Exception as e:
            print(f"❌ {package:20} | Error: {e}")

def generate_install_commands(core_results, web_results):
    """Generate installation commands for missing packages"""
    print("\n📦 MISSING PACKAGES INSTALLATION")
    print("-" * 50)
    
    missing_packages = []
    
    for package, success, version in core_results + web_results:
        if not success:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing core packages - install with:")
        print("```bash")
        print("# System packages (recommended)")
        system_packages = []
        for pkg in missing_packages:
            if pkg in ['Flask', 'Flask-SocketIO']:
                system_packages.append('python3-flask')
            elif pkg == 'python-socketio':
                system_packages.append('python3-socketio')
            elif pkg == 'PySocks':
                system_packages.append('python3-socks')
            elif pkg == 'beautifulsoup4':
                system_packages.append('python3-bs4')
            elif pkg == 'cryptography':
                system_packages.append('python3-cryptography')
            elif pkg == 'psutil':
                system_packages.append('python3-psutil')
            elif pkg == 'requests':
                system_packages.append('python3-requests')
        
        if system_packages:
            unique_system = list(set(system_packages))
            print(f"sudo apt install {' '.join(unique_system)}")
        
        print("\n# Or pip packages")
        print(f"pip install {' '.join(missing_packages)}")
        print("```")
    else:
        print("✅ All core packages are installed!")

def check_requirements_files():
    """Check if requirements files exist and are valid"""
    print("\n📄 CHECKING REQUIREMENTS FILES")
    print("-" * 50)
    
    req_files = [
        '/home/ubuntu/C2/requirements.txt',
        '/home/ubuntu/C2/bane/requirements.txt',
        '/home/ubuntu/C2/requirements-dev.txt',
        '/home/ubuntu/C2/requirements-minimal.txt',
        '/home/ubuntu/C2/requirements-full.txt'
    ]
    
    for req_file in req_files:
        path = Path(req_file)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                    non_comment_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
                    print(f"✅ {path.name:25} | {len(non_comment_lines)} dependencies")
            except Exception as e:
                print(f"❌ {path.name:25} | Error reading: {e}")
        else:
            print(f"❌ {path.name:25} | File not found")

def main():
    """Main test function"""
    print("🧪 C2 PROJECT DEPENDENCY TESTING")
    print("=" * 60)
    print("Testing all dependencies and system requirements")
    print("")
    
    # Test core dependencies
    core_results = test_core_dependencies()
    
    # Test web dependencies  
    web_results = test_web_dependencies()
    
    # Test optional dependencies
    optional_results = test_optional_dependencies()
    
    # Test system packages
    test_system_packages()
    
    # Check requirements files
    check_requirements_files()
    
    # Generate install commands
    generate_install_commands(core_results, web_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPENDENCY TEST SUMMARY")
    print("=" * 60)
    
    total_core = len(core_results)
    working_core = sum(1 for _, success, _ in core_results if success)
    
    total_web = len(web_results)
    working_web = sum(1 for _, success, _ in web_results if success)
    
    total_optional = len(optional_results)
    working_optional = sum(1 for _, success, _ in optional_results if success)
    
    print(f"🎯 Core Dependencies:     {working_core}/{total_core} working")
    print(f"🌐 Web Dependencies:      {working_web}/{total_web} working") 
    print(f"🔧 Optional Dependencies: {working_optional}/{total_optional} available")
    
    if working_core == total_core and working_web == total_web:
        print("\n🎉 ALL ESSENTIAL DEPENDENCIES ARE WORKING!")
        print("✅ Project is ready to run")
    elif working_core >= total_core * 0.8:
        print("\n⚠️  Most dependencies working, but some missing")
        print("💡 Check installation commands above")
    else:
        print("\n❌ CRITICAL DEPENDENCIES MISSING")
        print("🔧 Please install missing packages before running")

if __name__ == "__main__":
    main()
