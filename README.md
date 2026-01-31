# Voice Prompter 🎤

Teleprompter ativado por voz - mostra uma frase de cada vez e avança automaticamente quando você para de falar.

## Instalação

```bash
# macOS
brew install portaudio
pip install SpeechRecognition pyaudio

# Linux
sudo apt install portaudio19-dev
pip install SpeechRecognition pyaudio
```

## Uso

```bash
python prompter.py script.txt
```

## Controles

- **Falar** → avança quando você para
- **Enter/Espaço** → próxima frase (manual)
- **B** → volta uma frase
- **Q** → sair

## Dica

Coloque o terminal em fullscreen e aumente a fonte (Cmd+Plus no Mac).
