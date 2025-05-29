#!/usr/bin/env python3
"""
Setup script to create a configuration file from the template.
"""
import os
import shutil
import sys

def setup_config():
    """
    Copy the template config file to config.py if it doesn't exist
    """
    template_path = os.path.join('rsr', 'config.template.py')
    config_path = os.path.join('rsr', 'config.py')
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"Error: Template file {template_path} not found.")
        return False
    
    # Check if config already exists
    if os.path.exists(config_path):
        response = input(f"Config file {config_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    # Copy the template
    shutil.copy(template_path, config_path)
    print(f"Created {config_path} from template.")
    print("Please edit this file to add your API keys and settings.")
    
    return True

if __name__ == "__main__":
    if setup_config():
        print("\nSetup complete!")
        print("Next steps:")
        print("1. Edit rsr/config.py with your settings")
        print("2. Ensure MongoDB is running")
        print("3. Run python verify_installation.py to check your setup")
        print("4. Start the bot with python run.py")
    else:
        print("\nSetup failed.")
        sys.exit(1) 