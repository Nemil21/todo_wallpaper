#!/usr/bin/env python3
import json
import os
from pathlib import Path
import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from Xlib import display, X
from Xlib.ext import record
from Xlib.protocol import rq
import threading

class WallpaperTodo:
    def __init__(self):
        self.edit_mode = False
        self.todos = self.load_todos()
        self.current_text = ""
        self.setup_window()
        self.setup_keyboard_listener()

    def load_todos(self):
        try:
            config_dir = Path.home() / '.config' / 'wallpaper-todo'
            config_dir.mkdir(parents=True, exist_ok=True)
            todo_file = config_dir / 'todos.json'
            if todo_file.exists():
                with open(todo_file) as f:
                    return json.load(f)
            return []
        except Exception:
            return []

    def save_todos(self):
        try:
            config_dir = Path.home() / '.config' / 'wallpaper-todo'
            todo_file = config_dir / 'todos.json'
            with open(todo_file, 'w') as f:
                json.dump(self.todos, f)
        except Exception as e:
            print(f"Error saving todos: {e}")

    def setup_window(self):
        self.window = Gtk.Window()
        self.window.set_title("Wallpaper Todo")
        self.window.set_app_paintable(True)
        self.window.set_visual(self.window.get_screen().get_rgba_visual())
        self.window.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.window.set_keep_below(True)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect('draw', self.on_draw)
        self.window.add(self.drawing_area)

        self.window.connect('destroy', Gtk.main_quit)
        self.window.connect('key-press-event', self.on_key_press)
        
        # Make window fullscreen and show
        self.window.fullscreen()
        self.window.show_all()

    def setup_keyboard_listener(self):
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()
        
        ctx = self.record_dpy.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.KeyPress, X.KeyRelease),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }]
        )

        threading.Thread(target=self.start_keyboard_listener, args=(ctx,), daemon=True).start()

    def start_keyboard_listener(self, ctx):
        self.record_dpy.record_enable_context(ctx, self.process_key_event)
        self.record_dpy.record_free_context(ctx)

    def process_key_event(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            return
        
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, self.record_dpy.display, None, None)
            
            if event.type == X.KeyPress:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
                if keysym == 105:  # 'i' key
                    GLib.idle_add(self.enter_edit_mode)
                elif keysym == 9:  # ESC key
                    GLib.idle_add(self.exit_edit_mode)

    def enter_edit_mode(self):
        self.edit_mode = True
        self.window.queue_draw()

    def exit_edit_mode(self):
        if self.edit_mode and self.current_text.strip():
            self.todos.append({"text": self.current_text.strip(), "done": False})
            self.current_text = ""
            self.save_todos()
        self.edit_mode = False
        self.window.queue_draw()

    def on_key_press(self, widget, event):
        if self.edit_mode:
            keyname = Gdk.keyval_name(event.keyval)
            if keyname == 'BackSpace':
                self.current_text = self.current_text[:-1]
            elif keyname == 'Return':
                self.exit_edit_mode()
            elif len(keyname) == 1:
                self.current_text += keyname
            self.window.queue_draw()
        return True

    def on_draw(self, drawing_area, cr):
        # Clear the surface
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        # Set up text drawing
        cr.set_source_rgba(1, 1, 1, 0.8)
        cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(20)

        # Draw title
        cr.move_to(50, 50)
        cr.show_text("Todo List (Press 'i' to edit, 'ESC' to save)")

        # Draw todos
        y = 100
        for i, todo in enumerate(self.todos):
            cr.move_to(50, y)
            status = "☒" if todo["done"] else "☐"
            cr.show_text(f"{status} {todo['text']}")
            y += 30

        # Draw current input in edit mode
        if self.edit_mode:
            cr.move_to(50, y)
            cr.show_text(f"New todo: {self.current_text}_")

        return False

if __name__ == "__main__":
    app = WallpaperTodo()
    Gtk.main()