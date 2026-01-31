#!/bin/bash
# Voice Prompter - One-line install

set -e

echo "🎤 Installing Voice Prompter..."

# macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew list portaudio &>/dev/null; then
        echo "Installing portaudio..."
        brew install portaudio
    fi
fi

# Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! dpkg -l | grep -q portaudio19-dev 2>/dev/null; then
        echo "Installing portaudio..."
        sudo apt-get install -y portaudio19-dev
    fi
fi

# Install CLI
pip3 install -q git+https://github.com/danpalmieri/voice-prompter.git

echo ""
echo "✅ Installed!"
echo ""
echo "Usage: prompter script.txt"
