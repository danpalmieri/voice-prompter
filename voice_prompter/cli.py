#!/usr/bin/env python3
"""
Voice Prompter - Voice-activated teleprompter CLI.

Shows one phrase at a time, advances when you stop speaking.
"""

import sys
import os
import re
import argparse
import select
import tty
import termios

import speech_recognition as sr


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def split_phrases(text, max_length=150):
    """Split text into speakable phrases."""
    # Split on sentence endings
    phrases = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for p in phrases:
        p = p.strip()
        if not p:
            continue
        # Split long phrases on commas
        if len(p) > max_length:
            subphrases = re.split(r',\s*', p)
            result.extend([sp.strip() for sp in subphrases if sp.strip()])
        else:
            result.append(p)
    return result


def display(phrase, current, total):
    """Display phrase prominently in terminal."""
    clear()
    try:
        w = os.get_terminal_size().columns
        h = os.get_terminal_size().lines
    except OSError:
        w, h = 80, 24

    # Header
    print(f"\n{'─' * w}")
    print(f"{f'[{current}/{total}]':^{w}}")
    print(f"{'─' * w}")

    # Vertical centering
    print("\n" * max(0, (h - 12) // 2))

    # Word wrap
    words = phrase.split()
    lines = []
    line = ""
    max_width = min(w - 4, 80)

    for word in words:
        if len(line) + len(word) + 1 <= max_width:
            line += (" " if line else "") + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Display centered
    for l in lines:
        print(f"{l:^{w}}")

    print("\n\n")
    print(f"{'🎤 Speak... (Enter=next, B=back, Q=quit)':^{w}}")


def run_prompter(phrases, use_voice=True, pause_threshold=1.2):
    """Run the prompter loop."""
    total = len(phrases)
    current = 0

    if use_voice:
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = pause_threshold
        recognizer.dynamic_energy_threshold = True
        try:
            mic = sr.Microphone()
            print("Calibrating microphone...")
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Microphone not available: {e}")
            print("Falling back to manual mode.")
            use_voice = False
            mic = None
            import time
            time.sleep(1)
    else:
        mic = None
        recognizer = None

    # Set terminal to non-blocking
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while current < total:
            display(phrases[current], current + 1, total)

            if use_voice and mic:
                with mic as source:
                    try:
                        # Check keyboard
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1).lower()
                            if key == 'q':
                                break
                            elif key == 'b' and current > 0:
                                current -= 1
                                continue
                            elif key in '\n\r ':
                                current += 1
                                continue

                        # Listen for speech
                        audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=15)
                        current += 1
                    except sr.WaitTimeoutError:
                        continue
            else:
                # Manual mode
                key = sys.stdin.read(1).lower()
                if key == 'q':
                    break
                elif key == 'b' and current > 0:
                    current -= 1
                elif key in '\n\r ':
                    current += 1

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        clear()
        print("Done! 🎬")


def main():
    parser = argparse.ArgumentParser(
        description="Voice-activated teleprompter. Shows one phrase at a time, advances when you stop speaking.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  🎤 Speak     Auto-advance when you pause
  Enter/Space  Next phrase (manual)
  B            Previous phrase
  Q            Quit

Tip: Run in fullscreen terminal with large font.
        """
    )
    parser.add_argument("script", help="Text file with your script")
    parser.add_argument("-m", "--manual", action="store_true", help="Manual mode (no voice detection)")
    parser.add_argument("-p", "--pause", type=float, default=1.2, help="Pause threshold in seconds (default: 1.2)")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.0")

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

    print(f"Loaded {len(phrases)} phrases from {args.script}")

    run_prompter(phrases, use_voice=not args.manual, pause_threshold=args.pause)


if __name__ == "__main__":
    main()
