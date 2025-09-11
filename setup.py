#!/usr/bin/env python3
"""
Setup script for C2 system.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "config",
        "logs",
        "certs",
        "core/protocol",
        "core/server", 
        "core/client",
        "core/utils",
        "features/monitoring/templates",
        "features/monitoring/static",
        "features/proxy",
        "features/management",
        "tests/unit",
        "tests/integration", 
        "tests/e2e",
        "scripts/deployment",
        "scripts/maintenance",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created {directory}")

def create_init_files():
    """Create __init__.py files."""
    print("🐍 Creating Python package files...")
    
    init_files = [
        "core/__init__.py",
        "core/protocol/__init__.py",
        "core/server/__init__.py",
        "core/client/__init__.py",
        "core/utils/__init__.py",
        "features/__init__.py",
        "features/monitoring/__init__.py",
        "features/proxy/__init__.py",
        "features/management/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/e2e/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('"""Package initialization."""\n')
            print(f"  ✅ Created {init_file}")

def create_config_files():
    """Create configuration files."""
    print("⚙️ Creating configuration files...")
    
    # Create config directory if it doesn't exist
    os.makedirs("config", exist_ok=True)
    
    # Copy config files if they exist
    if os.path.exists("config.json"):
        shutil.copy("config.json", "config/config.json")
        print("  ✅ Copied config.json to config/")
    
    if os.path.exists("config_template.json"):
        shutil.copy("config_template.json", "config/config_template.json")
        print("  ✅ Copied config_template.json to config/")

def create_requirements():
    """Create requirements.txt."""
    print("📦 Creating requirements.txt...")
    
    requirements = [
        "asyncio",
        "ssl",
        "json",
        "uuid",
        "time",
        "signal",
        "sys",
        "os",
        "typing",
        "unittest",
        "subprocess",
        "pathlib"
    ]
    
    with open("requirements.txt", "w") as f:
        for req in requirements:
            f.write(f"{req}\n")
    
    print("  ✅ Created requirements.txt")

def create_gitignore():
    """Create .gitignore file."""
    print("🚫 Creating .gitignore...")
    
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Certificates
certs/
*.crt
*.key
*.pem

# Config (keep templates)
config/*.json
!config/*_template.json

# OS
.DS_Store
Thumbs.db

# Test artifacts
.pytest_cache/
.coverage
htmlcov/

# Temporary files
*.tmp
*.temp
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("  ✅ Created .gitignore")

def create_readme():
    """Create README.md."""
    print("📖 Creating README.md...")
    
    readme_content = """# C2 System

A modular Command and Control system with proxy capabilities.

## Structure

```
C2/
├── core/                    # Core functionality
│   ├── protocol/           # Communication protocol
│   ├── server/             # C2 server implementation
│   ├── client/             # Bot agent implementation
│   └── utils/              # Utility functions
├── features/               # Additional features
│   ├── monitoring/         # Health checks and monitoring
│   ├── proxy/              # Proxy functionality
│   └── management/         # Management tools
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── docs/                   # Documentation
└── main_c2.py             # C2 server entry point
    main_bot.py            # Bot agent entry point
```

## Quick Start

1. **Setup**:
   ```bash
   python3 setup.py
   ```

2. **Start C2 Server**:
   ```bash
   python3 main_c2.py
   ```

3. **Start Bot Agent**:
   ```bash
   python3 main_bot.py --c2-host localhost --c2-port 4443 --token your_token
   ```

4. **Run Tests**:
   ```bash
   python3 run_tests.py --all
   ```

## Features

- ✅ Modular architecture
- ✅ Health check endpoints
- ✅ Connection limits
- ✅ Graceful shutdown
- ✅ Comprehensive testing
- ✅ Web dashboard
- ✅ Proxy support (HTTP/SOCKS5)

## Documentation

See `docs/` directory for detailed documentation.
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("  ✅ Created README.md")

def main():
    """Main setup function."""
    print("🚀 Setting up C2 System...")
    
    create_directories()
    create_init_files()
    create_config_files()
    create_requirements()
    create_gitignore()
    create_readme()
    
    print("\n✅ Setup completed!")
    print("\nNext steps:")
    print("1. Configure your settings in config/config.json")
    print("2. Start C2 server: python3 main_c2.py")
    print("3. Start bot agent: python3 main_bot.py")
    print("4. Run tests: python3 run_tests.py --all")

if __name__ == "__main__":
    main()
