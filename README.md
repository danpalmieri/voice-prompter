# Voice Prompter 🎤

A voice-activated teleprompter that shows one phrase at a time and automatically advances when you stop speaking.

No more scrolling text or foot pedals. Just speak naturally and the next phrase appears.

## Install

```bash
# macOS (requires portaudio)
brew install portaudio
pip install voice-prompter

# Linux
sudo apt install portaudio19-dev
pip install voice-prompter
```

Or install from GitHub:

```bash
pip install git+https://github.com/danpalmieri/voice-prompter.git
```

## Usage

```bash
prompter script.txt
```

Options:

```bash
prompter script.txt              # Voice-activated (default)
prompter script.txt --manual     # Manual mode (keyboard only)
prompter script.txt --pause 1.5  # Adjust pause detection (seconds)
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

Perfect for recording videos, podcasts, or presentations.

## License

MIT
