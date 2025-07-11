#!/bin/bash

BASHRC="$HOME/.bashrc"

if [ -f /mnt/c/Python313/python.exe ]; then
    grep -qxF "export KEYRING_PROPERTY_PYTHON=/mnt/c/Python313/python.exe" "$BASHRC" || echo "export KEYRING_PROPERTY_PYTHON=/mnt/c/Python313/python.exe" >> "$BASHRC"
    grep -qxF "export PYTHON_KEYRING_BACKEND=keyring_pybridge.PyBridgeKeyring" "$BASHRC" || echo "export PYTHON_KEYRING_BACKEND=keyring_pybridge.PyBridgeKeyring" >> "$BASHRC"
fi
