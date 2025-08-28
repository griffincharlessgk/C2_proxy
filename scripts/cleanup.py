#!/usr/bin/env python3
"""
Cleanup script cho C2 Hybrid Botnet Management System
Xóa các file tạm, cache, và optimize system
"""

import os
import sys
import shutil
import glob
import tempfile
from pathlib import Path

def print_banner():
    """Print cleanup banner"""
    print("🧹 C2 SYSTEM CLEANUP UTILITY")
    print("=" * 50)

def cleanup_python_cache():
    """Xóa Python cache files"""
    print("🐍 Cleaning Python cache files...")
    
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo", 
        "**/*.pyd",
        "**/.pytest_cache"
    ]
    
    removed_count = 0
    project_root = Path(__file__).parent.parent
    
    for pattern in patterns:
        for path in project_root.glob(pattern):
            try:
                if path.is_file():
                    path.unlink()
                    removed_count += 1
                elif path.is_dir():
                    shutil.rmtree(path)
                    removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not remove {path}: {e}")
    
    print(f"  ✅ Removed {removed_count} Python cache items")

def cleanup_logs():
    """Cleanup old log files"""
    print("📋 Cleaning old log files...")
    
    log_dirs = [
        "logs",
        "bane/logs",
    ]
    
    removed_count = 0
    project_root = Path(__file__).parent.parent
    
    for log_dir in log_dirs:
        log_path = project_root / log_dir
        if log_path.exists():
            for log_file in log_path.glob("*.log.*"):  # Rotated logs
                try:
                    log_file.unlink()
                    removed_count += 1
                except Exception as e:
                    print(f"  ⚠️  Could not remove {log_file}: {e}")
    
    print(f"  ✅ Removed {removed_count} old log files")

def cleanup_temp_files():
    """Xóa temporary files"""
    print("🗂️  Cleaning temporary files...")
    
    patterns = [
        "**/*.tmp",
        "**/*.temp",
        "**/.*~",
        "**/*.swp",
        "**/*.swo",
        "**/.DS_Store",
        "**/Thumbs.db"
    ]
    
    removed_count = 0
    project_root = Path(__file__).parent.parent
    
    for pattern in patterns:
        for path in project_root.glob(pattern):
            try:
                if path.is_file():
                    path.unlink()
                    removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not remove {path}: {e}")
    
    print(f"  ✅ Removed {removed_count} temporary files")

def cleanup_build_artifacts():
    """Xóa build artifacts"""
    print("🔨 Cleaning build artifacts...")
    
    patterns = [
        "**/build",
        "**/dist", 
        "**/*.egg-info",
        "**/.eggs"
    ]
    
    removed_count = 0
    project_root = Path(__file__).parent.parent
    
    for pattern in patterns:
        for path in project_root.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not remove {path}: {e}")
    
    print(f"  ✅ Removed {removed_count} build artifacts")

def optimize_imports():
    """Optimize import statements in Python files"""
    print("⚡ Optimizing import statements...")
    
    project_root = Path(__file__).parent.parent
    optimized_count = 0
    
    for py_file in project_root.glob("**/*.py"):
        if "venv" in str(py_file) or "env" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple optimization: remove duplicate empty lines
            lines = content.split('\n')
            optimized_lines = []
            prev_empty = False
            
            for line in lines:
                if line.strip() == '':
                    if not prev_empty:
                        optimized_lines.append(line)
                    prev_empty = True
                else:
                    optimized_lines.append(line)
                    prev_empty = False
            
            optimized_content = '\n'.join(optimized_lines)
            
            if optimized_content != content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(optimized_content)
                optimized_count += 1
                
        except Exception as e:
            print(f"  ⚠️  Could not optimize {py_file}: {e}")
    
    print(f"  ✅ Optimized {optimized_count} Python files")

def check_permissions():
    """Check and fix file permissions"""
    print("🔐 Checking file permissions...")
    
    project_root = Path(__file__).parent.parent
    fixed_count = 0
    
    # Fix script permissions
    script_files = [
        "scripts/cleanup.py",
        "tests/run_all_tests.py", 
        "bane/hybrid_botnet_manager.py",
        "bane/start_clean.py"
    ]
    
    for script_file in script_files:
        script_path = project_root / script_file
        if script_path.exists():
            try:
                script_path.chmod(0o755)
                fixed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not fix permissions for {script_path}: {e}")
    
    # Secure config files
    config_files = [
        "bane/botnet_config.json",
        "bane/config_template.json"
    ]
    
    for config_file in config_files:
        config_path = project_root / config_file
        if config_path.exists():
            try:
                config_path.chmod(0o600)
                fixed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not fix permissions for {config_path}: {e}")
    
    print(f"  ✅ Fixed permissions for {fixed_count} files")

def display_disk_usage():
    """Display disk usage information"""
    print("💾 Disk usage information:")
    
    project_root = Path(__file__).parent.parent
    
    total_size = 0
    file_count = 0
    
    for path in project_root.rglob("*"):
        if path.is_file():
            try:
                size = path.stat().st_size
                total_size += size
                file_count += 1
            except Exception:
                pass
    
    print(f"  📁 Total files: {file_count}")
    print(f"  📊 Total size: {total_size / (1024*1024):.2f} MB")

def main():
    """Main cleanup function"""
    print_banner()
    
    try:
        cleanup_python_cache()
        cleanup_logs()
        cleanup_temp_files()
        cleanup_build_artifacts()
        optimize_imports()
        check_permissions()
        display_disk_usage()
        
        print("\n" + "=" * 50)
        print("✅ CLEANUP COMPLETED SUCCESSFULLY!")
        print("🚀 System is now optimized and ready for use.")
        
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
