#!/usr/bin/env python
"""
Dependency installer for Career Up

This script installs all required dependencies for the Career Up application.
"""

import subprocess
import sys
import platform

def install_dependencies():
    """Install required dependencies from requirements.txt"""
    print("=== Career Up Dependency Installer ===")
    print("Installing required packages...")
    
    try:
        # Upgrade pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install dependencies from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("\n=== All dependencies installed successfully! ===")
        print("You can now run the application with: python run.py")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError installing dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

def create_required_directories():
    """Create required directories if they don't exist"""
    import os
    
    # Create uploads directory
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("Created uploads directory")
    
    # Create output directory
    if not os.path.exists("output"):
        os.makedirs("output")
        print("Created output directory")

def check_google_genai():
    """Check if Google Generative AI is available"""
    try:
        import google.generativeai
        print("✅ Google Generative AI package is available")
    except ImportError:
        print("❌ Google Generative AI package is not available")
        print("   This is required for AI features.")
        print("   The installation should have added this package.")
        print("   If issues persist, try manual installation:")
        print("   pip install google-generativeai==0.3.1 protobuf==3.20.3")

if __name__ == "__main__":
    # Print Python version
    print(f"Python version: {platform.python_version()}")
    
    # Install dependencies
    install_dependencies()
    
    # Create required directories
    create_required_directories()
    
    # Check Google Generative AI
    check_google_genai()
    
    print("\nSetup complete! Follow the next steps in the README.md file.") 