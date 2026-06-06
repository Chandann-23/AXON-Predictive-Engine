# AXON Predictive Engine - Hugging Face Space Deploy Script
# This script deploys the backend folder directly to your Hugging Face Space with correct Git LFS configurations.

$ErrorActionPreference = "Stop"

$SPACE_URL = "https://huggingface.co/spaces/Chandann-23/Axon-predictive-engine"
$TEMP_DIR = Join-Path $PSScriptRoot ".hf_sync_temp"

Write-Host "Starting deployment to Hugging Face Space..." -ForegroundColor Cyan

# Cleanup old temp dir if it exists
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}

# Create temp dir
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

try {
    # Initialize repository
    Write-Host "Initializing temporary repository..." -ForegroundColor Yellow
    Set-Location $TEMP_DIR
    
    # Run git init and setup LFS
    git init
    git lfs install
    git checkout -b main
    
    # Configure Git LFS tracking
    git lfs track "models/*.pkl"
    
    # Copy backend folder contents and root .gitignore
    Write-Host "Copying backend assets..." -ForegroundColor Yellow
    Copy-Item -Path "$PSScriptRoot\backend\*" -Destination $TEMP_DIR -Recurse -Force
    Copy-Item -Path "$PSScriptRoot\.gitignore" -Destination $TEMP_DIR -Force
    
    # Commit files
    Write-Host "Staging and committing files..." -ForegroundColor Yellow
    git add -A
    git commit -m "deploy: update backend assets ($(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))"
    
    # Push to Hugging Face Space
    Write-Host "Pushing to Hugging Face Space (credentials prompt may appear)..." -ForegroundColor Yellow
    git push --force $SPACE_URL main
    
    Write-Host "Successfully deployed to Hugging Face Space! 🎉" -ForegroundColor Green
}
finally {
    # Return to original path and cleanup
    Set-Location $PSScriptRoot
    if (Test-Path $TEMP_DIR) {
        # Force garbage collection to release file locks before deleting
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
        Remove-Item -Recurse -Force $TEMP_DIR
    }
}
