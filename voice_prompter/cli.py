#!/usr/bin/env python3
"""
Voice Prompter - Horizontal scrolling teleprompter.
"""

import sys
import os
import time


def load_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return ' '.join(text.split())


def run_marquee(text):
    import tty
    import termios
    import select
    
    try:
        w = os.get_terminal_size().columns
        h = os.get_terminal_size().lines
    except OSError:
        w, h = 80, 24

    # Pad text
    padded = ' ' * w + text + ' ' * w
    
    offset = 0.0
    speed = 0.0  # chars per second (0 = paused)
    base_speed = 20
    
    old_settings = termios.tcgetattr(sys.stdin)
    
    # Setup terminal
    sys.stdout.write('\033[?25l')  # Hide cursor
    sys.stdout.write('\033[2J')    # Clear screen
    sys.stdout.flush()
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        last_time = time.time()
        
        while True:
            now = time.time()
            dt = now - last_time
            last_time = now
            
            # Update position
            offset += speed * dt
            
            # Clamp
            max_offset = len(text) + w
            if offset < 0:
                offset = 0
                speed = 0
            if offset > max_offset:
                offset = max_offset
                speed = 0
            
            # Get visible text
            start = int(offset) % len(padded)
            visible = padded[start:start + w]
            if len(visible) < w:
                visible += padded[:w - len(visible)]
            
            # Draw at TOP (line 2)
            sys.stdout.write('\033[2;1H')  # Move to row 2, col 1
            sys.stdout.write(f'\033[1;97m{visible}\033[0m')
            
            # Status at bottom
            sys.stdout.write(f'\033[{h};1H')
            if speed == 0:
                status = "⏸ PAUSED  |  →=play  ←=back  Q=quit"
            elif speed > 0:
                status = f"→ {speed:.0f} c/s  |  →=faster  ←=slower  SPACE=pause"
            else:
                status = f"← {-speed:.0f} c/s  |  →=slower  ←=faster  SPACE=pause"
            sys.stdout.write(f'\033[90m{status:<{w}}\033[0m')
            
            sys.stdout.flush()
            
            # Input check
            if select.select([sys.stdin], [], [], 0.016)[0]:
                key = sys.stdin.read(1)
                
                if key == 'q':
                    break
                elif key == ' ':
                    speed = 0 if speed != 0 else base_speed
                elif key == '\x1b':
                    # Arrow key
                    sys.stdin.read(1)  # skip [
                    arrow = sys.stdin.read(1)
                    
                    if arrow == 'C':  # Right
                        if speed <= 0:
                            speed = base_speed
                        else:
                            speed = min(speed + 10, 100)
                    elif arrow == 'D':  # Left
                        if speed >= 0:
                            speed = -base_speed
                        else:
                            speed = max(speed - 10, -100)
    
    finally:
        sys.stdout.write('\033[?25h')  # Show cursor
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdout.write('\033[2J\033[H')  # Clear
        print("Done! 🎬")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Horizontal scrolling teleprompter")
    parser.add_argument("script", help="Text file")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.3.1")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.script):
        print(f"Error: {args.script} not found")
        sys.exit(1)
    
    text = load_text(args.script)
    
    if not text:
        print("Error: No text")
        sys.exit(1)
    
    print(f"📜 {len(text)} chars | Cmd + for bigger font")
    print("→ to start")
    time.sleep(0.5)
    
    run_marquee(text)


if __name__ == "__main__":
    main()
