#!/usr/bin/env python3
"""
Voice Prompter - Voice-activated teleprompter CLI.

Shows one paragraph at a time, advances when it detects you speaking.
"""

import sys
import os
import re
import argparse
import threading
import queue
import time

import speech_recognition as sr


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def split_paragraphs(text):
    """Split text by blank lines (paragraphs)."""
    paragraphs = re.split(r'\n\s*\n', text)
    result = []
    for p in paragraphs:
        p = ' '.join(p.split())
        if p.strip():
            result.append(p.strip())
    return result


def display(phrase, current, total, voice_active=False):
    """Display phrase BIG at TOP of terminal."""
    clear()
    try:
        w = os.get_terminal_size().columns
        h = os.get_terminal_size().lines
    except OSError:
        w, h = 80, 24

    # BIG progress at top
    progress = f"[ {current} / {total} ]"
    print()
    print(f"\033[1;97m{progress:^{w}}\033[0m")
    print()
    print(f"\033[90m{'─' * w}\033[0m")
    print()

    # Word wrap
    words = phrase.split()
    max_width = min(w - 8, 50)
    
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= max_width:
            line += (" " if line else "") + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Display BIG and BOLD
    for l in lines:
        print(f"\033[1;97m{l:^{w}}\033[0m")
        print()

    # Footer
    footer_pos = h - 4
    current_pos = 5 + (len(lines) * 2)
    if footer_pos > current_pos:
        print("\n" * (footer_pos - current_pos))
    
    # Status line
    if voice_active:
        status = "🎤 Listening..."
    else:
        status = "🔇 Voice OFF"
    print(f"\033[93m{status:^{w}}\033[0m")
    print(f"\033[90m{'SPACE=next | B=back | V=voice | Q=quit':^{w}}\033[0m")


def keyboard_listener(cmd_queue, stop_event):
    """Listen for keyboard input in a separate thread."""
    import tty
    import termios
    import select
    
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while not stop_event.is_set():
            if select.select([sys.stdin], [], [], 0.05)[0]:
                key = sys.stdin.read(1).lower()
                cmd_queue.put(('key', key))
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def voice_listener(cmd_queue, stop_event, voice_enabled, recognizer, mic, min_words):
    """Listen for voice in a separate thread."""
    while not stop_event.is_set():
        # Check if voice is enabled
        if not voice_enabled.is_set():
            time.sleep(0.1)
            continue
            
        try:
            with mic as source:
                try:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=15)
                    
                    # Double-check voice is still enabled
                    if not voice_enabled.is_set():
                        continue
                    
                    try:
                        spoken = recognizer.recognize_google(audio, language="pt-BR")
                        word_count = len(spoken.split())
                        if word_count >= min_words:
                            cmd_queue.put(('voice', 'next'))
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        time.sleep(1)
                        
                except sr.WaitTimeoutError:
                    continue
                    
        except Exception:
            time.sleep(0.5)


def run_prompter(phrases, start_with_voice=True, min_words=5):
    """Run the prompter loop."""
    total = len(phrases)
    current = 0

    cmd_queue = queue.Queue()
    stop_event = threading.Event()
    voice_enabled = threading.Event()
    
    if start_with_voice:
        voice_enabled.set()

    # Start keyboard listener
    kb_thread = threading.Thread(target=keyboard_listener, args=(cmd_queue, stop_event), daemon=True)
    kb_thread.start()

    # Setup voice
    mic_available = False
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 1.0
    
    try:
        mic = sr.Microphone()
        print("🎤 Calibrating...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
        print("✅ Ready!")
        time.sleep(0.5)
        
        voice_thread = threading.Thread(
            target=voice_listener,
            args=(cmd_queue, stop_event, voice_enabled, recognizer, mic, min_words),
            daemon=True
        )
        voice_thread.start()
        mic_available = True
    except Exception as e:
        print(f"❌ Microphone: {e}")
        print("Manual mode only.")
        voice_enabled.clear()
        time.sleep(1)

    try:
        while current < total:
            display(phrases[current], current + 1, total, voice_enabled.is_set())

            while True:
                try:
                    source, cmd = cmd_queue.get(timeout=0.1)
                    
                    if source == 'key':
                        if cmd == 'q':
                            return
                        elif cmd == 'b' and current > 0:
                            current -= 1
                            break
                        elif cmd in '\n\r ':
                            current += 1
                            break
                        elif cmd == 'v' and mic_available:
                            # Toggle voice
                            if voice_enabled.is_set():
                                voice_enabled.clear()
                            else:
                                voice_enabled.set()
                            break  # Refresh display
                    elif source == 'voice' and cmd == 'next':
                        current += 1
                        break
                        
                except queue.Empty:
                    continue

    finally:
        stop_event.set()
        clear()
        print("Done! 🎬")


def main():
    parser = argparse.ArgumentParser(
        description="Voice-activated teleprompter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Splits text by blank lines (paragraphs).
Advances when you finish speaking each paragraph.

Controls:
  🎤 Speak     Advances after paragraph
  Space/Enter  Next (manual)
  B            Previous
  V            Toggle voice on/off
  Q            Quit
        """
    )
    parser.add_argument("script", help="Text file (separate paragraphs with blank lines)")
    parser.add_argument("-m", "--manual", action="store_true", help="Start in manual mode (voice off)")
    parser.add_argument("-w", "--words", type=int, default=5, help="Min words to advance (default: 5)")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.2.2")

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"Error: {args.script} not found")
        sys.exit(1)

    with open(args.script, 'r', encoding='utf-8') as f:
        text = f.read()

    phrases = split_paragraphs(text)

    if not phrases:
        print("Error: No text found")
        sys.exit(1)

    print(f"📜 {len(phrases)} paragraphs")
    print("💡 Cmd + to increase font")
    print()

    run_prompter(phrases, start_with_voice=not args.manual, min_words=args.words)


if __name__ == "__main__":
    main()
