#!/usr/bin/env python3
"""
Verify environment dependencies are correctly installed
"""

import sys
from pathlib import Path

def check_import(module_name, package_name=None):
    """Check if module can be imported"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name}: {e}")
        return False

def main():
    print("="*60)
    print("Environment Dependency Check")
    print("="*60)
    print()
    
    # Core dependencies
    print("Core Framework:")
    checks = []
    checks.append(check_import("openai", "openai"))
    checks.append(check_import("langchain", "langchain"))
    checks.append(check_import("langchain_openai", "langchain-openai"))
    checks.append(check_import("langgraph", "langgraph"))
    
    print("\nConfiguration:")
    checks.append(check_import("dotenv", "python-dotenv"))
    
    print("\nChemistry:")
    checks.append(check_import("pymatgen", "pymatgen"))
    
    print("\nUtilities:")
    checks.append(check_import("requests", "requests"))
    checks.append(check_import("pydantic", "pydantic"))
    
    print("\nData Analysis:")
    checks.append(check_import("numpy", "numpy"))
    checks.append(check_import("pandas", "pandas"))
    checks.append(check_import("matplotlib", "matplotlib"))
    checks.append(check_import("seaborn", "seaborn"))
    
    print("\nTesting:")
    checks.append(check_import("pytest", "pytest"))
    
    print("\n" + "="*60)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All dependencies installed ({passed}/{total})")
        print("\nNext steps:")
        print("  1. Configure .env file")
        print("  2. cd evaluation")
        print("  3. python run_table2_evaluation.py")
        return 0
    else:
        print(f"⚠️  Some dependencies missing ({passed}/{total})")
        print("\nPlease run:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
