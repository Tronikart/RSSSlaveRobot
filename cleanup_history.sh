#!/bin/bash
# Script to remove sensitive configuration files from Git history

echo "This script will rewrite Git history to remove config.py from all commits."
echo "WARNING: This will change commit hashes. Anyone who has cloned your repository will need to re-clone after this."
echo "Make sure you have a backup of your repository before proceeding."
echo ""
read -p "Are you sure you want to proceed? (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Create a backup of config.py
echo "Creating backup of config.py..."
cp rsr/config.py config.py.backup

# Ensure we have the template file
if [ ! -f rsr/config.template.py ]; then
    echo "Error: config.template.py not found. Please create it first."
    exit 1
fi

# Filter branch to remove config.py from history
echo "Removing config.py from Git history..."
git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch rsr/config.py" \
    --prune-empty --tag-name-filter cat -- --all

# Add config.py to .gitignore if not already there
if ! grep -q "rsr/config.py" .gitignore; then
    echo "Adding rsr/config.py to .gitignore..."
    echo "rsr/config.py" >> .gitignore
fi

# Restore the config file from backup (but it won't be tracked)
echo "Restoring config.py from backup..."
mv config.py.backup rsr/config.py

echo ""
echo "History cleaning complete!"
echo ""
echo "Next steps:"
echo "1. Force-push the changes to your remote repository:"
echo "   git push origin --force --all"
echo ""
echo "2. Make sure all collaborators re-clone the repository."
echo ""
echo "3. If you're publishing this repository, verify that rsr/config.py"
echo "   is not included in any commits by running:"
echo "   git log --all --full-history -- rsr/config.py"
echo ""
echo "Note: rsr/config.py is now ignored by Git, but your local copy is preserved."
echo "New users will need to run setup_config.py to create their own config.py file." 