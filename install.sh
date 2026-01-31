#!/bin/bash
# Voice Prompter - One-line install

set -e

echo "🎤 Installing Voice Prompter..."

# macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install portaudio pipx 2>/dev/null || true
    pipx ensurepath
fi

# Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get install -y portaudio19-dev pipx
    pipx ensurepath
fi

# Install CLI
pipx install git+https://github.com/danpalmieri/voice-prompter.git

echo ""
echo "✅ Installed!"
echo ""
echo "Usage: prompter script.txt"
echo ""
echo "You may need to restart your terminal or run: source ~/.zshrc"
