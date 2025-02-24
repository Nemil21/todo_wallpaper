#!/usr/bin/env python3
import os
import sys
import pygame
from pynput import keyboard
from PIL import Image, ImageDraw, ImageFont

# File Paths
TODO_FILE = "/home/nemilai/Desktop/TodoWallpaper/todo.md"
IMAGE_FILE = "/home/nemilai/Desktop/TodoWallpaper/todo.png"
FONT_PATH = "/home/nemilai/Downloads/DejaVu_Sans/DejaVuSans-Bold.ttf"

# Screen resolution for the generated wallpaper
WALLPAPER_WIDTH = 1920
WALLPAPER_HEIGHT = 1080

def create_todo_file_if_not_exists():
    """Create a sample todo file if none exists."""
    if not os.path.exists(TODO_FILE):
        os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
        with open(TODO_FILE, "w") as f:
            f.write("[ ] Sample Task\n")

def markdown_to_image():
    """
    Convert lines in TODO_FILE to an image representing a to-do list,
    and set it as the current desktop wallpaper.
    """
    with open(TODO_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Create a blank background
    img = Image.new("RGB", (WALLPAPER_WIDTH, WALLPAPER_HEIGHT), "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 36)

    y_offset = 40
    for line in lines:
        # Replace “[ ]” or “[x]” with a Unicode checkbox
        if "[ ]" in line:
            todo_text = line.replace("[ ]", "☐").strip()
        elif "[x]" in line:
            todo_text = line.replace("[x]", "☑").strip()
        else:
            todo_text = line.strip()

        draw.text((50, y_offset), todo_text, fill="white", font=font)
        y_offset += 50

    img.save(IMAGE_FILE)
    # On GNOME-based Ubuntu
    os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{IMAGE_FILE}")

def toggle_checkbox(lines, index):
    """Toggle the checkbox in a given line if present."""
    if index < 0 or index >= len(lines):
        return lines
    line = lines[index]
    if "[ ]" in line:
        lines[index] = line.replace("[ ]", "[x]", 1)
    elif "[x]" in line:
        lines[index] = line.replace("[x]", "[ ]", 1)
    return lines

def save_todo_lines(lines):
    """Save updated lines to the TODO_FILE."""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        # Ensure each line ends with a newline
        f.write("\n".join(line.rstrip("\n") for line in lines) + "\n")

def background_edit_mode():
    """
    Run a headless edit mode using SDL_VIDEODRIVER=dummy
    so that we can detect key presses without showing a new visible window.
    """
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Required so pygame can capture events, but it won't be shown
    screen = pygame.display.set_mode((1, 1), pygame.NOFRAME)
    pygame.display.set_caption("Invisible To-Do List Editor")

    # Load lines and start editing
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cursor_pos = 0
    editing = True

    while editing:
        # Pump events so pygame can register key presses
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    lines = toggle_checkbox(lines, cursor_pos)
                elif event.key == pygame.K_UP:
                    cursor_pos = max(0, cursor_pos - 1)
                elif event.key == pygame.K_DOWN:
                    cursor_pos = min(len(lines) - 1, cursor_pos + 1)
                elif event.key == pygame.K_RETURN:
                    # Insert a new unchecked line below
                    lines.insert(cursor_pos + 1, "[ ] New Task\n")
                    cursor_pos += 1
                elif event.key == pygame.K_BACKSPACE:
                    # Delete current line
                    if lines:
                        lines.pop(cursor_pos)
                        cursor_pos = min(cursor_pos, len(lines) - 1)
                elif event.key == pygame.K_ESCAPE:
                    # Exit edit mode
                    editing = False

    # Save and update wallpaper after editing
    save_todo_lines(lines)
    markdown_to_image()
    pygame.quit()

def on_press(key):
    """
    Global key listener callback:
    Press 'i' to enter edit mode; press ESC (there) to exit.
    """
    if hasattr(key, 'char') and key.char == 'i':
        background_edit_mode()

def main():
    """
    Main entry point:
    1. Create a default todo file if needed.
    2. Generate the initial wallpaper.
    3. Listen for the 'i' keystroke globally, so user can trigger edit mode.
    """
    create_todo_file_if_not_exists()
    markdown_to_image()  # Generate wallpaper once initially

    # Start global keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Keep running until the user stops the script
    try:
        listener.join()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()