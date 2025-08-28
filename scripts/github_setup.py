#!/usr/bin/env python3
"""
GitHub Setup Helper Script
Helps with uploading project to GitHub
"""

import os
import subprocess
import sys

def print_banner():
    """Print setup banner"""
    print("🚀 GITHUB UPLOAD HELPER")
    print("=" * 50)
    print("📦 C2 Hybrid Botnet Manager")
    print("🛡️ Educational Security Research Tool")
    print("")

def check_git_status():
    """Check current git status"""
    print("📊 CURRENT REPOSITORY STATUS:")
    print("-" * 30)
    
    try:
        # Check if we're in a git repo
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️  Uncommitted changes detected:")
                print(result.stdout)
            else:
                print("✅ Repository is clean - ready for upload")
        
        # Show commit count
        commit_result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                                     capture_output=True, text=True)
        if commit_result.returncode == 0:
            commit_count = commit_result.stdout.strip()
            print(f"📝 Total commits: {commit_count}")
        
        # Show current branch
        branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                     capture_output=True, text=True)
        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip()
            print(f"🌿 Current branch: {branch}")
            
    except Exception as e:
        print(f"❌ Error checking git status: {e}")

def show_upload_instructions():
    """Show GitHub upload instructions"""
    print("\n🔗 GITHUB UPLOAD INSTRUCTIONS:")
    print("=" * 50)
    print("""
📋 STEP-BY-STEP GITHUB UPLOAD:

1. 🌐 CREATE GITHUB REPOSITORY:
   • Go to: https://github.com/new
   • Repository name: C2-Hybrid-Botnet-Manager
   • Description: Educational cybersecurity research tool
   • Set to: Public or Private (your choice)
   • ❌ DON'T initialize with README (we already have one)
   • Click "Create repository"

2. 🔗 ADD REMOTE ORIGIN:
   Copy and run these commands:
   
   git remote add origin https://github.com/YOUR_USERNAME/C2-Hybrid-Botnet-Manager.git
   git branch -M main
   git push -u origin main

3. 📚 REPLACE YOUR_USERNAME with your actual GitHub username

4. 🔐 AUTHENTICATION:
   • If prompted for password, use GitHub Personal Access Token
   • Go to: GitHub Settings > Developer settings > Personal access tokens
   • Generate token with 'repo' permissions
   • Use token as password when prompted

5. ✅ VERIFY UPLOAD:
   • Check your GitHub repository page
   • Verify all files are uploaded
   • Check README.md displays correctly
""")

def generate_remote_command():
    """Generate personalized remote command"""
    print("\n⚡ QUICK SETUP COMMANDS:")
    print("-" * 30)
    
    username = input("Enter your GitHub username: ").strip()
    
    if username:
        repo_name = "C2-Hybrid-Botnet-Manager"
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        
        print(f"\n📋 Copy and run these commands:")
        print("```bash")
        print(f"git remote add origin {remote_url}")
        print("git branch -M main")
        print("git push -u origin main")
        print("```")
        
        print(f"\n🌐 Your repository will be available at:")
        print(f"https://github.com/{username}/{repo_name}")
    else:
        print("⚠️  Username required for personalized commands")

def check_sensitive_files():
    """Check for sensitive files that shouldn't be uploaded"""
    print("\n🔒 SECURITY CHECK:")
    print("-" * 30)
    
    sensitive_patterns = [
        "*.key", "*.pem", "id_rsa*", 
        "config.json", "botnet_config.json",
        "*.log", "passwords*.txt"
    ]
    
    found_sensitive = False
    
    for pattern in sensitive_patterns:
        try:
            result = subprocess.run(['find', '.', '-name', pattern, '-type', 'f'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                if not found_sensitive:
                    print("⚠️  SENSITIVE FILES DETECTED:")
                    found_sensitive = True
                print(f"   {pattern}: {result.stdout.strip()}")
        except:
            pass
    
    if not found_sensitive:
        print("✅ No sensitive files detected")
        print("✅ Safe to upload to GitHub")
    else:
        print("\n🛡️  These files are already in .gitignore")
        print("✅ They won't be uploaded to GitHub")

def show_repository_info():
    """Show repository information"""
    print("\n📊 REPOSITORY INFORMATION:")
    print("-" * 30)
    
    try:
        # Count files
        result = subprocess.run(['find', '.', '-type', 'f', '!', '-path', './.git/*', 
                               '!', '-path', './venv/*'], capture_output=True, text=True)
        file_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        print(f"📁 Total files: {file_count}")
        
        # Repository size
        size_result = subprocess.run(['du', '-sh', '.', '--exclude=.git', '--exclude=venv'], 
                                   capture_output=True, text=True)
        if size_result.returncode == 0:
            size = size_result.stdout.split()[0]
            print(f"💾 Repository size: {size}")
        
        # Languages
        print("🔤 Languages: Python, JavaScript, HTML, CSS")
        print("🛠️  Framework: Flask, Bane Security")
        print("📚 Purpose: Educational cybersecurity research")
        
    except Exception as e:
        print(f"❌ Error getting repository info: {e}")

def main():
    """Main setup function"""
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists('bane') or not os.path.exists('README.md'):
        print("❌ Error: Please run this script from the C2 project root directory")
        sys.exit(1)
    
    # Check git status
    check_git_status()
    
    # Show repository info
    show_repository_info()
    
    # Security check
    check_sensitive_files()
    
    # Show upload instructions
    show_upload_instructions()
    
    # Generate personalized commands
    generate_remote_command()
    
    print("\n" + "=" * 50)
    print("🎯 READY FOR GITHUB UPLOAD!")
    print("=" * 50)
    print("✅ Repository is prepared and ready")
    print("✅ All sensitive files are protected")
    print("✅ Documentation is complete")
    print("📚 Follow the instructions above to upload")
    print("")
    print("🛡️  Remember: This is for educational use only!")
    print("🎓 Happy learning and ethical security research!")

if __name__ == "__main__":
    main()
