#!/usr/bin/env python3
"""
Voice Prompter - Voice-activated teleprompter CLI.

Shows one phrase at a time, advances when it detects you speaking.
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


def split_phrases(text, max_length=100):
    """Split text into speakable phrases."""
    phrases = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for p in phrases:
        p = p.strip()
        if not p:
            continue
        if len(p) > max_length:
            subphrases = re.split(r',\s*', p)
            result.extend([sp.strip() for sp in subphrases if sp.strip()])
        else:
            result.append(p)
    return result


def display(phrase, current, total, status=""):
    """Display phrase BIG in terminal."""
    clear()
    try:
        w = os.get_terminal_size().columns
        h = os.get_terminal_size().lines
    except OSError:
        w, h = 80, 24

    # Header
    progress = f"[{current}/{total}]"
    print(f"\033[90m{progress:^{w}}\033[0m")
    print()

    # Word wrap
    available_height = h - 8
    words = phrase.split()
    max_width = min(w - 4, 60)
    
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

    # Vertical centering
    text_height = len(lines)
    padding_top = max(0, (available_height - text_height) // 2)
    print("\n" * padding_top)

    # Display BIG and BOLD
    for l in lines:
        print(f"\033[1m{l:^{w}}\033[0m")

    # Status and footer
    remaining_lines = h - padding_top - text_height - 6
    print("\n" * max(0, remaining_lines))
    
    if status:
        print(f"\033[93m{status:^{w}}\033[0m")
    else:
        print()
    print(f"\033[90m{'ESPAÇO=próx | B=volta | Q=sair':^{w}}\033[0m")


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


def voice_listener(cmd_queue, stop_event, recognizer, mic, min_words):
    """Listen for voice in a separate thread."""
    while not stop_event.is_set():
        try:
            with mic as source:
                try:
                    # Listen for speech
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=12)
                    
                    # Try to recognize
                    try:
                        spoken = recognizer.recognize_google(audio, language="pt-BR")
                        # Count words - filter out short sounds
                        word_count = len(spoken.split())
                        if word_count >= min_words:
                            cmd_queue.put(('voice', 'next'))
                    except sr.UnknownValueError:
                        # Couldn't understand - probably noise
                        pass
                    except sr.RequestError as e:
                        # API error - wait and retry
                        time.sleep(1)
                        
                except sr.WaitTimeoutError:
                    continue
                    
        except Exception as e:
            time.sleep(0.5)


def run_prompter(phrases, use_voice=True, min_words=3):
    """Run the prompter loop."""
    total = len(phrases)
    current = 0

    cmd_queue = queue.Queue()
    stop_event = threading.Event()

    # Start keyboard listener
    kb_thread = threading.Thread(target=keyboard_listener, args=(cmd_queue, stop_event), daemon=True)
    kb_thread.start()

    # Setup voice
    if use_voice:
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 300
        recognizer.pause_threshold = 0.8  # Faster response
        
        try:
            mic = sr.Microphone()
            print("🎤 Calibrando microfone...")
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.5)
            print(f"✅ Pronto! (sensibilidade: {int(recognizer.energy_threshold)})")
            time.sleep(0.5)
            
            voice_thread = threading.Thread(
                target=voice_listener,
                args=(cmd_queue, stop_event, recognizer, mic, min_words),
                daemon=True
            )
            voice_thread.start()
        except Exception as e:
            print(f"❌ Microfone não disponível: {e}")
            print("Usando modo manual.")
            use_voice = False
            time.sleep(1)

    try:
        while current < total:
            display(phrases[current], current + 1, total, "🎤 Ouvindo..." if use_voice else "")

            # Wait for command
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
                    elif source == 'voice' and cmd == 'next':
                        current += 1
                        break
                        
                except queue.Empty:
                    continue

    finally:
        stop_event.set()
        clear()
        print("Fim! 🎬")


def main():
    parser = argparse.ArgumentParser(
        description="Voice-activated teleprompter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  🎤 Speak     Advances after you speak (min 3 words)
  Space/Enter  Next phrase
  B            Previous phrase  
  Q            Quit
        """
    )
    parser.add_argument("script", help="Text file with your script")
    parser.add_argument("-m", "--manual", action="store_true", help="Manual mode (no voice)")
    parser.add_argument("-w", "--words", type=int, default=3, help="Min words to advance (default: 3)")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.3")

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"Error: File not found: {args.script}")
        sys.exit(1)

    with open(args.script, 'r', encoding='utf-8') as f:
        text = f.read()

    phrases = split_phrases(text)

    if not phrases:
        print("Error: No text found in file.")
        sys.exit(1)

    print(f"📜 {len(phrases)} frases")
    print("💡 Aumente a fonte: Cmd + (Mac)")
    print()

    run_prompter(phrases, use_voice=not args.manual, min_words=args.words)


if __name__ == "__main__":
    main()
