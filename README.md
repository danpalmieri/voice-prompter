# Voice Prompter 🎤

A voice-activated teleprompter that shows one phrase at a time and automatically advances when you stop speaking.

No more scrolling text or foot pedals. Just speak naturally and the next phrase appears.

## Install

```bash
curl -sL https://raw.githubusercontent.com/danpalmieri/voice-prompter/master/install.sh | bash
```

Or manually:

```bash
# macOS
brew install portaudio
pip3 install SpeechRecognition pyaudio

# Linux
sudo apt install portaudio19-dev
pip3 install SpeechRecognition pyaudio

# Download
curl -o prompter.py https://raw.githubusercontent.com/danpalmieri/voice-prompter/master/prompter.py
```

## Usage

```bash
python3 prompter.py your_script.txt
```

**Tip:** Run terminal in fullscreen and increase font size (Cmd + on Mac).

## Controls

| Key | Action |
|-----|--------|
| 🎤 Speak | Auto-advance when you pause |
| Enter / Space | Next phrase (manual) |
| B | Previous phrase |
| Q | Quit |

## How it works

1. Splits your script into sentences
2. Displays one phrase at a time (large, centered)
3. Listens to your microphone
4. Detects when you stop speaking → shows next phrase

Perfect for recording videos, podcasts, or presentations without losing your place.

## License

MIT
