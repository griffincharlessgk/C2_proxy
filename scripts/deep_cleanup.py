#!/usr/bin/env python3
"""
Deep cleanup script để xóa tất cả file không cần thiết và cũ
"""

import os
import sys
import shutil
import glob
import time
from pathlib import Path

def print_banner():
    """Print banner"""
    print("🧹 DEEP CLEANUP UTILITY - C2 PROJECT")
    print("=" * 60)
    print("⚠️  Sẽ xóa các file không cần thiết để tối ưu dung lượng")
    print("")

def get_directory_size(path):
    """Get size of directory in MB"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total += os.path.getsize(filepath)
            except:
                pass
    return total / (1024 * 1024)  # Convert to MB

def cleanup_python_cache():
    """Xóa tất cả Python cache"""
    print("🐍 Cleaning Python cache...")
    
    project_root = Path("/home/ubuntu/C2")
    removed_count = 0
    
    # Remove __pycache__ directories
    for pycache_dir in project_root.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            removed_count += 1
            print(f"  ✅ Removed {pycache_dir}")
        except Exception as e:
            print(f"  ⚠️  Failed to remove {pycache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            removed_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed to remove {pyc_file}: {e}")
    
    # Remove .pyo files
    for pyo_file in project_root.rglob("*.pyo"):
        try:
            pyo_file.unlink()
            removed_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed to remove {pyo_file}: {e}")
    
    print(f"  📊 Removed {removed_count} Python cache items")
    return removed_count

def cleanup_build_artifacts():
    """Xóa build artifacts"""
    print("🔨 Cleaning build artifacts...")
    
    project_root = Path("/home/ubuntu/C2")
    removed_count = 0
    
    # Build directories to remove
    build_patterns = [
        "**/build",
        "**/dist", 
        "**/*.egg-info",
        "**/.eggs"
    ]
    
    for pattern in build_patterns:
        for path in project_root.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    removed_count += 1
                    print(f"  ✅ Removed {path}")
                else:
                    path.unlink()
                    removed_count += 1
                    print(f"  ✅ Removed {path}")
            except Exception as e:
                print(f"  ⚠️  Failed to remove {path}: {e}")
    
    print(f"  📊 Removed {removed_count} build artifacts")
    return removed_count

def cleanup_virtual_environment():
    """Xóa virtual environment (có thể tái tạo)"""
    print("📦 Cleaning virtual environment...")
    
    venv_path = Path("/home/ubuntu/C2/venv")
    
    if venv_path.exists():
        try:
            size_before = get_directory_size(venv_path)
            print(f"  📊 Virtual environment size: {size_before:.1f} MB")
            
            # Ask for confirmation (auto-yes for script)
            print("  ⚠️  Virtual environment sẽ được xóa (có thể tái tạo với pip)")
            
            shutil.rmtree(venv_path)
            print(f"  ✅ Removed virtual environment ({size_before:.1f} MB freed)")
            return size_before
        except Exception as e:
            print(f"  ❌ Failed to remove venv: {e}")
            return 0
    else:
        print("  ℹ️  No virtual environment found")
        return 0

def cleanup_temporary_files():
    """Xóa temporary files"""
    print("🗂️  Cleaning temporary files...")
    
    project_root = Path("/home/ubuntu/C2")
    removed_count = 0
    
    # Temporary file patterns
    temp_patterns = [
        "**/*.tmp",
        "**/*.temp",
        "**/.*~",
        "**/*.swp",
        "**/*.swo",
        "**/.DS_Store",
        "**/Thumbs.db",
        "**/*.bak",
        "**/*.backup",
        "**/*.old"
    ]
    
    for pattern in temp_patterns:
        for path in project_root.glob(pattern):
            try:
                if path.is_file():
                    path.unlink()
                    removed_count += 1
                    print(f"  ✅ Removed {path.name}")
            except Exception as e:
                print(f"  ⚠️  Failed to remove {path}: {e}")
    
    print(f"  📊 Removed {removed_count} temporary files")
    return removed_count

def cleanup_old_test_files():
    """Xóa old test files"""
    print("🧪 Cleaning old test files...")
    
    project_root = Path("/home/ubuntu/C2")
    removed_count = 0
    
    # Old test files to remove
    old_test_files = [
        "bane/test_infect_debug.py",
        "bane/test_suite.py",
        "test_malware",
        "test_malware_bane"
    ]
    
    for file_path in old_test_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                else:
                    full_path.unlink()
                removed_count += 1
                print(f"  ✅ Removed {file_path}")
            except Exception as e:
                print(f"  ⚠️  Failed to remove {file_path}: {e}")
    
    print(f"  📊 Removed {removed_count} old test files")
    return removed_count

def cleanup_duplicate_documentation():
    """Xóa duplicate documentation"""
    print("📚 Cleaning duplicate documentation...")
    
    project_root = Path("/home/ubuntu/C2")
    removed_count = 0
    
    # Keep main docs, remove duplicates
    docs_to_check = [
        "bane/README_HYBRID.md",  # Keep main README.md instead
        "bane/PROJECT_STATUS.md"  # May be outdated
    ]
    
    for doc_path in docs_to_check:
        full_path = project_root / doc_path
        if full_path.exists():
            try:
                full_path.unlink()
                removed_count += 1
                print(f"  ✅ Removed duplicate doc: {doc_path}")
            except Exception as e:
                print(f"  ⚠️  Failed to remove {doc_path}: {e}")
    
    print(f"  📊 Removed {removed_count} duplicate docs")
    return removed_count

def cleanup_empty_directories():
    """Xóa empty directories"""
    print("📁 Cleaning empty directories...")
    
    project_root = Path("/home/ubuntu/C2")
    removed_count = 0
    
    # Walk through directories from deepest to shallowest
    for dirpath, dirnames, filenames in os.walk(project_root, topdown=False):
        dir_path = Path(dirpath)
        
        # Skip important directories
        if any(name in str(dir_path) for name in ['.git', 'tests', 'scripts', 'bane/bane']):
            continue
        
        try:
            # Check if directory is empty
            if not any(dir_path.iterdir()):
                dir_path.rmdir()
                removed_count += 1
                print(f"  ✅ Removed empty dir: {dir_path.relative_to(project_root)}")
        except (OSError, PermissionError):
            # Directory not empty or permission denied
            pass
        except Exception as e:
            print(f"  ⚠️  Error checking {dir_path}: {e}")
    
    print(f"  📊 Removed {removed_count} empty directories")
    return removed_count

def optimize_file_permissions():
    """Optimize file permissions"""
    print("🔐 Optimizing file permissions...")
    
    project_root = Path("/home/ubuntu/C2")
    fixed_count = 0
    
    # Script files should be executable
    script_files = [
        "scripts/cleanup.py",
        "scripts/deep_cleanup.py",
        "scripts/fix_malware_server.py",
        "scripts/test_malware_server.py",
        "tests/run_all_tests.py",
        "bane/hybrid_botnet_manager.py",
        "bane/start_clean.py",
        "bane/vps_setup.sh",
        "bane/run_tests.sh"
    ]
    
    for script_file in script_files:
        script_path = project_root / script_file
        if script_path.exists():
            try:
                script_path.chmod(0o755)
                fixed_count += 1
            except Exception as e:
                print(f"  ⚠️  Failed to fix permissions for {script_file}: {e}")
    
    # Config files should be secure
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
                print(f"  ⚠️  Failed to secure {config_file}: {e}")
    
    print(f"  📊 Fixed permissions for {fixed_count} files")
    return fixed_count

def generate_summary():
    """Generate final summary"""
    print("\n" + "=" * 60)
    print("📊 CLEANUP SUMMARY")
    print("=" * 60)
    
    # Get final size
    final_size = get_directory_size("/home/ubuntu/C2")
    
    # Count files
    file_count = sum(1 for _ in Path("/home/ubuntu/C2").rglob("*") if _.is_file())
    
    print(f"📁 Total files: {file_count}")
    print(f"💾 Total size: {final_size:.1f} MB")
    
    # List remaining main components
    print(f"\n📦 Main components:")
    main_dirs = [
        "bane/bane",
        "tests", 
        "scripts",
        "bane/malware",
        "bane/templates"
    ]
    
    for main_dir in main_dirs:
        dir_path = Path("/home/ubuntu/C2") / main_dir
        if dir_path.exists():
            dir_size = get_directory_size(dir_path)
            file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
            print(f"  📂 {main_dir}: {file_count} files, {dir_size:.1f} MB")

def main():
    """Main cleanup function"""
    print_banner()
    
    # Get initial size
    initial_size = get_directory_size("/home/ubuntu/C2")
    print(f"📊 Initial project size: {initial_size:.1f} MB")
    print("")
    
    try:
        # Run cleanup operations
        cleanup_python_cache()
        print("")
        
        cleanup_build_artifacts()
        print("")
        
        venv_freed = cleanup_virtual_environment()
        print("")
        
        cleanup_temporary_files()
        print("")
        
        cleanup_old_test_files()
        print("")
        
        cleanup_duplicate_documentation()
        print("")
        
        cleanup_empty_directories()
        print("")
        
        optimize_file_permissions()
        
        # Generate summary
        generate_summary()
        
        # Calculate space saved
        final_size = get_directory_size("/home/ubuntu/C2")
        space_saved = initial_size - final_size
        
        print(f"\n🎉 CLEANUP COMPLETED!")
        print(f"💾 Space saved: {space_saved:.1f} MB")
        print(f"📉 Size reduction: {(space_saved/initial_size)*100:.1f}%")
        print(f"🚀 Project is now optimized and clean!")
        
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
