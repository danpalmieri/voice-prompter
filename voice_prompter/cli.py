#!/usr/bin/env python3
"""
Voice Prompter - Voice-activated teleprompter CLI.

Shows one phrase at a time, advances when it recognizes you speaking the phrase.
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


def split_phrases(text, max_length=100):
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


def normalize_text(text):
    """Normalize text for comparison."""
    # Remove punctuation, lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def texts_match(spoken, expected, threshold=0.4):
    """Check if spoken text matches expected phrase."""
    spoken_norm = normalize_text(spoken)
    expected_norm = normalize_text(expected)
    
    if not spoken_norm or not expected_norm:
        return False
    
    # Check if key words from expected are in spoken
    expected_words = set(expected_norm.split())
    spoken_words = set(spoken_norm.split())
    
    if not expected_words:
        return False
    
    # Calculate overlap
    overlap = len(expected_words & spoken_words) / len(expected_words)
    return overlap >= threshold


def display(phrase, current, total):
    """Display phrase BIG in terminal."""
    clear()
    try:
        w = os.get_terminal_size().columns
        h = os.get_terminal_size().lines
    except OSError:
        w, h = 80, 24

    # Header (small)
    progress = f"[{current}/{total}]"
    print(f"\033[90m{progress:^{w}}\033[0m")
    print()

    # Calculate how much space we have for the phrase
    available_height = h - 6
    
    # Word wrap with wider lines
    words = phrase.split()
    max_width = min(w - 4, 60)  # Shorter lines = bigger feel
    
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
        # Bold + larger visual impact
        print(f"\033[1m{l:^{w}}\033[0m")

    # Footer
    remaining_lines = h - padding_top - text_height - 4
    print("\n" * max(0, remaining_lines))
    print(f"\033[90m{'🎤 Fale a frase... (Enter=próx, B=volta, Q=sair)':^{w}}\033[0m")


def run_prompter(phrases, use_voice=True, pause_threshold=1.5, match_threshold=0.4):
    """Run the prompter loop."""
    total = len(phrases)
    current = 0

    recognizer = None
    mic = None

    if use_voice:
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = pause_threshold
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 400  # Higher = less sensitive to background noise
        try:
            mic = sr.Microphone()
            print("Calibrando microfone...")
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"Calibrado! Energy threshold: {recognizer.energy_threshold}")
        except Exception as e:
            print(f"Microfone não disponível: {e}")
            print("Modo manual ativado.")
            use_voice = False
            import time
            time.sleep(1)

    # Set terminal to non-blocking
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while current < total:
            display(phrases[current], current + 1, total)
            expected_phrase = phrases[current]

            if use_voice and mic:
                with mic as source:
                    try:
                        # Check keyboard first
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
                        
                        # Try to recognize what was said
                        try:
                            spoken = recognizer.recognize_google(audio, language="pt-BR")
                            # Check if it matches the expected phrase
                            if texts_match(spoken, expected_phrase, match_threshold):
                                current += 1
                            # If not a match, stay on same phrase (ignore background noise)
                        except sr.UnknownValueError:
                            # Couldn't understand - ignore (probably background noise)
                            pass
                        except sr.RequestError:
                            # API error - fall back to simple detection
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
        print("Fim! 🎬")


def main():
    parser = argparse.ArgumentParser(
        description="Voice-activated teleprompter. Shows one phrase at a time, advances when you speak the phrase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  🎤 Speak     Advances when you say the phrase
  Enter/Space  Next phrase (manual)
  B            Previous phrase
  Q            Quit

Tip: Run in fullscreen terminal with large font (Cmd+ on Mac).
        """
    )
    parser.add_argument("script", help="Text file with your script")
    parser.add_argument("-m", "--manual", action="store_true", help="Manual mode (no voice detection)")
    parser.add_argument("-p", "--pause", type=float, default=1.5, help="Pause threshold in seconds (default: 1.5)")
    parser.add_argument("-t", "--threshold", type=float, default=0.4, help="Match threshold 0-1 (default: 0.4)")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.1")

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

    print(f"Carregando {len(phrases)} frases de {args.script}")
    print("Dica: Aumente a fonte do terminal (Cmd +) para texto maior!")
    print()

    run_prompter(phrases, use_voice=not args.manual, pause_threshold=args.pause, match_threshold=args.threshold)


if __name__ == "__main__":
    main()
