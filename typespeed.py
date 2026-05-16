import curses
from curses import wrapper
import time
import random
import os


# ─── Ghost record ────────────────────────────────────────────────────────────
# A "run" is stored as a list of floats: the timestamp (relative to run-start)
# at which each character was typed.  Index = character position.
# ghost_records = { sentence_text: {"times": [float, ...], "wpm": int} }
ghost_records = {}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_text(filepath="text.txt"):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"'{filepath}' not found. Create it with one sentence per line.")
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    if not lines:
        raise ValueError(f"'{filepath}' is empty. Add at least one line of text.")
    return random.choice(lines)


def calc_wpm(n_chars, elapsed_seconds):
    elapsed_seconds = max(elapsed_seconds, 1)
    return round((n_chars / 5) / (elapsed_seconds / 60))


def ghost_position_at(times, elapsed):
    """Return how many chars the ghost has typed by `elapsed` seconds."""
    pos = 0
    for t in times:
        if t <= elapsed:
            pos += 1
        else:
            break
    return pos


# ─── Display ─────────────────────────────────────────────────────────────────

def draw_screen(stdscr, target, current, wpm, ghost_pos, ghost_wpm, ahead):
    """Render the full frame."""
    max_y, max_x = stdscr.getmaxyx()

    # Row 0: target text with typed overlay + ghost cursor
    stdscr.addstr(0, 0, target, curses.color_pair(3))

    # Ghost cursor (cyan block on the next-to-type ghost char)
    if ghost_pos < len(target):
        stdscr.addstr(0, ghost_pos, target[ghost_pos], curses.color_pair(5))

    # Player's typed characters (green / red) drawn on top
    for i, char in enumerate(current):
        color = curses.color_pair(1) if char == target[i] else curses.color_pair(2)
        stdscr.addstr(0, i, char, color)

    # Underline + bold the next character to type
    cursor_pos = len(current)
    if cursor_pos < len(target):
        stdscr.addstr(0, cursor_pos, target[cursor_pos],
                      curses.color_pair(3) | curses.A_UNDERLINE | curses.A_BOLD)

    # Row 2: stats bar
    ghost_str = f"Ghost: {ghost_wpm} WPM" if ghost_wpm else "Ghost: --"
    if ghost_wpm:
        delta = ahead
        delta_str = f"+{delta} chars ahead" if delta >= 0 else f"{delta} chars behind"
    else:
        delta_str = ""

    stats = f"WPM: {wpm:<4}  |  {ghost_str}  {delta_str}"
    stdscr.addstr(2, 0, stats[:max_x - 1], curses.color_pair(3))

    # Row 3: progress bar
    bar_width = min(len(target), max_x - 12)
    filled = int(bar_width * len(current) / max(len(target), 1))
    bar = "█" * filled + "░" * (bar_width - filled)
    pct = int(100 * len(current) / max(len(target), 1))
    stdscr.addstr(3, 0, f"[{bar}] {pct:3d}%"[:max_x - 1], curses.color_pair(4))

    # Row 5: hint
    stdscr.addstr(5, 0, "ESC quit  |  BACKSPACE correct", curses.color_pair(3))


def draw_results(stdscr, target, current, wpm, ghost_wpm, beat_ghost):
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    # Replay the completed text fully green
    stdscr.addstr(0, 0, target, curses.color_pair(1))

    msg = f"  Finished!  WPM: {wpm}"
    if ghost_wpm:
        if beat_ghost:
            msg += f"  |  Beat the ghost! ({ghost_wpm} WPM)  New record!"
        else:
            msg += f"  |  Ghost: {ghost_wpm} WPM  (try again!)"

    stdscr.addstr(2, 0, msg[:max_x - 1], curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(3, 0, "Press any key to play again, or ESC to quit.")
    stdscr.refresh()


# ─── Core game loop ──────────────────────────────────────────────────────────

def wpm_test(stdscr, target_text):
    global ghost_records

    current_text = []
    keystroke_times = []   # parallel list: time each char was typed (relative to start)

    wpm = 0
    start_time = None
    stdscr.nodelay(True)

    while True:
        now = time.time()
        elapsed = (now - start_time) if start_time else 0

        # Ghost calculations
        ghost_pos = 0
        ghost_wpm = 0
        ahead = 0
        ghost = ghost_records.get(target_text)
        if ghost:
            ghost_pos = ghost_position_at(ghost["times"], elapsed)
            ghost_wpm = ghost["wpm"]
            ahead = len(current_text) - ghost_pos

        stdscr.clear()
        draw_screen(stdscr, target_text, current_text, wpm,
                    ghost_pos, ghost_wpm, ahead)
        stdscr.refresh()

        try:
            key = stdscr.getkey()
        except curses.error:
            if start_time is not None:
                wpm = calc_wpm(len(current_text), elapsed)
            time.sleep(0.05)
            continue

        if key == '\x1b':
            return False

        if key in ("KEY_BACKSPACE", '\b', '\x7f'):
            if current_text:
                current_text.pop()
                keystroke_times.pop()
            continue

        if len(key) == 1 and len(current_text) < len(target_text):
            if start_time is None:
                start_time = time.time()
                elapsed = 0
            current_text.append(key)
            keystroke_times.append(time.time() - start_time)

        if start_time is not None:
            wpm = calc_wpm(len(current_text), time.time() - start_time)

        # Completion check
        if "".join(current_text) == target_text:
            stdscr.nodelay(False)
            final_wpm = calc_wpm(len(current_text), time.time() - start_time)

            ghost_wpm_final = ghost_records[target_text]["wpm"] if target_text in ghost_records else 0
            beat = final_wpm > ghost_wpm_final

            # Always save on first run for this text, update only if improved
            if target_text not in ghost_records or final_wpm > ghost_records[target_text]["wpm"]:
                ghost_records[target_text] = {
                    "times": keystroke_times[:],
                    "wpm": final_wpm,
                }

            draw_results(stdscr, target_text, current_text,
                         final_wpm, ghost_wpm_final, beat)
            return True


# ─── Start screen ────────────────────────────────────────────────────────────

def start_screen(stdscr, target_text):
    stdscr.clear()
    stdscr.addstr(0, 0, "Speed Typing  --  Ghost Mode", curses.A_BOLD)
    stdscr.addstr(2, 0, "Race your best run. Each completed attempt saves a ghost.")
    stdscr.addstr(3, 0, "Cyan highlight = ghost cursor position.")
    stdscr.addstr(4, 0, "Beat it to set a new record.")

    # Show ghost status for this sentence
    if target_text in ghost_records:
        stdscr.addstr(6, 0, f"Ghost on deck: {ghost_records[target_text]['wpm']} WPM  -- beat it!",
                      curses.color_pair(5))
    else:
        stdscr.addstr(6, 0, "No ghost yet -- complete a run to set one.",
                      curses.color_pair(3))

    stdscr.addstr(8, 0, "Press any key to begin, or ESC to quit.")
    stdscr.refresh()
    key = stdscr.getkey()
    return key != '\x1b'


# ─── Entry point ─────────────────────────────────────────────────────────────

def main(stdscr):
    curses.init_pair(1, curses.COLOR_GREEN,  curses.COLOR_BLACK)  # correct chars
    curses.init_pair(2, curses.COLOR_RED,    curses.COLOR_BLACK)  # wrong chars
    curses.init_pair(3, curses.COLOR_WHITE,  curses.COLOR_BLACK)  # neutral UI
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # progress bar
    curses.init_pair(5, curses.COLOR_BLACK,  curses.COLOR_CYAN)   # ghost cursor

    try:
        first_text = load_text()
    except (FileNotFoundError, ValueError) as e:
        stdscr.addstr(0, 0, str(e))
        stdscr.addstr(1, 0, "Press any key to exit.")
        stdscr.refresh()
        stdscr.getkey()
        return

    if not start_screen(stdscr, first_text):
        return

    next_text = first_text
    while True:
        try:
            completed = wpm_test(stdscr, next_text)
        except (FileNotFoundError, ValueError) as e:
            stdscr.nodelay(False)
            stdscr.clear()
            stdscr.addstr(0, 0, str(e))
            stdscr.addstr(1, 0, "Press any key to exit.")
            stdscr.refresh()
            stdscr.getkey()
            return

        if not completed:
            break

        stdscr.nodelay(False)
        next_text = load_text()
        key = stdscr.getkey()
        if key == '\x1b':
            break


wrapper(main)