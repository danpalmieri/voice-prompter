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
    curses.curs_set(0)
    stdscr.nodelay(True)
    
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, 8, -1)
    
    h, w = stdscr.getmaxyx()
    
    padded = ' ' * w + text + ' ' * w
    total_len = len(text) + w
    
    offset = 0.0
    speed = 0.0
    speed_step = 2
    max_speed = 40
    
    last_time = time.perf_counter()
    last_offset_int = -1
    
    while True:
        now = time.perf_counter()
        dt = now - last_time
        last_time = now
        
        # Update position
        offset += speed * dt
        
        # Clamp
        if offset < 0:
            offset = 0
            speed = 0
        if offset > total_len:
            offset = total_len
            speed = 0
        
        # Only redraw if offset changed visually
        current_offset_int = int(offset)
        if current_offset_int != last_offset_int:
            last_offset_int = current_offset_int
            
            # Get visible text
            start = current_offset_int
            visible = padded[start:start + w]
            if len(visible) < w:
                visible = visible.ljust(w)
            
            # Draw text at TOP
            try:
                stdscr.move(1, 0)
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(visible[:w-1])
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
                stdscr.move(h - 3, 0)
                stdscr.addstr(f"{bar} {pct:3d}%"[:w-1])
                stdscr.attroff(curses.color_pair(2))
            except:
                pass
        
        # Status (always update for speed display)
        if speed == 0:
            status = "PAUSED | → start | Q quit"
        else:
            direction = "→" if speed > 0 else "←"
            status = f"{direction} {abs(speed):.0f} c/s | →/← adjust | SPACE pause"
        
        try:
            stdscr.attron(curses.color_pair(2))
            stdscr.move(h - 1, 0)
            stdscr.addstr(status[:w-1].ljust(w-1))
            stdscr.attroff(curses.color_pair(2))
        except:
            pass
        
        stdscr.refresh()
        
        # Input
        key = stdscr.getch()
        
        if key == ord('q'):
            break
        elif key == ord(' '):
            speed = 0
        elif key == curses.KEY_RIGHT:
            # Increase speed (or slow down if going backward)
            speed += speed_step
            if speed > max_speed:
                speed = max_speed
        elif key == curses.KEY_LEFT:
            # Decrease speed (or speed up backward)
            speed -= speed_step
            if speed < -max_speed:
                speed = -max_speed
        
        # Small sleep to prevent CPU spinning
        time.sleep(0.008)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Horizontal scrolling teleprompter")
    parser.add_argument("script", help="Text file")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.3.4")
    
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
    print("→ to start scrolling")
    time.sleep(1)
    
    curses.wrapper(lambda stdscr: run_marquee(stdscr, text))
    print("Done! 🎬")


if __name__ == "__main__":
    main()
