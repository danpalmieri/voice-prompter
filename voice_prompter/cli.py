#!/usr/bin/env python3
"""
Voice Prompter - Horizontal scrolling teleprompter.

Text scrolls like a marquee/ticker across one line.
Arrow keys control speed and direction.
"""

import sys
import os
import re
import argparse
import time
import threading


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def load_text(filepath):
    """Load and join all text into one continuous string."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    # Join all lines, normalize whitespace
    text = ' '.join(text.split())
    return text


def display_marquee(text, offset, width, speed_indicator=""):
    """Display text as horizontal marquee."""
    # Move cursor to home position without full clear (less flicker)
    sys.stdout.write('\033[H')
    
    try:
        w = os.get_terminal_size().columns
        h = os.get_terminal_size().lines
    except OSError:
        w, h = 80, 24

    # Pad text with spaces for smooth scrolling
    padded = ' ' * w + text + ' ' * w
    
    # Calculate visible portion
    start = int(offset) % len(padded)
    visible = padded[start:start + w]
    if len(visible) < w:
        visible += padded[:w - len(visible)]

    # Clear screen and position
    clear()
    
    # Top padding to center vertically
    top_pad = (h - 4) // 2
    print('\n' * top_pad)
    
    # The marquee line - BIG and BOLD
    print(f'\033[1;97m{visible}\033[0m')
    
    # Bottom info
    print('\n' * (h - top_pad - 4))
    
    # Progress bar
    progress = offset / (len(text) + w)
    bar_width = w - 20
    filled = int(bar_width * min(progress, 1.0))
    bar = '█' * filled + '░' * (bar_width - filled)
    
    # Status line
    status = f'[{bar}] {speed_indicator}'
    print(f'\033[90m{status:^{w}}\033[0m')
    print(f'\033[90m{"→/← speed | SPACE=pause | Q=quit":^{w}}\033[0m')
    
    sys.stdout.flush()


def run_marquee(text):
    """Run the marquee prompter."""
    import tty
    import termios
    import select
    
    try:
        w = os.get_terminal_size().columns
    except OSError:
        w = 80

    offset = 0.0
    base_speed = 15  # chars per second
    speed_multiplier = 0.0  # 0 = paused
    direction = 1  # 1 = forward, -1 = backward
    
    last_key_time = 0
    tap_count = 0
    
    old_settings = termios.tcgetattr(sys.stdin)
    
    # Hide cursor
    sys.stdout.write('\033[?25l')
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        last_time = time.time()
        
        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Update position
            offset += base_speed * speed_multiplier * direction * dt
            
            # Clamp offset
            max_offset = len(text) + w
            if offset < 0:
                offset = 0
                speed_multiplier = 0
            if offset > max_offset:
                offset = max_offset
                speed_multiplier = 0
            
            # Speed indicator
            if speed_multiplier == 0:
                indicator = "⏸ PAUSED"
            else:
                arrow = "→→" if direction > 0 else "←←"
                if speed_multiplier == 1.0:
                    indicator = f"{arrow} 1x"
                elif speed_multiplier == 1.5:
                    indicator = f"{arrow} 1.5x"
                elif speed_multiplier == 2.0:
                    indicator = f"{arrow} 2x"
                else:
                    indicator = f"{arrow} {speed_multiplier:.1f}x"
            
            display_marquee(text, offset, w, indicator)
            
            # Check for input (non-blocking)
            if select.select([sys.stdin], [], [], 0.03)[0]:
                key = sys.stdin.read(1)
                
                if key == 'q':
                    break
                elif key == ' ':
                    # Toggle pause
                    if speed_multiplier == 0:
                        speed_multiplier = 1.0
                        direction = 1
                    else:
                        speed_multiplier = 0
                elif key == '\x1b':  # Escape sequence (arrow keys)
                    # Read the rest of the escape sequence
                    if select.select([sys.stdin], [], [], 0.01)[0]:
                        seq = sys.stdin.read(2)
                        
                        now = time.time()
                        
                        if seq == '[C':  # Right arrow
                            direction = 1
                            
                            # Check for double/triple tap
                            if now - last_key_time < 0.3:
                                tap_count += 1
                            else:
                                tap_count = 1
                            last_key_time = now
                            
                            if tap_count >= 3:
                                speed_multiplier = 2.0
                            elif tap_count == 2:
                                speed_multiplier = 1.5
                            else:
                                speed_multiplier = 1.0
                                
                        elif seq == '[D':  # Left arrow
                            direction = -1
                            
                            # Check for double/triple tap
                            if now - last_key_time < 0.3:
                                tap_count += 1
                            else:
                                tap_count = 1
                            last_key_time = now
                            
                            if tap_count >= 3:
                                speed_multiplier = 2.0
                            elif tap_count == 2:
                                speed_multiplier = 1.5
                            else:
                                speed_multiplier = 1.0
            
            time.sleep(0.016)  # ~60fps
    
    finally:
        # Show cursor
        sys.stdout.write('\033[?25h')
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        clear()
        print("Done! 🎬")


def main():
    parser = argparse.ArgumentParser(
        description="Horizontal scrolling teleprompter (marquee style).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Text scrolls horizontally like a ticker/marquee.

Controls:
  →          Scroll forward (1x, tap again for 1.5x, again for 2x)
  ←          Scroll backward (same speed logic)
  SPACE      Pause/resume
  Q          Quit

Tip: Increase terminal font size (Cmd +) for bigger text.
        """
    )
    parser.add_argument("script", help="Text file to display")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.3.0")

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"Error: {args.script} not found")
        sys.exit(1)

    text = load_text(args.script)

    if not text:
        print("Error: No text found")
        sys.exit(1)

    print(f"📜 {len(text)} characters")
    print("💡 Cmd + to increase font")
    print("Press → to start scrolling...")
    print()
    
    time.sleep(1)

    run_marquee(text)


if __name__ == "__main__":
    main()
