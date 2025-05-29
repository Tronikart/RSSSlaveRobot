#!/usr/bin/env python3
"""
Script to update import paths after moving to the repo folder
This should be run from inside the repo folder
"""
import os
import re
import sys
from pathlib import Path

def scan_python_files():
    """Find all Python files in the current directory and subdirectories"""
    python_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                python_files.append(path)
    return python_files

def update_imports_in_file(file_path):
    """Update import statements in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if there are any imports that need updating
    original_content = content
    
    # Replace import statements
    # We're looking for patterns like:
    # from rsr.utils.xxx import yyy
    # import rsr.utils.xxx
    import_pattern = re.compile(r'(from|import)\s+(rsr\.[\w\.]+)')
    
    # Find all matches
    matches = import_pattern.findall(content)
    if not matches:
        return False, 0
    
    # Replace all matches
    for match in matches:
        import_type, module_path = match
        content = content.replace(f"{import_type} {module_path}", f"{import_type} {module_path}")
    
    # If no changes were made, return
    if content == original_content:
        return False, 0
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True, len(matches)

def main():
    """Main function"""
    # Check if we're in the repo folder
    if not os.path.exists('rsr'):
        print("Error: 'rsr' directory not found. Make sure you're running this from the repo folder.")
        print("Current directory:", os.getcwd())
        return False
    
    print("Scanning for Python files...")
    python_files = scan_python_files()
    print(f"Found {len(python_files)} Python files")
    
    updated_files = 0
    total_changes = 0
    
    print("\nUpdating import statements...")
    for file_path in python_files:
        updated, changes = update_imports_in_file(file_path)
        if updated:
            updated_files += 1
            total_changes += changes
            print(f"Updated {file_path} ({changes} changes)")
    
    print(f"\nCompleted! Updated {updated_files} files with {total_changes} import changes")
    return True

if __name__ == "__main__":
    print("This script will update import statements in Python files after moving to the repo folder")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    success = main()
    if not success:
        sys.exit(1) 