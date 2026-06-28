#!/usr/bin/env bash
# Last updated: 2026-06-28 — v3.0.0
set -euo pipefail

# Uninstaller for HX32 Download Manager
# Removes installed files created by the Debian package.

INSTALL_PATH="/usr/local/bin/hx32-download-manager"
DESKTOP_PATH="/usr/share/applications/hx32-download-manager.desktop"
DATA_DIR="/usr/share/hx32-download-manager"

if [ -f "$INSTALL_PATH" ]; then
    echo "Removing $INSTALL_PATH"
    sudo rm -f "$INSTALL_PATH"
else
    echo "$INSTALL_PATH not found"
fi

if [ -f "$DESKTOP_PATH" ]; then
    echo "Removing $DESKTOP_PATH"
    sudo rm -f "$DESKTOP_PATH"
else
    echo "$DESKTOP_PATH not found"
fi

if [ -d "$DATA_DIR" ]; then
    echo "Removing $DATA_DIR"
    sudo rm -rf "$DATA_DIR"
else
    echo "$DATA_DIR not found"
fi

echo "HX32 Download Manager uninstall complete."
