#!/usr/bin/env python3
"""
Voice Prompter - Horizontal scrolling teleprompter.
"""

import sys
import os
import time
import curses


def load_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return ' '.join(text.split())


def run_marquee(stdscr, text):
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(16)  # ~60fps
    
    # Colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, 8, -1)  # Gray
    
    h, w = stdscr.getmaxyx()
    
    # Pad text
    padded = ' ' * w + text + ' ' * w
    total_len = len(text) + w
    
    offset = 0.0
    speed = 0.0
    base_speed = 6  # even slower
    
    last_time = time.time()
    
    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
        
        # Update
        offset += speed * dt
        
        if offset < 0:
            offset = 0
            speed = 0
        if offset > total_len:
            offset = total_len
            speed = 0
        
        # Get visible
        start = int(offset)
        visible = padded[start:start + w]
        if len(visible) < w:
            visible = visible.ljust(w)
        
        # Draw text at TOP
        try:
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(1, 0, visible[:w-1])
            stdscr.attroff(curses.A_BOLD)
        except:
            pass
        
        # Progress bar at BOTTOM
        progress = offset / total_len if total_len > 0 else 0
        bar_w = w - 12
        filled = int(bar_w * min(progress, 1.0))
        bar = '█' * filled + '░' * (bar_w - filled)
        pct = int(progress * 100)
        
        try:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(h - 3, 0, f"{bar} {pct:3d}%"[:w-1])
            stdscr.attroff(curses.color_pair(2))
        except:
            pass
        
        # Status
        if speed == 0:
            status = "⏸ PAUSED | → play | ← back | Q quit"
        elif speed > 0:
            status = f"→ {speed:.0f} c/s | → faster | ← slower | SPACE pause"
        else:
            status = f"← {-speed:.0f} c/s | ← faster | → slower | SPACE pause"
        
        try:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(h - 1, 0, status[:w-1].ljust(w-1))
            stdscr.attroff(curses.color_pair(2))
        except:
            pass
        
        stdscr.refresh()
        
        # Input
        try:
            key = stdscr.getch()
        except:
            key = -1
        
        if key == ord('q'):
            break
        elif key == ord(' '):
            speed = 0 if speed != 0 else base_speed
        elif key == curses.KEY_RIGHT:
            if speed <= 0:
                speed = base_speed
            else:
                speed = min(speed + 3, 60)
        elif key == curses.KEY_LEFT:
            if speed >= 0:
                speed = -base_speed
            else:
                speed = max(speed - 3, -60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Horizontal scrolling teleprompter")
    parser.add_argument("script", help="Text file")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.3.3")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.script):
        print(f"Error: {args.script} not found")
        sys.exit(1)
    
    text = load_text(args.script)
    
    if not text:
        print("Error: No text")
        sys.exit(1)
    
    print(f"📜 {len(text)} chars")
    print("💡 Cmd + for bigger font")
    print("→ to start, Q to quit")
    time.sleep(1)
    
    curses.wrapper(lambda stdscr: run_marquee(stdscr, text))
    print("Done! 🎬")


if __name__ == "__main__":
    main()
