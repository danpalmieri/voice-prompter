#!/bin/bash
# Voice Prompter - Auto-install for macOS/Linux

set -e

echo "🎤 Installing Voice Prompter..."

# macOS: install portaudio
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew list portaudio &>/dev/null; then
        echo "Installing portaudio..."
        brew install portaudio
    fi
fi

# Linux: install portaudio
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! dpkg -l | grep -q portaudio19-dev; then
        echo "Installing portaudio..."
        sudo apt-get install -y portaudio19-dev
    fi
fi

# Install Python dependencies
pip3 install -q SpeechRecognition pyaudio

# Download script
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
curl -sL -o "$INSTALL_DIR/prompter.py" "https://raw.githubusercontent.com/danpalmieri/voice-prompter/master/prompter.py"
chmod +x "$INSTALL_DIR/prompter.py"

echo ""
echo "✅ Installed!"
echo ""
echo "Usage:"
echo "  python3 ~/.local/bin/prompter.py your_script.txt"
