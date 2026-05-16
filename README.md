# Typespeed

A simple terminal-based typing speed test built with Python and the `curses` library.

## What this project is

This is a speed typing test that displays a random sentence from a text file and measures your typing performance in real time. It tracks:

- Words per minute (WPM)
- Correct vs incorrect typed characters
- Typing progress through the current sentence

The project uses `curses` to render the UI in the terminal and accepts keyboard input while the timer runs.

## Files

- `typespeed.py` - main Python script for the typing test
- `text.txt` - list of sample sentences used by the test
- `README.md` - this documentation file

## Requirements

- Python 3.8+ (works with Python 3.14)
- A terminal that supports `curses` (macOS/Linux)

## How to run

1. Open a terminal.
2. Change to the project folder:

```bash
cd "/Users/omkadam/Documents/Om Kadam/PROJECTS/Projects(Python)/Typespeed"
```

3. Run the script:

```bash
python3 typespeed.py
```

4. Follow the on-screen instructions:

- Press any key to begin
- Type the sentence shown on screen
- Use backspace to correct mistakes
- Press `Esc` to exit

## Customizing the text

To change the typing prompts, edit `text.txt` and add or replace sentences. Each line in the file is treated as a separate text prompt.

## Notes

- If you see errors related to `text.txt`, make sure the file exists in the same folder as `typespeed.py`.
- This project is intended as a lightweight learning tool for terminal-based UI and typing practice.
