# PowerShell script to remove sensitive configuration files from Git history

Write-Host "This script will rewrite Git history to remove config.py from all commits."
Write-Host "WARNING: This will change commit hashes. Anyone who has cloned your repository will need to re-clone after this."
Write-Host "Make sure you have a backup of your repository before proceeding."
Write-Host ""
$confirm = Read-Host "Are you sure you want to proceed? (y/N)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Operation cancelled."
    exit 0
}

# Create a backup of config.py
Write-Host "Creating backup of config.py..."
Copy-Item -Path "rsr\config.py" -Destination "config.py.backup"

# Ensure we have the template file
if (-not (Test-Path "rsr\config.template.py")) {
    Write-Host "Error: config.template.py not found. Please create it first."
    exit 1
}

# Filter branch to remove config.py from history
Write-Host "Removing config.py from Git history..."
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch rsr/config.py" --prune-empty --tag-name-filter cat -- --all

# Add config.py to .gitignore if not already there
$gitignore = Get-Content -Path ".gitignore" -Raw
if (-not ($gitignore -match "rsr/config.py")) {
    Write-Host "Adding rsr/config.py to .gitignore..."
    Add-Content -Path ".gitignore" -Value "`nrsr/config.py"
}

# Restore the config file from backup (but it won't be tracked)
Write-Host "Restoring config.py from backup..."
Move-Item -Path "config.py.backup" -Destination "rsr\config.py" -Force

Write-Host ""
Write-Host "History cleaning complete!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Force-push the changes to your remote repository:"
Write-Host "   git push origin --force --all"
Write-Host ""
Write-Host "2. Make sure all collaborators re-clone the repository."
Write-Host ""
Write-Host "3. If you're publishing this repository, verify that rsr/config.py"
Write-Host "   is not included in any commits by running:"
Write-Host "   git log --all --full-history -- rsr/config.py"
Write-Host ""
Write-Host "Note: rsr/config.py is now ignored by Git, but your local copy is preserved."
Write-Host "New users will need to run setup_config.py to create their own config.py file." 