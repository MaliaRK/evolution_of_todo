#!/usr/bin/env python3
"""
Deployment Verification Script for Todo AI System

This script verifies that all components are properly set up for cloud deployment.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_backend_structure():
    """Check if backend structure is correct for deployment"""
    print("[INFO] Checking backend structure...")
    
    backend_path = Path("backend")
    required_files = [
        "requirements.txt",
        "src/main.py",
        "src/models/__init__.py",
        "src/services/__init__.py",
        "src/api/__init__.py",
        "src/config/__init__.py",
        "src/handlers/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (backend_path / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"[ERROR] Missing backend files: {missing_files}")
        return False
    else:
        print("[SUCCESS] Backend structure is correct")
        return True

def check_frontend_structure():
    """Check if frontend structure is correct for deployment"""
    print("[INFO] Checking frontend structure...")
    
    frontend_path = Path("frontend")
    required_files = [
        "package.json",
        "package-lock.json",
        "src/",
        "Dockerfile"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (frontend_path / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"[ERROR] Missing frontend files: {missing_files}")
        return False
    else:
        print("[SUCCESS] Frontend structure is correct")
        return True

def check_docker_files():
    """Check if Docker files are properly created"""
    print("[INFO] Checking Docker files...")
    
    required_docker_files = [
        "backend/Dockerfile",
        "frontend/Dockerfile",
        "docker-compose.prod.yml"
    ]
    
    missing_files = []
    for file_path in required_docker_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"[ERROR] Missing Docker files: {missing_files}")
        return False
    else:
        print("[SUCCESS] Docker files are present")
        return True

def check_deployment_docs():
    """Check if deployment documentation is available"""
    print("[INFO] Checking deployment documentation...")
    
    required_docs = [
        "DEPLOYMENT_GUIDE.md",
        "RAILWAY_DEPLOYMENT.md",
        "Procfile"
    ]
    
    missing_docs = []
    for doc_path in required_docs:
        if not Path(doc_path).exists():
            missing_docs.append(doc_path)
    
    if missing_docs:
        print(f"[ERROR] Missing deployment documentation: {missing_docs}")
        return False
    else:
        print("[SUCCESS] Deployment documentation is available")
        return True

def check_environment_setup():
    """Check if environment setup is documented"""
    print("[INFO] Checking environment setup...")
    
    # Check if environment variables are documented in README
    readme_path = Path("README.md")
    if readme_path.exists():
        readme_content = readme_path.read_text()
        if "DATABASE_URL" in readme_content and "API_BASE_URL" in readme_content:
            print("[SUCCESS] Environment variables are documented")
            return True
        else:
            print("[WARN] Environment variables may not be fully documented")
            return True  # Not critical for deployment
    else:
        print("[WARN] README.md not found")
        return True

def check_cloud_readiness():
    """Overall cloud readiness check"""
    print("\nPerforming cloud deployment readiness check...\n")
    
    checks = [
        ("Backend Structure", check_backend_structure),
        ("Frontend Structure", check_frontend_structure),
        ("Docker Files", check_docker_files),
        ("Deployment Docs", check_deployment_docs),
        ("Environment Setup", check_environment_setup),
    ]
    
    results = []
    for check_name, check_func in checks:
        result = check_func()
        results.append((check_name, result))
        print()  # Empty line for readability
    
    print("="*50)
    print("Cloud Deployment Readiness Report:")
    print("="*50)
    
    all_passed = True
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {check_name}")
        if not result:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("SUCCESS: All checks passed! The application is ready for cloud deployment.")
        print("\nNext steps:")
        print("   1. Set up your cloud platform account (Railway, Heroku, Render, etc.)")
        print("   2. Prepare your environment variables")
        print("   3. Deploy the backend service first")
        print("   4. Deploy the frontend service with reference to backend URL")
        print("   5. Test the health endpoints after deployment")
        print("\nRefer to DEPLOYMENT_GUIDE.md for detailed instructions.")
    else:
        print("FAILURE: Some checks failed. Please address the issues before deployment.")
    
    return all_passed

if __name__ == "__main__":
    # Change to the project root directory
    os.chdir(Path(__file__).parent)
    
    print("Cloud Deployment Verification for Todo AI System")
    print("================================================\n")
    
    is_ready = check_cloud_readiness()
    
    sys.exit(0 if is_ready else 1)