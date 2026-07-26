#!/usr/bin/env pwsh
# CantioDAW Installer for Windows
# Usage: irm https://github.com/cuteandevil/CantioDAW/releases/latest/download/install.ps1 | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Version = "v0.1.0"
$Repo = "cuteandevil/CantioDAW"
$Dest = Join-Path $HOME "cantiodaw"

Write-Host "=== CantioDAW Installer ===" -ForegroundColor Cyan
Write-Host "Installing version $Version to $Dest"

# Check existing installation
if (Test-Path $Dest) {
    $choice = Read-Host "Directory $Dest already exists. Overwrite? (y/N)"
    if ($choice -ne "y" -and $choice -ne "Y") {
        Write-Host "Installation cancelled."
        exit 1
    }
    Remove-Item -Recurse -Force $Dest
}

# Create temp directory
$TmpDir = Join-Path $env:TMP "cantiodaw-install"
New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

# Download release
$ZipUrl = "https://github.com/$Repo/releases/download/$Version/CantioDAW-$Version-release.zip"
$ZipPath = Join-Path $TmpDir "release.zip"
Write-Host "Downloading from $ZipUrl ..."
curl.exe -sL -o $ZipPath $ZipUrl

# Extract
Write-Host "Extracting..."
Expand-Archive -Path $ZipPath -DestinationPath $Dest -Force

# Cleanup
Remove-Item -Recurse -Force $TmpDir

Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host "CantioDAW installed to: $Dest"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  cd $Dest"
Write-Host "  .\cantiodaw-mcp.exe --test"
Write-Host ""
Write-Host "Add to PATH? Add this to your PowerShell profile:"
Write-Host "  `$env:Path += `";$Dest`""
