#!/usr/bin/env python3
"""
Script to analyze and update dependencies for C2 project
"""

import os
import sys
import re
import ast
import subprocess
from collections import defaultdict, Counter
from pathlib import Path

def extract_imports_from_file(file_path):
    """Extract imports from a Python file"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find import statements
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import',
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
                
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1).split('.')[0]
                    if not module.startswith('bane') and not module.startswith('.'):
                        imports.add(module)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imports

def get_all_imports():
    """Get all imports from the project"""
    project_root = Path("/home/ubuntu/C2")
    all_imports = Counter()
    
    # Analyze bane modules
    for py_file in project_root.rglob("*.py"):
        if "__pycache__" in str(py_file) or "venv" in str(py_file):
            continue
        imports = extract_imports_from_file(py_file)
        all_imports.update(imports)
    
    return all_imports

def get_standard_library_modules():
    """Get list of Python standard library modules"""
    standard_libs = {
        'os', 'sys', 'time', 'json', 'threading', 'subprocess', 'warnings',
        'datetime', 'typing', 'socket', 'random', 're', 'hashlib', 'base64',
        'urllib', 'ssl', 'struct', 'collections', 'smtplib', 'ftplib',
        'http', 'httplib', 'html', 'email', 'io', 'tempfile', 'shutil',
        'pathlib', 'itertools', 'functools', 'operator', 'copy', 'pickle',
        'csv', 'configparser', 'logging', 'argparse', 'getopt', 'platform',
        'signal', 'errno', 'stat', 'glob', 'uuid', 'hashlib', 'hmac',
        'secrets', 'gc', 'inspect', 'trace', 'traceback', 'weakref',
        'ast', 'dis', 'imp', 'importlib', 'keyword', 'pkgutil', 'types',
        'unittest', 'doctest', 'pdb', 'profile', 'pstats', 'timeit',
        'math', 'cmath', 'decimal', 'fractions', 'statistics', 'random',
        'bisect', 'heapq', 'array', 'queue', 'zlib', 'gzip', 'bz2', 'lzma',
        'tarfile', 'zipfile', 'sqlite3', 'dbm'
    }
    return standard_libs

def get_pip_package_mapping():
    """Map import names to pip package names"""
    return {
        'bs4': 'beautifulsoup4',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'sklearn': 'scikit-learn',
        'flask': 'Flask',
        'jwt': 'PyJWT',
        'socks': 'PySocks',
        'kamene': 'kamene',
        'scapy': 'scapy',
        'pymysql': 'PyMySQL',
        'xtelnet': 'xtelnet',
        'stem': 'stem',
        'google': 'google',
        'colorama': 'colorama',
        'dnspython': 'dnspython',
        'tldextract': 'tldextract',
        'pwinput': 'pwinput',
        'future': 'future',
        'cryptography': 'cryptography',
        'psutil': 'psutil',
        'tabulate': 'tabulate',
        'jsbeautifier': 'jsbeautifier',
        'bidict': 'bidict',
        'engineio': 'python-engineio',
        'socketio': 'python-socketio',
        'werkzeug': 'Werkzeug',
        'jinja2': 'Jinja2',
        'markupsafe': 'MarkupSafe',
        'itsdangerous': 'itsdangerous',
        'click': 'click',
        'blinker': 'blinker',
        'urllib3': 'urllib3',
        'charset_normalizer': 'charset-normalizer',
        'certifi': 'certifi',
        'idna': 'idna',
        'pycodestyle': 'pycodestyle',
        'pyflakes': 'pyflakes',
        'mccabe': 'mccabe',
        'flake8': 'flake8',
        'black': 'black',
        'pytest': 'pytest',
        'coverage': 'coverage',
        'pluggy': 'pluggy',
        'packaging': 'packaging',
        'iniconfig': 'iniconfig',
        'pathspec': 'pathspec',
        'platformdirs': 'platformdirs',
        'filelock': 'filelock'
    }

def check_package_availability(package):
    """Check if a package is available via pip"""
    try:
        result = subprocess.run([
            'python3', '-c', f'import {package}'
        ], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def categorize_dependencies():
    """Categorize dependencies by type"""
    all_imports = get_all_imports()
    standard_libs = get_standard_library_modules()
    pip_mapping = get_pip_package_mapping()
    
    categories = {
        'core_required': [],
        'web_interface': [],
        'security_tools': [],
        'optional': [],
        'unknown': []
    }
    
    # Core dependencies
    core_deps = {
        'requests', 'PySocks', 'bs4', 'pymysql', 'cryptography', 
        'future', 'psutil', 'json', 'urllib3'
    }
    
    # Web interface dependencies
    web_deps = {
        'flask', 'socketio', 'engineio', 'werkzeug', 'jinja2',
        'markupsafe', 'itsdangerous', 'click', 'blinker'
    }
    
    # Security/network tools
    security_deps = {
        'kamene', 'scapy', 'stem', 'dnspython', 'tldextract',
        'xtelnet', 'colorama', 'google'
    }
    
    # Optional dependencies
    optional_deps = {
        'tabulate', 'jsbeautifier', 'pwinput', 'bidict',
        'charset_normalizer', 'certifi', 'idna'
    }
    
    for module, count in all_imports.items():
        if module in standard_libs:
            continue
            
        pip_name = pip_mapping.get(module, module)
        available = check_package_availability(module)
        
        entry = {
            'import_name': module,
            'pip_name': pip_name,
            'usage_count': count,
            'available': available
        }
        
        if module in core_deps:
            categories['core_required'].append(entry)
        elif module in web_deps:
            categories['web_interface'].append(entry)
        elif module in security_deps:
            categories['security_tools'].append(entry)
        elif module in optional_deps:
            categories['optional'].append(entry)
        else:
            categories['unknown'].append(entry)
    
    return categories

def generate_requirements_content(categories):
    """Generate requirements.txt content"""
    content = []
    
    content.append("# C2 Hybrid Botnet Manager - Dependencies")
    content.append("# Generated automatically - DO NOT EDIT MANUALLY")
    content.append("")
    
    # Core dependencies
    content.append("# Core Dependencies (Required)")
    for dep in sorted(categories['core_required'], key=lambda x: x['pip_name']):
        if dep['available']:
            content.append(f"{dep['pip_name']}>=2.0.0")
        else:
            content.append(f"# {dep['pip_name']}>=2.0.0  # Not available")
    content.append("")
    
    # Web interface
    content.append("# Web Interface Dependencies")
    content.append("Flask>=2.0.0")
    content.append("Flask-SocketIO>=5.0.0")
    for dep in sorted(categories['web_interface'], key=lambda x: x['pip_name']):
        if dep['pip_name'] not in ['Flask', 'Flask-SocketIO'] and dep['available']:
            content.append(f"{dep['pip_name']}>=1.0.0")
    content.append("")
    
    # Security tools
    content.append("# Security & Network Tools (Optional)")
    for dep in sorted(categories['security_tools'], key=lambda x: x['pip_name']):
        if dep['available']:
            content.append(f"{dep['pip_name']}>=1.0.0")
        else:
            content.append(f"# {dep['pip_name']}>=1.0.0  # Optional - install manually if needed")
    content.append("")
    
    # Optional dependencies
    content.append("# Optional Dependencies (Enhanced Features)")
    for dep in sorted(categories['optional'], key=lambda x: x['pip_name']):
        if dep['available']:
            content.append(f"# {dep['pip_name']}>=1.0.0  # Optional")
    content.append("")
    
    # Development dependencies
    content.append("# Development Dependencies (Optional)")
    content.append("# pytest>=7.0.0")
    content.append("# coverage>=6.0.0")
    content.append("# flake8>=4.0.0")
    content.append("# black>=22.0.0")
    
    return '\n'.join(content)

def create_minimal_requirements():
    """Create minimal requirements.txt for essential functionality"""
    minimal = [
        "# Minimal Requirements for C2 Hybrid Botnet Manager",
        "# Core functionality only",
        "",
        "# Essential packages",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "cryptography>=3.4.0",
        "psutil>=5.8.0",
        "",
        "# Web interface (optional but recommended)",
        "Flask>=2.0.0",
        "Flask-SocketIO>=5.0.0",
        "",
        "# Network tools (install if available)",
        "PySocks>=1.7.0",
        "",
        "# System compatibility",
        "future>=0.18.0"
    ]
    return '\n'.join(minimal)

def main():
    """Main analysis function"""
    print("🔍 ANALYZING C2 PROJECT DEPENDENCIES")
    print("=" * 60)
    
    # Analyze imports
    print("📊 Scanning project files for imports...")
    categories = categorize_dependencies()
    
    # Display results
    total_deps = sum(len(cat) for cat in categories.values())
    print(f"📦 Found {total_deps} unique dependencies")
    print("")
    
    for category, deps in categories.items():
        if deps:
            print(f"📂 {category.replace('_', ' ').title()}: {len(deps)} packages")
            for dep in sorted(deps, key=lambda x: x['usage_count'], reverse=True)[:5]:
                status = "✅" if dep['available'] else "❌"
                print(f"   {status} {dep['pip_name']} (used {dep['usage_count']} times)")
            if len(deps) > 5:
                print(f"   ... and {len(deps) - 5} more")
            print("")
    
    # Generate requirements files
    print("📝 Generating requirements files...")
    
    # Full requirements
    full_requirements = generate_requirements_content(categories)
    with open('/home/ubuntu/C2/requirements-full.txt', 'w') as f:
        f.write(full_requirements)
    print("✅ Generated requirements-full.txt")
    
    # Minimal requirements
    minimal_requirements = create_minimal_requirements()
    with open('/home/ubuntu/C2/requirements-minimal.txt', 'w') as f:
        f.write(minimal_requirements)
    print("✅ Generated requirements-minimal.txt")
    
    # Update main requirements.txt
    with open('/home/ubuntu/C2/bane/requirements.txt', 'w') as f:
        f.write(minimal_requirements)
    print("✅ Updated bane/requirements.txt")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEPENDENCY ANALYSIS SUMMARY")
    print("=" * 60)
    
    available_count = sum(1 for cat in categories.values() for dep in cat if dep['available'])
    unavailable_count = total_deps - available_count
    
    print(f"📦 Total dependencies: {total_deps}")
    print(f"✅ Available: {available_count}")
    print(f"❌ Unavailable: {unavailable_count}")
    print("")
    print("📄 Files generated:")
    print("  - requirements-full.txt (complete dependency list)")
    print("  - requirements-minimal.txt (essential only)")
    print("  - bane/requirements.txt (updated)")
    print("")
    print("💡 Recommendations:")
    if unavailable_count > 0:
        print(f"  - {unavailable_count} packages are not available or optional")
        print("  - Use requirements-minimal.txt for basic installation")
        print("  - Install optional packages manually if needed")
    else:
        print("  - All dependencies are available!")
        print("  - Use requirements-full.txt for complete installation")

if __name__ == "__main__":
    main()
