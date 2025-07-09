import tkinter as tk
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import subprocess
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend to avoid threading issues with matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import os
import threading
from fpdf import FPDF
import logging
import sys

def get_analysis_logger(working_directory):
    """
    Returns a logger for the analysis tab, with its handler set to Analysis/analysis.log
    """
    log_dir = os.path.join(working_directory, "Analysis")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "analysis.log")

    logger = logging.getLogger(f"SIRAH.Analysis")
    logger.setLevel(logging.INFO)

    # Remove existing file handlers for this logger
    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            logger.removeHandler(h)
            h.close()
    # Add new handler
    handler = logging.FileHandler(log_path)
    handler.setLevel(logging.INFO)   # or ERROR if you prefer
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False  # So it does not duplicate in root logger

    # (optional) also add a StreamHandler to console if you want
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    print(f"[SIRAH-TOOLS-GUI][Analysis] Logging to {log_path}", flush=True)
    return logger


def get_last_n_lines(text: str, n: int = 10) -> str:
    """
    Return the last n lines of a given multiline string.

    Args:
        text (str): The complete text.
        n (int): Number of lines to return.

    Returns:
        str: The last n lines of the provided text.
    """
    lines = text.strip().split('\n')
    return '\n'.join(lines[-n:])


def create_analysis_tab(tab: ttk.Frame, state, style) -> callable:
    """
    Create the 'Analysis' tab of the GUI, including scrollable frames, basic and advanced analysis sections,
    parameters section, actions, and output display. Also sets up placeholders, bindings, and default states.

    Args:
        tab (ttk.Frame): The parent frame that holds this tab.
        state: The state object holding references to variables and widgets shared among tabs.
        style: The ttkbootstrap style object for theming and styling.

    Returns:
        callable: A function that can reset this tab to its initial state.
    """
    # Main frame inside the tab
    main_frame = ttk.Frame(tab)
    main_frame.pack(fill='both', expand=True)

    # Canvas and scrollbar to allow scrolling within the tab
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    def on_frame_configure(event):
        """
        Update the scroll region of the canvas whenever the size of the scrollable frame changes.

        Args:
            event: The Tkinter event that triggered this function.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_frame_configure)

    # Add the scrollable frame to the canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ------------------- BASIC ANALYSIS SECTION -------------------
    basic_analysis_frame = ttk.Labelframe(scrollable_frame, text="Basic Analysis", padding=10)
    basic_analysis_frame.pack(fill="x", padx=10, pady=5)
    basic_analysis_frame.columnconfigure((0, 1, 2), weight=1)

    # Atom Selection 1 label and entry
    ttk.Label(basic_analysis_frame, text="Selection:").grid(row=0, column=0, sticky="w", padx=5)
    state.atom_selection1 = ttk.Entry(basic_analysis_frame)
    # Add placeholder to the atom_selection1 entry
    add_placeholder(state.atom_selection1, "Use VMD syntax: name GC, sirah_protein, name CA, protein", style, state)
    state.atom_selection1.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

    # Basic analysis checkbuttons (RMSD, RMSF, Rgyr)
    state.rmsd_var = tk.IntVar()
    state.rmsf_var = tk.IntVar()
    state.rgyr_var = tk.IntVar()

    basic_analysis_options = [
        ("RMSD", state.rmsd_var, "rmsd_checkbutton"),
        ("RMSF", state.rmsf_var, "rmsf_checkbutton"),
        ("Radius of Gyration", state.rgyr_var, "rgyr_checkbutton")
    ]

    for idx, (text, var, attr_name) in enumerate(basic_analysis_options):
        checkbutton = ttk.Checkbutton(
            basic_analysis_frame, text=text, variable=var, bootstyle="success",
            command=lambda: update_analyze_button(state)
        )
        checkbutton.grid(row=1, column=idx, padx=5, pady=5, sticky="w")
        setattr(state, attr_name, checkbutton)

    # ------------------- ADVANCED ANALYSIS SECTION -------------------
    advanced_analysis_frame = ttk.Labelframe(scrollable_frame, text="Advanced Analysis", padding=10)
    advanced_analysis_frame.pack(fill="x", padx=10, pady=5)
    advanced_analysis_frame.columnconfigure((0, 1, 2, 3), weight=1)

    # Atom Selection 2
    ttk.Label(advanced_analysis_frame, text="Selection 2:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    entry2 = ttk.Entry(advanced_analysis_frame)
    add_placeholder(entry2, "Use VMD syntax: name GC, name CA", style, state)
    entry2.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    setattr(state, 'atom_selection2', entry2)

    # Atom Selection 3
    ttk.Label(advanced_analysis_frame, text="Selection 3:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
    entry3 = ttk.Entry(advanced_analysis_frame)
    add_placeholder(entry3, "Use VMD syntax: name GC, name CA", style, state)
    entry3.grid(row=0, column=3, sticky="ew", padx=5, pady=2)
    setattr(state, 'atom_selection3', entry3)

    # Advanced analysis checkbuttons (SASA, Distance, RDF)
    state.sasa_var = tk.IntVar()
    state.nativec_var = tk.IntVar()
    state.rdf_var = tk.IntVar()
    state.contact_surface_var = tk.IntVar()

    advanced_analysis_options = [
        ("SASA", state.sasa_var, "sasa_checkbutton"),
        ("Distance", state.nativec_var, "nativec_checkbutton"),
        ("RDF", state.rdf_var, "rdf_checkbutton"),
        ("Contact surface", state.contact_surface_var, "contact_surface_checkbuttom")
    ]

    def update_sasa_contact_surface():
        """Make SASA and Contact surface mutually exclusive."""
        if state.sasa_var.get():
            state.contact_surface_var.set(0)
            state.sasa_checkbutton.config(state="normal")
            state.contact_surface_checkbuttom.config(state="disabled")
            state.sasa_rp_entry.config(state="normal")
        elif state.contact_surface_var.get():
            state.sasa_var.set(0)
            state.sasa_checkbutton.config(state="disabled")
            state.contact_surface_checkbuttom.config(state="normal")
            state.sasa_rp_entry.config(state="normal")
        else:
            state.sasa_checkbutton.config(state="normal")
            state.contact_surface_checkbuttom.config(state="normal")
            state.sasa_rp_entry.config(state="normal")
        update_analyze_button(state)


    for idx, (text, var, attr_name) in enumerate(advanced_analysis_options):
        checkbutton = ttk.Checkbutton(
            advanced_analysis_frame, text=text, variable=var, bootstyle="danger",
            command=update_sasa_contact_surface if text in ("SASA", "Contact surface") else lambda: update_analyze_button(state)
        )
        checkbutton.grid(row=1, column=idx, padx=5, pady=5, sticky="w")
        setattr(state, attr_name, checkbutton)


    # ------------------- GENERATE REPORT SECTION -------------------
    pdf_frame = ttk.Labelframe(scrollable_frame, text="Generate Report", padding=10)
    pdf_frame.pack(fill="x", padx=10, pady=5)

    # Configure columns for spacing
    pdf_frame.columnconfigure(0, weight=0)
    pdf_frame.columnconfigure(1, weight=0)
    pdf_frame.columnconfigure(2, weight=0)

    # Generate PDF Report checkbutton
    state.report_var = tk.IntVar()
    report_check = ttk.Checkbutton(
        pdf_frame,
        text="Generate PDF report",
        variable=state.report_var,
        bootstyle="info"
    )
    # Place the report checkbutton at column 0
    report_check.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # New checkbutton "rmsf2pdbeta" to the right of Generate PDF report with a bigger separation
    state.rmsf2pdbeta_var = tk.IntVar()
    rmsf2pdbeta_check = ttk.Checkbutton(
        pdf_frame,
        text="rmsf into pdb bfactor",
        variable=state.rmsf2pdbeta_var,
        bootstyle="info"
    )
    # Place rmsf2pdbeta_check further to the right (e.g., column=2) to provide more separation
    rmsf2pdbeta_check.grid(row=0, column=2, sticky="w", padx=20, pady=5)

    # ------------------- PARAMETERS SECTION -------------------
    parameters_frame = ttk.Labelframe(scrollable_frame, text="Parameters", padding=10)
    parameters_frame.pack(fill="x", padx=10, pady=5)
    parameters_frame.columnconfigure((1, 3, 5), weight=1)

    # Time Step
    ttk.Label(parameters_frame, text="Time Step:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    state.time_step_entry = ttk.Entry(parameters_frame, textvariable=state.time_step)
    state.time_step_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    state.time_step_entry.bind("<KeyRelease>", lambda event: update_analyze_button(state))

    # Steps Between Frames
    ttk.Label(parameters_frame, text="Steps Between Frames:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
    state.steps_between_frames_entry = ttk.Entry(parameters_frame, textvariable=state.steps_between_frames)
    state.steps_between_frames_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=2)
    state.steps_between_frames_entry.bind("<KeyRelease>", lambda event: update_analyze_button(state))

    # Reference File
    ttk.Label(parameters_frame, text="Reference File:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    ref_file_text = os.path.basename(state.reference_file) if state.reference_file else "N/A"
    state.reference_file_label = ttk.Label(parameters_frame, text=ref_file_text)
    state.reference_file_label.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=2)

    # Skip
    ttk.Label(parameters_frame, text="Skip:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    state.skip_entry = ttk.Entry(parameters_frame)
    state.skip_entry.insert(0, "1")  # Default value of skip is 1
    state.skip_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
    state.skip_entry.bind("<KeyRelease>", lambda event: update_analyze_button(state))

    # Solvent Radius (SRAD) for SASA
    ttk.Label(parameters_frame, text="Solvent Radius (SRAD):").grid(row=1, column=2, sticky="w", padx=5, pady=2)
    state.sasa_rp_entry = ttk.Entry(parameters_frame, width=10)
    state.sasa_rp_entry.grid(row=1, column=3, sticky="w", padx=5, pady=2)
    state.sasa_rp_entry.insert(0, "2.1")  # Default value
    state.sasa_rp_entry.config(state="disabled")  # Disabled by default until SASA is selected

    def toggle_sasa_rp_entry(state):
        """
        Enable or disable the SASA solvent radius entry depending on whether SASA is selected.

        Args:
            state: The state object containing variables and widgets.
        """
        if state.sasa_var.get():
            state.sasa_rp_entry.config(state="normal")
        else:
            state.sasa_rp_entry.delete(0, tk.END)
            state.sasa_rp_entry.insert(0, "2.1")
            state.sasa_rp_entry.config(state="disabled")

    state.sasa_var.trace_add("write", lambda *args: toggle_sasa_rp_entry(state))

    # ------------------- ACTION BUTTONS SECTION -------------------
    action_buttons_frame = ttk.Frame(scrollable_frame)
    action_buttons_frame.pack(fill="x", padx=10, pady=10)

    # Analyze Button (starts analysis)
    state.analyze_button = ttk.Button(
        action_buttons_frame,
        text="Analyze",
        command=lambda: run_analysis(state),
        bootstyle="success",
        state="disabled"  # Disabled by default, enabled when conditions are met
    )
    state.analyze_button.pack(side="left", expand=True, fill="x", padx=5, pady=5)

    # Stop Button (stops analysis)
    state.stop_button = ttk.Button(
        action_buttons_frame,
        text="Stop",
        command=lambda: stop_analysis(state),
        bootstyle="danger",
        state="disabled"  # Disabled by default, enabled during analysis
    )
    state.stop_button.pack(side="left", expand=True, fill="x", padx=5, pady=5)

    # Update entry text color based on theme
    update_entry_text_color(state, style.theme_use())

    # ------------------- VMD OUTPUT DISPLAY -------------------
    output_label = ttk.Label(scrollable_frame, text="VMD Output:")
    output_label.pack(anchor="w", padx=10, pady=(10, 0))

    # ScrolledText widget to display output from VMD
    state.analysis_output_text = scrolledtext.ScrolledText(
        scrollable_frame, wrap=tk.WORD, height=10, state='disabled'
    )
    state.analysis_output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def reset_tab():
        """
        Resets the analysis tab to its initial state. Clears entries, unchecks checkbuttons,
        disables certain fields, and clears the output text.
        """
        try:
            # Reset selections and placeholders
            for i in range(1, 4):
                entry = getattr(state, f'atom_selection{i}', None)
                if entry:
                    entry.delete(0, tk.END)
                    if i == 1:
                        placeholder_text = "Use VMD syntax: name GC, sirah_protein, name CA, protein"
                    else:
                        placeholder_text = "Use VMD syntax: name GC, name CA"
                    add_placeholder(entry, placeholder_text, style, state)
                    entry.config(foreground="grey")
                    entry.placeholder_active = True

            # Reset all checkbuttons
            state.rmsd_var.set(0)
            state.rmsf_var.set(0)
            state.rgyr_var.set(0)
            state.sasa_var.set(0)
            state.nativec_var.set(0)
            state.rdf_var.set(0)
            state.contact_surface_var(0)
            state.report_var.set(0)
            state.rmsf2pdbeta_var.set(0)

            # Reset reference file label
            ref_file_text = os.path.basename(state.reference_file) if state.reference_file else "N/A"
            state.reference_file_label.config(text=ref_file_text)

            # Reset skip value
            state.skip_entry.delete(0, tk.END)
            state.skip_entry.insert(0, "1")

            # Disable Analyze and Stop buttons
            state.analyze_button.config(state="disabled")
            state.stop_button.config(state="disabled")

            # Clear the output text area
            state.analysis_output_text.config(state='normal')
            state.analysis_output_text.delete(1.0, tk.END)
            state.analysis_output_text.config(state='disabled')

            # Update the entry text color based on the current theme
            update_entry_text_color(state, style.theme_use())

            logger.info("Analysis tab has been reset successfully.")
        except Exception as e:
            logger.exception("Failed to reset the analysis tab.")
            messagebox.showerror("Error", f"Failed to reset the analysis tab:\n{str(e)}")

    return reset_tab


def add_placeholder(entry: ttk.Entry, placeholder: str, style, state) -> None:
    """
    Add placeholder text to an Entry widget and configure event bindings to clear/restore it.

    Args:
        entry (ttk.Entry): The Entry widget to which the placeholder is added.
        placeholder (str): The placeholder text to show when the entry is empty.
        style: The ttkbootstrap style object.
        state: The state object with shared variables and widgets.
    """
    entry.insert(0, placeholder)
    entry.config(foreground="grey")
    entry.placeholder = placeholder
    entry.placeholder_active = True
    entry.bind("<FocusIn>", lambda event: clear_placeholder(event, style, state))
    entry.bind("<FocusOut>", lambda event: restore_placeholder(event, style, state))
    entry.bind("<KeyRelease>", lambda event: update_analyze_button(state))


def clear_placeholder(event, style, state) -> None:
    """
    Clear the placeholder text when the Entry widget gains focus.

    Args:
        event: The focus-in event object.
        style: The ttkbootstrap style object.
        state: The state object with shared variables and widgets.
    """
    widget = event.widget
    if widget.placeholder_active:
        widget.delete(0, tk.END)
        current_theme = style.theme_use()
        text_color = "black" if current_theme in ["litera", "journal"] else "white"
        widget.config(foreground=text_color)
        widget.placeholder_active = False
        update_analyze_button(state)


def restore_placeholder(event, style, state) -> None:
    """
    Restore the placeholder text if the Entry widget loses focus while empty.

    Args:
        event: The focus-out event object.
        style: The ttkbootstrap style object.
        state: The state object with shared variables and widgets.
    """
    widget = event.widget
    if not widget.get():
        widget.insert(0, widget.placeholder)
        widget.config(foreground="grey")
        widget.placeholder_active = True
        update_analyze_button(state)


def update_entry_text_color(state, theme_name: str) -> None:
    """
    Update text color of Entry fields depending on the theme.
    If placeholder is active, it remains grey, otherwise it switches to black or white.

    Args:
        state: The state object with shared variables and widgets.
        theme_name (str): The name of the current ttkbootstrap theme.
    """
    text_color = "black" if theme_name in ["litera", "journal"] else "white"
    for i in range(1, 4):
        entry = getattr(state, f'atom_selection{i}', None)
        if entry:
            if not entry.placeholder_active:
                entry.config(foreground=text_color)
            else:
                entry.config(foreground="grey")


def update_analyze_button(state) -> None:
    """
    Enable or disable the 'Analyze' button based on the conditions:
    - At least one analysis option (basic or advanced) is selected.
    - At least one of the selection entries is filled (not placeholder).

    Args:
        state: The state object with shared variables and widgets.
    """
    analyses_selected = any([
        state.rmsd_var.get(),
        state.rmsf_var.get(),
        state.rgyr_var.get(),
        state.sasa_var.get(),
        state.nativec_var.get(),
        state.rdf_var.get(),
        state.contact_surface_var.get()
    ])

    selections_filled = any([
        not state.atom_selection1.placeholder_active and state.atom_selection1.get().strip(),
        not state.atom_selection2.placeholder_active and state.atom_selection2.get().strip(),
        not state.atom_selection3.placeholder_active and state.atom_selection3.get().strip()
    ])

    if analyses_selected and selections_filled:
        state.analyze_button.config(state="normal")
    else:
        state.analyze_button.config(state="disabled")


def show_progress_window(root) -> tk.Toplevel:
    """
    Show a small progress window indicating that the analysis is running.

    Args:
        root: The main Tk root window.

    Returns:
        tk.Toplevel: The progress window that displays a label and a progress bar.
    """
    progress_win = tk.Toplevel(root)
    progress_win.title("Progress")
    progress_win.geometry("300x100")
    progress_win.resizable(False, False)
    ttk.Label(progress_win, text="Calculating...").pack(pady=10)
    progress_bar = ttk.Progressbar(progress_win, mode="indeterminate")
    progress_bar.pack(fill="x", padx=20, pady=10)
    progress_bar.start()
    return progress_win


def run_analysis(state) -> None:
    """
    Initiate the analysis in a separate thread. Show a progress window and disable the 'Analyze' button.
    Enable the 'Stop' button during analysis.

    Args:
        state: The state object with shared variables and widgets.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Running analysis...")

    # Disable Analyze, enable Stop
    state.analyze_button.config(state='disabled')
    state.stop_button.config(state='normal')

    # Show progress window
    progress_window = show_progress_window(state.root)
    state.progress_window = progress_window

    # Clear previous output
    state.analysis_output_text.config(state='normal')
    state.analysis_output_text.delete(1.0, tk.END)
    state.analysis_output_text.config(state='disabled')

    # Flag to allow stopping analysis
    state.stop_analysis = False

    def analysis_thread():
        """
        Run the analysis logic in a separate thread to avoid blocking the GUI.
        """
        try:
            analyze(state)
        except Exception as e:
            logger.exception("An error occurred during analysis")
            state.root.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

    threading.Thread(target=analysis_thread, daemon=True).start()


def stop_analysis(state):
    """
    Stop the ongoing VMD process if the user requests it. Restore buttons and close progress window.

    Args:
        state: The state object with shared variables and widgets.
    """
    if hasattr(state, 'vmd_process') and state.vmd_process:
        state.vmd_process.terminate()
        logger = get_analysis_logger(state.working_directory)
        logger.info("VMD process terminated by the user.")
        insert_vmd_output(state, "\nProcess terminated by the user.\n")
    state.stop_analysis = True

    # Restore button states
    state.analyze_button.config(state='normal')
    state.stop_button.config(state='disabled')

    # Close progress window if it exists
    if hasattr(state, 'progress_window') and state.progress_window:
        state.progress_window.destroy()


def analyze(state) -> None:
    """
    Execute the analysis based on user selections. Validate inputs, build and run the VMD command,
    and handle file overwrites. After successful run, triggers post-processing.

    Args:
        state: The state object with shared variables and widgets.
    """

    logger = get_analysis_logger(state.working_directory)
    logger.info("Starting analysis...")
    # Check if working directory is set
    if not getattr(state, 'working_directory', None):
        state.root.after(0, lambda: messagebox.showerror("Error", "Please set a working directory before proceeding."))
        logger.error("Working directory not set.")
        return

    # Ensure 'Analysis' directory exists
    analysis_dir = os.path.join(state.working_directory, "Analysis")
    if not os.path.exists(analysis_dir):
        try:
            os.makedirs(analysis_dir)
            logger.info(f"Analysis directory created at {analysis_dir}")
        except Exception as e:
            state.root.after(0, lambda: messagebox.showerror("Error", f"Failed to create analysis directory: {e}"))
            logger.exception(f"Failed to create analysis directory at {analysis_dir}.")
            return

    # Extract selections
    selection1 = state.atom_selection1.get().strip()
    selection2_entry = getattr(state, 'atom_selection2', None)
    selection3_entry = getattr(state, 'atom_selection3', None)
    selection2 = selection2_entry.get().strip() if selection2_entry else ""
    selection3 = selection3_entry.get().strip() if selection3_entry else ""

    # Check if placeholders are active
    if state.atom_selection1.placeholder_active:
        selection1 = ""
    if selection2_entry and selection2_entry.placeholder_active:
        selection2 = ""
    if selection3_entry and selection3_entry.placeholder_active:
        selection3 = ""

    # Get parameters
    try:
        time_step_value = float(state.time_step.get())
    except ValueError:
        state.root.after(0, lambda: messagebox.showerror("Error", "Invalid value for 'Time Step'."))
        return

    try:
        steps_between_frames_value = float(state.steps_between_frames.get())
    except ValueError:
        state.root.after(0, lambda: messagebox.showerror("Error", "Invalid value for 'Steps Between Frames'."))
        return

    reference_file_value = state.reference_file if getattr(state, 'reference_file', None) else "None"
    skip_value = state.skip_entry.get() if hasattr(state, 'skip_entry') else "1"

    ref_file_text = os.path.basename(reference_file_value) if reference_file_value != "None" else "N/A"
    state.root.after(0, lambda: state.reference_file_label.config(text=ref_file_text))

    # Determine if basic or advanced analyses are selected
    basic_analysis_selected = state.rmsd_var.get() or state.rmsf_var.get() or state.rgyr_var.get()
    advanced_analysis_selected = state.sasa_var.get() or state.nativec_var.get() or state.rdf_var.get() or state.contact_surface_var.get()

    # Validate selections based on chosen analyses
    if basic_analysis_selected and not advanced_analysis_selected:
        # Only basic analyses
        if not selection1:
            state.root.after(0, lambda: messagebox.showerror("Error",
                                                             "Please enter a valid atom selection for Basic Analysis."))
            logger.error("Invalid selection for Basic Analysis.")
            return
        selection2 = selection1
        selection3 = selection1

    elif advanced_analysis_selected and not basic_analysis_selected:
        # Only advanced analyses
        if not selection2:
            state.root.after(0, lambda: messagebox.showerror("Error",
                                                             "Please enter a valid atom selection for Advanced Analysis (Selection 2)."))
            logger.error("Invalid Selection 2 for Advanced Analysis.")
            return
        selection1 = selection2
        if not selection3:
            selection3 = selection2
            logger.info("Selection 3 is empty; using Selection 2 as Selection 3.")

    elif basic_analysis_selected and advanced_analysis_selected:
        # Both basic and advanced analyses
        if not selection1:
            state.root.after(0, lambda: messagebox.showerror("Error",
                                                             "Please enter a valid atom selection for Basic Analysis (Selection 1)."))
            logger.error("Invalid selection for Basic Analysis.")
            return
        if not selection2:
            state.root.after(0, lambda: messagebox.showerror("Error",
                                                             "Please enter a valid atom selection for Advanced Analysis (Selection 2)."))
            logger.error("Invalid Selection 2 for Advanced Analysis.")
            return
        if not selection3:
            selection3 = selection2
            logger.info("Selection 3 is empty; using Selection 2 as Selection 3.")

    else:
        # No analyses selected
        state.root.after(0, lambda: messagebox.showwarning("Warning",
                                                           "No analyses selected. Please select at least one analysis option."))
        logger.warning("No analysis options selected.")
        return

    # Check if topology and trajectory files are loaded
    if not getattr(state, 'topology_file', None) or not getattr(state, 'trajectory_file', None):
        state.root.after(0, lambda: messagebox.showerror("Error",
                                                         "Please load both topology and trajectory files before analysis."))
        logger.error("Topology or trajectory files not loaded.")
        return

    # Clean up selection strings for filenames
    selection1_clean = selection1.replace(" ", "_")
    selection2_clean = selection2.replace(" ", "_")
    selection3_clean = selection3.replace(" ", "_")

    # Determine analysis code
    analysis_code = 0
    if state.rmsd_var.get():
        analysis_code += 1
    if state.rmsf_var.get():
        analysis_code += 2
    if state.rgyr_var.get():
        analysis_code += 4
    if state.sasa_var.get():
        analysis_code += 8
    if state.nativec_var.get():
        analysis_code += 16
    if state.rdf_var.get():
        analysis_code += 32
    if state.contact_surface_var.get():
        analysis_code += 64

    logger.info(f"Analysis code: {analysis_code}")

    # ------------------- Checking for existing files (Overwrite Prompt) -------------------
    expected_files = []

    if state.rmsd_var.get():
        expected_files.append(os.path.join(analysis_dir, f"RMSD_{selection1_clean}.dat"))
        expected_files.append(os.path.join(analysis_dir, f"RMSD_{selection1_clean}.png"))

    if state.rmsf_var.get():
        expected_files.append(os.path.join(analysis_dir, f"RMSF_{selection1_clean}.dat"))
        expected_files.append(os.path.join(analysis_dir, f"RMSF_{selection1_clean}.png"))

    if state.rgyr_var.get():
        expected_files.append(os.path.join(analysis_dir, f"RGYR_{selection1_clean}.dat"))
        expected_files.append(os.path.join(analysis_dir, f"RGYR_{selection1_clean}.png"))

    if state.sasa_var.get():
        expected_files.append(os.path.join(analysis_dir, f"SASA_{selection2_clean}_{selection3_clean}.dat"))
        expected_files.append(os.path.join(analysis_dir, f"SASA_{selection2_clean}_{selection3_clean}.png"))

    if state.nativec_var.get():
        expected_files.append(os.path.join(analysis_dir, f"distance_{selection2_clean}_{selection3_clean}.dat"))
        expected_files.append(os.path.join(analysis_dir, f"Distance_{selection2_clean}_{selection3_clean}.png"))

    if state.rdf_var.get():
        expected_files.append(os.path.join(analysis_dir, f"rdf_{selection2_clean}_{selection3_clean}.dat"))
        expected_files.append(os.path.join(analysis_dir, f"rdf_{selection2_clean}_{selection3_clean}_g.png"))
        expected_files.append(os.path.join(analysis_dir, f"rdf_{selection2_clean}_{selection3_clean}_integral.png"))

    if state.report_var.get():
        expected_files.append(os.path.join(analysis_dir, f"Analysis_{selection1_clean}.pdf"))

    if state.rmsf2pdbeta_var.get():
        expected_files.append(os.path.join(analysis_dir, f"RMSF_protein.pdb"))

    existing_files = [f for f in expected_files if os.path.exists(f)]

    if existing_files:
        message = "The following files already exist:\n"
        message += "\n".join([os.path.basename(f) for f in existing_files])
        message += "\nDo you want to overwrite them?"

        overwrite_decision = {"value": None}
        decision_event = threading.Event()

        # *** ATENCIÓN: esta función va DENTRO del if, así accede a message ***
        def ask_overwrite():
            overwrite_decision["value"] = messagebox.askyesno("Overwrite Files?", message)
            decision_event.set()

        state.root.after(0, ask_overwrite)
        decision_event.wait()  # Espera hasta que el usuario responda

        if not overwrite_decision["value"]:
            logger.info("User chose not to overwrite existing files. Analysis canceled.")
            state.root.after(0, lambda: state.analyze_button.config(state='normal'))
            state.root.after(0, lambda: state.stop_button.config(state='disabled'))
            if hasattr(state, 'progress_window') and state.progress_window:
                state.root.after(0, state.progress_window.destroy)
            return

    # ------------------- Running VMD -------------------
    try:
        script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "TCL")
        tcl_script_path = os.path.join(script_dir, "sirah_analysis.tcl")

        if not os.path.exists(tcl_script_path):
            state.root.after(0, lambda: messagebox.showerror("Error", f"TCL script not found at {tcl_script_path}."))
            logger.error(f"TCL script not found at {tcl_script_path}.")
            return

        # Add the rmsf2pdbeta_var value as the last argument
        command = [
            "vmd", "-dispdev", "text", "-e", tcl_script_path,
            "-args", state.topology_file, state.trajectory_file,
            selection1, selection2, selection3, str(analysis_code),
            script_dir, analysis_dir, reference_file_value, skip_value, state.sasa_rp_entry.get(),
            str(state.rmsf2pdbeta_var.get())  # New argument
        ]

        # Ensure all command elements are strings
        command = [str(item) if item is not None else "None" for item in command]

        logger.info(f"Executing command: {' '.join(command)}")

        state.vmd_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        def read_output(process, state, selection2_clean, selection3_clean):
            """
            Read the VMD process output (stdout and stderr) asynchronously and update the GUI.
            Once the process finishes, handle post-processing if it ended successfully.

            Args:
                process: The subprocess.Popen object running the VMD command.
                state: The state object with shared variables and widgets.
                selection2_clean (str): Cleaned selection 2 (no spaces).
                selection3_clean (str): Cleaned selection 3 (no spaces).
            """
            logger = get_analysis_logger(state.working_directory)
            logger.info("Reading VMD Output")
            try:
                for line in process.stdout:
                    insert_vmd_output(state, line)
                for line in process.stderr:
                    insert_vmd_output(state, line)
                process.stdout.close()
                process.stderr.close()
                process.wait()

                if process.returncode != 0 and not state.stop_analysis:
                    logger.error(f"VMD exited with return code {process.returncode}")
                    state.root.after(0, lambda: messagebox.showerror("Error",
                                                                     f"VMD exited with return code {process.returncode}."))
                    return

                # Only run post-processing if user didn't stop the analysis
                if not state.stop_analysis:
                    post_process_analysis(state, selection1_clean, selection2_clean, selection3_clean, analysis_dir)
                    insert_vmd_output(state, "\nAnalysis completed.\n")

                # Restore buttons
                state.root.after(0, lambda: state.analyze_button.config(state='normal'))
                state.root.after(0, lambda: state.stop_button.config(state='disabled'))

            except Exception as e:
                logger.exception("An error occurred while reading output.")
                state.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{str(e)}"))
            finally:
                # Ensure the progress window is closed
                if hasattr(state, 'progress_window') and state.progress_window:
                    state.root.after(0, state.progress_window.destroy)

        threading.Thread(target=read_output, args=(state.vmd_process, state, selection2_clean, selection3_clean), daemon=True).start()

    except Exception as e:
        logger.exception("An unexpected error occurred.")
        state.root.after(0, lambda: messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}"))
        if hasattr(state, 'progress_window') and state.progress_window:
            state.progress_window.destroy()
        return


def post_process_analysis(state, selection1_clean: str, selection2_clean: str, selection3_clean: str, analysis_dir: str) -> None:
    """
    Post-processing after the VMD script finishes:
    - Generate plots from data files
    - Mark analyses as completed
    - Generate PDF report if requested

    Args:
        state: The state object with shared variables and widgets.
        selection1_clean (str): Cleaned selection 1.
        selection2_clean (str): Cleaned selection 2.
        selection3_clean (str): Cleaned selection 3.
        analysis_dir (str): Path to the analysis directory.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Running post-process analysis (ploting and generate PDF)...")
    try:
        # RMSD Plot
        if state.rmsd_var.get():
            plot_generic(state, f"RMSD_{selection1_clean}.dat", "Time (µs)", "RMSD (Å)",
                         f"RMSD per Frame - {selection1_clean}",
                         f"RMSD_{selection1_clean}", analysis_dir)
            mark_analysis_completed(state.rmsd_checkbutton, state.rmsd_var, state)

        # RMSF Plot
        if state.rmsf_var.get():
            plot_rmsf(state, f"RMSF_{selection1_clean}.dat", "Residue", "RMSF (Å)",
                      f"RMSF per Residue - {selection1_clean}",
                      f"RMSF_{selection1_clean}", analysis_dir)
            mark_analysis_completed(state.rmsf_checkbutton, state.rmsf_var, state)

        # Radius of Gyration Plot
        if state.rgyr_var.get():
            plot_generic(state, f"RGYR_{selection1_clean}.dat", "Time (µs)", "Radius of Gyration (Å)",
                         f"Radius of Gyration per Frame - {selection1_clean}",
                         f"RGYR_{selection1_clean}", analysis_dir)
            mark_analysis_completed(state.rgyr_checkbutton, state.rgyr_var, state)

        # SASA Plot
        if state.sasa_var.get():
            plot_generic(state, f"SASA_{selection2_clean}_{selection3_clean}.dat", "Time (µs)", "SASA (Å²)",
                         f"SASA per Frame - {selection2_clean} & {selection3_clean}",
                         f"SASA_{selection2_clean}_{selection3_clean}", analysis_dir)
            mark_analysis_completed(state.sasa_checkbutton, state.sasa_var, state)

        # Contact Surface Plot
        if state.contact_surface_var.get():
            plot_generic(
                state,
                f"contact_surface_{selection2_clean}_{selection3_clean}.dat",
                "Time (µs)",
                "Contact surface area (Å²)",
                f"Contact Surface per Frame - {selection2_clean} & {selection3_clean}",
                f"ContactSurface_{selection2_clean}_{selection3_clean}",
                analysis_dir
            )
            mark_analysis_completed(state.contact_surface_checkbuttom, state.contact_surface_var, state)

        # Distance Plot
        if state.nativec_var.get():
            plot_generic(state, f"distance_{selection2_clean}_{selection3_clean}.dat", "Time (µs)", "Distance (Å)",
                         f"Distance between {selection2_clean} & {selection3_clean}",
                         f"Distance_{selection2_clean}_{selection3_clean}", analysis_dir)
            mark_analysis_completed(state.nativec_checkbutton, state.nativec_var, state)

        # RDF Plot
        if state.rdf_var.get():
            title_g = f"RDF Analysis - g(r) for {selection2_clean} & {selection3_clean}"
            title_integral = f"RDF Analysis - Integral for {selection2_clean} & {selection3_clean}"
            plot_rdf(state, f"rdf_{selection2_clean}_{selection3_clean}.dat",
                     f"rdf_{selection2_clean}_{selection3_clean}", analysis_dir,
                     title_g, title_integral)
            mark_analysis_completed(state.rdf_checkbutton, state.rdf_var, state)

        # Generate PDF if requested
        if state.report_var.get():
            pdf_filename = os.path.join(analysis_dir, f"Analysis_{selection1_clean}.pdf")
            generate_pdf(state, pdf_filename, selection1_clean, selection2_clean, selection3_clean)
            state.root.after(0, lambda: messagebox.showinfo("Success", f"Analysis report saved as {pdf_filename}."))
            logger.info(f"PDF report saved as {pdf_filename}.")

    except Exception as e:
        logger.exception("Post-processing of analysis failed.")
        state.root.after(0, lambda err=e: messagebox.showerror("Error", f"Post-processing of analysis failed:\n{str(err)}"))



def insert_vmd_output(state, output: str) -> None:
    """
    Insert lines of VMD output into the ScrolledText widget in a thread-safe manner
    AND print them to the terminal (stdout) in real time.
    """
    def insert_text():
        state.analysis_output_text.config(state='normal')
        state.analysis_output_text.insert(tk.END, output)
        state.analysis_output_text.config(state='disabled')
        state.analysis_output_text.see(tk.END)  # Scroll to the end

        # Print also to the terminal/console
        print(output, end='', flush=True)

    state.root.after(0, insert_text)


def mark_analysis_completed(checkbutton: ttk.Checkbutton, var: tk.IntVar, state) -> None:
    """
    Mark an analysis as completed by setting the associated checkbutton to a success style and checking it.

    Args:
        checkbutton (ttk.Checkbutton): The Checkbutton widget for the analysis.
        var (tk.IntVar): The variable associated with the analysis option.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Mark analysis as completed...")
    checkbutton.config(bootstyle="success")
    var.set(1)
    logger.info(f"Analysis {checkbutton.cget('text')} completed.")


def plot_generic(state, data_file: str, x_label: str, y_label: str, title: str, output_file_prefix: str, analysis_dir: str) -> str:
    """
    Generate a generic line plot from a data file containing two columns: frame and value.
    Converts frames to time using the time step and steps between frames, then saves the plot as PNG.

    Args:
        state: The state object with shared variables and widgets.
        data_file (str): The name of the data file to read.
        x_label (str): The X-axis label.
        y_label (str): The Y-axis label.
        title (str): The title of the plot.
        output_file_prefix (str): The prefix for the output PNG file.
        analysis_dir (str): The directory where output files are saved.

    Returns:
        str: The path to the generated plot file.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Ploting...")
    try:
        # Retrieve time-related parameters
        try:
            time_step_value = float(state.time_step.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid value for 'Time Step'.")
            return

        try:
            steps_between_frames_value = float(state.steps_between_frames.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid value for 'Steps Between Frames'.")
            return

        try:
            skip_value = float(state.skip_entry.get()) if hasattr(state, 'skip_entry') else 1
        except ValueError:
            messagebox.showerror("Error", "Invalid value for 'Skip'.")
            return

        # Convert frames to time in microseconds
        frames_to_time = steps_between_frames_value * time_step_value * 1e-9 * skip_value

        data_file_path = os.path.join(analysis_dir, data_file)
        if not os.path.exists(data_file_path):
            logger.error(f"Data file {data_file_path} not found.")
            state.root.after(0, lambda: messagebox.showerror("Error", f"Data file {data_file} not found."))
            return

        # Read data
        data = pd.read_csv(data_file_path, delim_whitespace=True, header=None)
        x_data = data.iloc[:, 0] * frames_to_time
        y_data = data.iloc[:, 1]

        # Create plot
        plt.figure(figsize=(10, 8))
        plt.plot(x_data, y_data, color="#018571")
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.grid(False)
        plt.tight_layout()

        plot_filename = os.path.join(analysis_dir, f"{output_file_prefix}.png")
        plt.savefig(plot_filename, format="png", dpi=300)
        plt.close()
        logger.info(f"Generated plot {plot_filename}")
        return plot_filename
    except Exception as e:
        logger.exception(f"Failed to generate plot {title}.")
        state.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate plot {title}:\n{str(e)}"))


def plot_rmsf(state, data_file: str, x_label: str, y_label: str, title: str, output_file_prefix: str, analysis_dir: str) -> str:
    """
    Generate an RMSF plot from a data file containing two columns: residue index and RMSF value.

    Args:
        state: The state object with shared variables and widgets.
        data_file (str): Name of the data file.
        x_label (str): Label for the X-axis (Residue).
        y_label (str): Label for the Y-axis (RMSF).
        title (str): Plot title.
        output_file_prefix (str): Prefix for the output PNG file.
        analysis_dir (str): Path to the analysis directory.

    Returns:
        str: The path to the generated plot file.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Ploting RMSF...")
    try:
        data_file_path = os.path.join(analysis_dir, data_file)
        if not os.path.exists(data_file_path):
            logger.error(f"Data file {data_file_path} not found.")
            state.root.after(0, lambda: messagebox.showerror("Error", f"Data file {data_file} not found."))
            return

        data = pd.read_csv(data_file_path, delim_whitespace=True, header=None)
        x_data = data.iloc[:, 0]
        y_data = data.iloc[:, 1]

        plt.figure(figsize=(10, 8))
        plt.plot(x_data, y_data, color="#018571", marker="o", markersize=3)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.grid(False)
        plt.tight_layout()

        plot_filename = os.path.join(analysis_dir, f"{output_file_prefix}.png")
        plt.savefig(plot_filename, format="png", dpi=300)
        plt.close()
        logger.info(f"Generated plot {plot_filename}")
        return plot_filename
    except Exception as e:
        logger.exception(f"Failed to generate plot {title}.")
        state.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate plot {title}:\n{str(e)}"))


def plot_rdf(state, data_file: str, output_file_prefix: str, analysis_dir: str, title_g: str, title_integral: str) -> tuple:
    """
    Generate RDF plots:
    - Plot of r vs g(r)
    - Plot of r vs integral of g(r)

    Args:
        state: The state object with shared variables and widgets.
        data_file (str): The data file containing columns: r, g, integral.
        output_file_prefix (str): Prefix for the output files.
        analysis_dir (str): Path to the analysis directory.
        title_g (str): Title for the g(r) plot.
        title_integral (str): Title for the integral plot.

    Returns:
        tuple: Paths to the g(r) and integral plot files.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Ploting RDF...")
    try:
        data_file_path = os.path.join(analysis_dir, data_file)
        if not os.path.exists(data_file_path):
            logger.error(f"Data file {data_file_path} not found.")
            state.root.after(0, lambda: messagebox.showerror("Error", f"Data file {data_file} not found."))
            return

        data = pd.read_csv(data_file_path, delim_whitespace=True, header=0)

        # g(r) plot
        plt.figure(figsize=(10, 8))
        plt.plot(data['r'], data['g'], color="#018571", label='g(r)')
        plt.xlabel("r (Å)")
        plt.ylabel("g(r)")
        plt.title(title_g)
        plt.grid(False)
        plt.annotate(
            "See documentation for normalization info.",
            xy=(0.95, 0.05), xycoords='axes fraction',
            fontsize=9, color='gray', ha='right', va='bottom'
        )
        plt.tight_layout()

        plot_filename_g = os.path.join(analysis_dir, f"{output_file_prefix}_g.png")
        plt.savefig(plot_filename_g, format="png", dpi=300)
        plt.close()
        logger.info(f"Generated RDF g(r) plot {plot_filename_g}")

        # Integral plot
        plt.figure(figsize=(10, 8))
        plt.plot(data['r'], data['integral'], color="#018571", label='Integral g(r)')
        plt.xlabel("r (Å)")
        plt.ylabel("Integral g(r)")
        plt.title(title_integral)
        plt.grid(False)
        plt.tight_layout()

        plot_filename_integral = os.path.join(analysis_dir, f"{output_file_prefix}_integral.png")
        plt.savefig(plot_filename_integral, format="png", dpi=300)
        plt.close()
        logger.info(f"Generated RDF integral plot {plot_filename_integral}")

        return plot_filename_g, plot_filename_integral
    except Exception as e:
        logger.exception("Failed to generate RDF plot.")
        state.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate RDF plot:\n{str(e)}"))


def generate_pdf(state, pdf_filename: str, selection1: str, selection2: str, selection3: str) -> None:
    """
    Generate a PDF report containing the generated plots. Each selected analysis has a corresponding page.

    Args:
        state: The state object with shared variables and widgets.
        pdf_filename (str): Full path to the PDF file to generate.
        selection1 (str): Selection 1 used in the analysis.
        selection2 (str): Selection 2 used in the analysis.
        selection3 (str): Selection 3 used in the analysis.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Creating PDF...")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    try:
        analysis_dir = os.path.join(state.working_directory, "Analysis")
        selection1_clean = selection1.replace(" ", "_")
        selection2_clean = selection2.replace(" ", "_")
        selection3_clean = selection3.replace(" ", "_")

        # RMSD
        if state.rmsd_var.get():
            rmsd_image = os.path.join(analysis_dir, f"RMSD_{selection1_clean}.png")
            if os.path.exists(rmsd_image):
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "RMSD Analysis", ln=True, align="C")
                pdf.image(rmsd_image, x=10, y=30, w=190)

        # RMSF
        if state.rmsf_var.get():
            rmsf_image = os.path.join(analysis_dir, f"RMSF_{selection1_clean}.png")
            if os.path.exists(rmsf_image):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "RMSF Analysis", ln=True, align="C")
                pdf.image(rmsf_image, x=10, y=30, w=190)

        # Radius of Gyration
        if state.rgyr_var.get():
            rgyr_image = os.path.join(analysis_dir, f"RGYR_{selection1_clean}.png")
            if os.path.exists(rgyr_image):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Radius of Gyration Analysis", ln=True, align="C")
                pdf.image(rgyr_image, x=10, y=30, w=190)

        # SASA
        if state.sasa_var.get():
            sasa_image = os.path.join(analysis_dir, f"SASA_{selection2_clean}_{selection3_clean}.png")
            if os.path.exists(sasa_image):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "SASA Analysis", ln=True, align="C")
                pdf.image(sasa_image, x=10, y=30, w=190)

        # Contact Surface
        if state.contact_surface_var.get():
            surf_image = os.path.join(analysis_dir, f"ContactSurface_{selection2_clean}_{selection3_clean}.png")
            if os.path.exists(surf_image):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Contact Surface Analysis", ln=True, align="C")
                pdf.image(surf_image, x=10, y=30, w=190)


        # Distance
        if state.nativec_var.get():
            contacts_image = os.path.join(analysis_dir, f"Distance_{selection2_clean}_{selection3_clean}.png")
            if os.path.exists(contacts_image):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Distance Analysis", ln=True, align="C")
                pdf.image(contacts_image, x=10, y=30, w=190)

        # RDF
        if state.rdf_var.get():
            rdf_image_g = os.path.join(analysis_dir, f"rdf_{selection2_clean}_{selection3_clean}_g.png")
            rdf_image_integral = os.path.join(analysis_dir, f"rdf_{selection2_clean}_{selection3_clean}_integral.png")
            if os.path.exists(rdf_image_g):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "RDF Analysis - g(r)", ln=True, align="C")
                pdf.image(rdf_image_g, x=10, y=30, w=190)

            if os.path.exists(rdf_image_integral):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "RDF Analysis - Integral", ln=True, align="C")
                pdf.image(rdf_image_integral, x=10, y=30, w=190)

        # Save the PDF
        pdf.output(pdf_filename)
        state.root.after(0,
                         lambda: messagebox.showinfo("Success", f"PDF report generated successfully: {pdf_filename}."))
        logger.info(f"PDF report saved as {pdf_filename}.")

    except Exception as e:
        logger.exception("Failed to generate PDF.")
        state.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}"))


def open_vmd(state) -> None:
    """
    Open VMD with the loaded topology and trajectory files, if they are available.

    Args:
        state: The state object with shared variables and widgets.
    """
    logger = get_analysis_logger(state.working_directory)
    logger.info("Open VMD...")
    if not getattr(state, 'topology_file', None) or not getattr(state, 'trajectory_file', None):
        messagebox.showerror("Error", "Please load both topology and trajectory files before opening VMD.")
        logger.error("Topology or trajectory files not loaded.")
        return

    try:
        subprocess.run(["vmd", state.topology_file, state.trajectory_file], check=True)
        logger.info("VMD opened successfully.")
    except subprocess.CalledProcessError as e:
        last_10_lines = get_last_n_lines(e.stderr, 10) if e.stderr else "No stderr provided."
        messagebox.showerror("Error", f"Failed to open VMD:\n{last_10_lines}")
        logger.exception("Failed to open VMD.")
    except Exception as e:
        logger.exception("Failed to open VMD.")
        messagebox.showerror("Error", f"Failed to open VMD:\n{str(e)}")
