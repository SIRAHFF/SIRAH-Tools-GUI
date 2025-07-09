# main.py

import sys
import os
import tkinter as tk
import ttkbootstrap as ttk

# Add the 'modules' directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.load_files_tab import create_load_files_tab, AnalysisState
from modules.analysis_tab import create_analysis_tab
from modules.contacts_tab import create_contacts_tab
from modules.ss_analysis_tab import create_ss_analysis_tab
from modules.backmapping_tab import create_backmapping_tab
from modules.about_tab import create_about_tab

def apply_font_style(style):
    default_font = ("Sans-Serif", 11)
    style.configure('.', font=default_font)

def toggle_theme(app, theme_var, state, style):
    if theme_var.get() == "Dark":
        app.style.theme_use("superhero")
    else:
        app.style.theme_use("litera")

    apply_font_style(app.style)
    update_entry_text_color(state, app.style.theme_use())

def update_entry_text_color(state, theme_name):
    text_color = "black" if theme_name in ["litera", "journal"] else "white"
    for attr in ['atom_selection1', 'atom_selection2', 'atom_selection3']:
        widget = getattr(state, attr, None)
        if widget:
            widget.config(foreground=text_color)

def main():
    root = ttk.Window(themename="superhero")
    root.title("SIRAH TOOLS GUI v1.0")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    ASPECT_RATIO = 3 / 4
    max_width_percentage = 0.7
    max_height_percentage = 0.75

    max_window_width = int(screen_width * max_width_percentage)
    max_window_height = int(screen_height * max_height_percentage)

    window_width = max_window_width
    window_height = int(window_width / ASPECT_RATIO)

    if window_height > max_window_height:
        window_height = max_window_height
        window_width = int(window_height * ASPECT_RATIO)

    MIN_WIDTH = int(screen_width * 0.6)
    MIN_HEIGHT = int(screen_height * 0.9)
    window_width = max(window_width, MIN_WIDTH)
    window_height = max(window_height, MIN_HEIGHT)

    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    style = ttk.Style()
    apply_font_style(style)

    state = AnalysisState(root, style)

    top_frame = ttk.Frame(root)
    top_frame.pack(side="top", fill="both", expand=True)

    notebook = ttk.Notebook(top_frame)
    notebook.pack(side="left", padx=10, pady=10, fill="both", expand=True)

    theme_var = tk.StringVar(value="Dark")
    toggle_button = ttk.Checkbutton(
        top_frame,
        text="Dark/Light",
        variable=theme_var,
        onvalue="Dark",
        offvalue="Light",
        command=lambda: toggle_theme(root, theme_var, state, style),
        bootstyle="round-toggle"
    )
    toggle_button.place(relx=0.985, rely=0.015, anchor="ne")

    # Store tab creation info. We will use this to recreate tabs.
    tabs = {
        "Load Files": (create_load_files_tab, []),
        "Analysis": (create_analysis_tab, [style]),
        "Contacts": (create_contacts_tab, []),
        "SS Analysis": (create_ss_analysis_tab, []),
        "Backmapping": (create_backmapping_tab, []),
        "About/Help": (create_about_tab, [])
    }

    # Keep references to the frames so we can remove and re-add them
    tab_frames = {}
    # "Load Files" will be created first and we will define a reset_other_tabs function
    # that recreates all others.

    def reset_other_tabs():
        """
        This function resets all OTHER tabs (except Load Files) by removing them from the notebook
        and recreating them from scratch.
        """
        # Remember the load files tab frame so we don't destroy it
        # We'll remove all other tabs and recreate them.
        for tname in list(tab_frames.keys()):
            if tname != "Load Files":
                frame = tab_frames[tname]
                notebook.forget(frame)
                frame.destroy()
                del tab_frames[tname]

        # Recreate all other tabs
        for tab_name, (create_tab, extra_args) in tabs.items():
            if tab_name != "Load Files":
                new_frame = ttk.Frame(notebook)
                create_tab(new_frame, state, *extra_args)
                notebook.add(new_frame, text=tab_name)
                tab_frames[tab_name] = new_frame

    # Create the Load Files tab first, providing the reset_other_tabs callback
    load_files_frame = ttk.Frame(notebook)
    # Now create load files tab with the reset_other_tabs callback
    load_files_reset = tabs["Load Files"][0](load_files_frame, state, reset_callback=reset_other_tabs)
    notebook.add(load_files_frame, text="Load Files")
    tab_frames["Load Files"] = load_files_frame

    # Create the other tabs
    for tab_name, (create_tab, extra_args) in tabs.items():
        if tab_name != "Load Files":
            tab_frame = ttk.Frame(notebook)
            create_tab(tab_frame, state, *extra_args)
            notebook.add(tab_frame, text=tab_name)
            tab_frames[tab_name] = tab_frame

    def on_tab_changed(event):
        selected_tab = notebook.tab(notebook.index("current"))["text"]
        if selected_tab == "Analysis" and hasattr(state, 'analyze_button'):
            state.analyze_button.focus_set()

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    root.mainloop()

if __name__ == "__main__":
    main()
