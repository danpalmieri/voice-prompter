#!/usr/bin/env python3
"""
Voice-activated teleprompter - shows one phrase at a time,
advances when you stop speaking.

Usage: python prompter.py script.txt
"""

import sys
import os
import re
import time

try:
    import speech_recognition as sr
except ImportError:
    print("Installing speech_recognition...")
    os.system("pip install SpeechRecognition")
    import speech_recognition as sr

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def split_into_phrases(text):
    """Split text into speakable phrases."""
    # Split on sentence endings and common pause points
    phrases = re.split(r'(?<=[.!?])\s+|(?<=,)\s+(?=\w{20,})', text)
    # Clean up and filter empty
    phrases = [p.strip() for p in phrases if p.strip()]
    # If phrases are too long, split further
    result = []
    for p in phrases:
        if len(p) > 150:
            # Split long phrases on commas
            subphrases = re.split(r',\s*', p)
            result.extend([sp.strip() for sp in subphrases if sp.strip()])
        else:
            result.append(p)
    return result

def display_phrase(phrase, current, total):
    """Display phrase prominently in terminal."""
    clear_screen()
    term_width = os.get_terminal_size().columns
    term_height = os.get_terminal_size().lines
    
    # Header
    progress = f"[{current}/{total}]"
    print(f"\n{'─' * term_width}")
    print(f"{progress:^{term_width}}")
    print(f"{'─' * term_width}\n")
    
    # Center the phrase vertically
    padding_top = (term_height - 10) // 2
    print("\n" * max(0, padding_top - 4))
    
    # Word wrap the phrase
    words = phrase.split()
    lines = []
    current_line = ""
    max_width = min(term_width - 4, 80)
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_width:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Display centered
    for line in lines:
        print(f"{line:^{term_width}}")
    
    print("\n" * 3)
    print(f"{'🎤 Falando... (Enter para avançar manual, Q para sair)':^{term_width}}")

def wait_for_speech_end(recognizer, mic):
    """Wait for user to speak and then stop."""
    with mic as source:
        try:
            # Listen for speech (with timeout)
            audio = recognizer.listen(source, timeout=30, phrase_time_limit=15)
            return True
        except sr.WaitTimeoutError:
            return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python prompter.py <arquivo.txt>")
        print("\nControles:")
        print("  Enter = próxima frase")
        print("  B = voltar")
        print("  Q = sair")
        print("\nOu fale e ele avança automaticamente quando você parar.")
        sys.exit(1)
    
    # Load script
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    
    phrases = split_into_phrases(text)
    total = len(phrases)
    
    if total == 0:
        print("Arquivo vazio!")
        sys.exit(1)
    
    # Setup speech recognition
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Adjust for ambient noise
    recognizer.pause_threshold = 1.5   # Seconds of silence to consider phrase done
    recognizer.dynamic_energy_threshold = True
    
    try:
        mic = sr.Microphone()
        # Calibrate for ambient noise
        print("Calibrando microfone...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        use_voice = True
    except Exception as e:
        print(f"Microfone não disponível: {e}")
        print("Modo manual (Enter para avançar)")
        use_voice = False
        time.sleep(2)
    
    current = 0
    
    # Set terminal to non-blocking input
    import select
    import tty
    import termios
    
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        while current < total:
            display_phrase(phrases[current], current + 1, total)
            
            if use_voice:
                # Listen for speech in background while checking for key input
                with mic as source:
                    try:
                        # Non-blocking check for keyboard
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1).lower()
                            if key == 'q':
                                break
                            elif key == 'b' and current > 0:
                                current -= 1
                                continue
                            elif key in ['\n', '\r', ' ']:
                                current += 1
                                continue
                        
                        # Listen for speech
                        audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=10)
                        # Speech detected and ended, advance
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
                elif key in ['\n', '\r', ' ']:
                    current += 1
    
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        clear_screen()
        print("Fim! 🎬")

if __name__ == "__main__":
    main()
