#!/bin/bash
# Voice Prompter - Instalação automática para macOS

set -e

echo "🎤 Instalando Voice Prompter..."

# Instalar portaudio se não existir
if ! brew list portaudio &>/dev/null; then
    echo "Instalando portaudio..."
    brew install portaudio
fi

# Instalar dependências Python
pip3 install -q SpeechRecognition pyaudio

# Baixar o script
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
curl -sL -o "$INSTALL_DIR/prompter.py" "https://raw.githubusercontent.com/danpalmieri/clawdbot/master/tools/voice-prompter/prompter.py"
chmod +x "$INSTALL_DIR/prompter.py"

# Criar alias
cat >> ~/.zshrc << 'EOF'
alias prompter='python3 ~/.local/bin/prompter.py'
EOF

echo ""
echo "✅ Instalado!"
echo ""
echo "Uso:"
echo "  source ~/.zshrc"
echo "  prompter seu_script.txt"
echo ""
echo "Ou direto:"
echo "  python3 ~/.local/bin/prompter.py seu_script.txt"
