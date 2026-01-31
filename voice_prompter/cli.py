#!/usr/bin/env python3
"""
Voice Prompter - Voice-activated teleprompter CLI.

Shows one phrase at a time, advances when it recognizes you speaking the phrase.
"""

import sys
import os
import re
import argparse
import threading
import queue

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


def normalize_text(text):
    """Normalize text for comparison."""
    text = re.sub(r'[^\w\s]', '', text.lower())
    text = ' '.join(text.split())
    return text


def texts_match(spoken, expected, threshold=0.4):
    """Check if spoken text matches expected phrase."""
    spoken_norm = normalize_text(spoken)
    expected_norm = normalize_text(expected)
    
    if not spoken_norm or not expected_norm:
        return False
    
    expected_words = set(expected_norm.split())
    spoken_words = set(spoken_norm.split())
    
    if not expected_words:
        return False
    
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

    # Header
    progress = f"[{current}/{total}]"
    print(f"\033[90m{progress:^{w}}\033[0m")
    print()

    # Word wrap
    available_height = h - 6
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

    # Footer
    remaining_lines = h - padding_top - text_height - 4
    print("\n" * max(0, remaining_lines))
    print(f"\033[90m{'🎤 Fale... | ESPAÇO=próx | B=volta | Q=sair':^{w}}\033[0m")


def keyboard_listener(cmd_queue, stop_event):
    """Listen for keyboard input in a separate thread."""
    import tty
    import termios
    
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while not stop_event.is_set():
            import select
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1).lower()
                cmd_queue.put(('key', key))
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def voice_listener(cmd_queue, phrase_queue, stop_event, recognizer, mic, match_threshold):
    """Listen for voice in a separate thread."""
    while not stop_event.is_set():
        try:
            # Get current expected phrase
            try:
                expected = phrase_queue.get_nowait()
            except queue.Empty:
                expected = None
            
            if expected is None:
                import time
                time.sleep(0.1)
                continue
                
            with mic as source:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    
                    try:
                        spoken = recognizer.recognize_google(audio, language="pt-BR")
                        if texts_match(spoken, expected, match_threshold):
                            cmd_queue.put(('voice', 'next'))
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        cmd_queue.put(('voice', 'next'))
                        
                except sr.WaitTimeoutError:
                    continue
        except Exception as e:
            import time
            time.sleep(0.1)


def run_prompter(phrases, use_voice=True, pause_threshold=1.5, match_threshold=0.4):
    """Run the prompter loop."""
    total = len(phrases)
    current = 0

    cmd_queue = queue.Queue()
    phrase_queue = queue.Queue()
    stop_event = threading.Event()

    # Start keyboard listener thread
    kb_thread = threading.Thread(target=keyboard_listener, args=(cmd_queue, stop_event), daemon=True)
    kb_thread.start()

    # Setup voice if enabled
    voice_thread = None
    if use_voice:
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = pause_threshold
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 400
        
        try:
            mic = sr.Microphone()
            print("Calibrando microfone...")
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"Calibrado! (threshold: {int(recognizer.energy_threshold)})")
            
            voice_thread = threading.Thread(
                target=voice_listener,
                args=(cmd_queue, phrase_queue, stop_event, recognizer, mic, match_threshold),
                daemon=True
            )
            voice_thread.start()
        except Exception as e:
            print(f"Microfone não disponível: {e}")
            print("Modo manual ativado.")
            use_voice = False
            import time
            time.sleep(1)

    try:
        while current < total:
            display(phrases[current], current + 1, total)
            
            # Send current phrase to voice listener
            if use_voice:
                # Clear old phrases
                while not phrase_queue.empty():
                    try:
                        phrase_queue.get_nowait()
                    except queue.Empty:
                        break
                phrase_queue.put(phrases[current])

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
  🎤 Speak     Advances when you say the phrase
  Space/Enter  Next phrase
  B            Previous phrase  
  Q            Quit
        """
    )
    parser.add_argument("script", help="Text file with your script")
    parser.add_argument("-m", "--manual", action="store_true", help="Manual mode (no voice)")
    parser.add_argument("-p", "--pause", type=float, default=1.5, help="Pause threshold (default: 1.5)")
    parser.add_argument("-t", "--threshold", type=float, default=0.4, help="Match threshold 0-1 (default: 0.4)")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.2")

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

    print(f"📜 {len(phrases)} frases carregadas")
    print("💡 Aumente a fonte: Cmd + (Mac) ou Ctrl + (Linux)")
    print()

    run_prompter(phrases, use_voice=not args.manual, pause_threshold=args.pause, match_threshold=args.threshold)


if __name__ == "__main__":
    main()
