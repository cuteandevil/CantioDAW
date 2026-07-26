#!/usr/bin/env bash
# CantioDAW Installer for macOS / Linux
# Usage: curl -fsSL https://github.com/cuteandevil/CantioDAW/releases/latest/download/install.sh | bash

set -euo pipefail

VERSION="v0.1.0"
REPO="cuteandevil/CantioDAW"
DEST="${HOME}/cantiodaw"

echo "=== CantioDAW Installer ==="
echo "Installing version ${VERSION} to ${DEST}"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)   PLATFORM="linux";;
    Darwin*)  PLATFORM="darwin";;
    *)        echo "Unsupported OS: ${OS}"; exit 1;;
esac

# Check existing
if [ -d "${DEST}" ]; then
    read -p "Directory ${DEST} already exists. Overwrite? (y/N) " choice
    case "${choice}" in
        y|Y) rm -rf "${DEST}";;
        *) echo "Installation cancelled."; exit 1;;
    esac
fi

TMPDIR=$(mktemp -d)
ZIP_URL="https://github.com/${REPO}/releases/download/${VERSION}/CantioDAW-${VERSION}-release.zip"

echo "Downloading from ${ZIP_URL} ..."
curl -fsSL -o "${TMPDIR}/release.zip" "${ZIP_URL}"

echo "Extracting..."
unzip -q "${TMPDIR}/release.zip" -d "${DEST}"

rm -rf "${TMPDIR}"

echo "=== Installation Complete ==="
echo "CantioDAW installed to: ${DEST}"
echo ""
echo "Quick start:"
echo "  cd ${DEST}"
echo "  ./cantiodaw-mcp --test"
echo ""
echo "Add to PATH? Add this to your ~/.bashrc or ~/.zshrc:"
echo "  export PATH=\"\${PATH}:${DEST}\""
