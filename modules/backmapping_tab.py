import ttkbootstrap as ttk
import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import threading
import queue
import shutil

def ensure_amberhome():
    """
    Checks and sets the AMBERHOME environment variable.
    If AMBERHOME is not set, attempts to locate AmberTools by searching for common executables in the system PATH.
    Returns a message indicating the status of AMBERHOME.

    Returns:
        str: A message indicating the status of AMBERHOME.
    """
    amberhome = os.environ.get('AMBERHOME')

    if amberhome:
        message = f"$AMBERHOME is set to: {amberhome}"
    else:
        # Try to find AmberTools executables in PATH
        ambertools_executables = ['cpptraj', 'sander', 'tleap']
        for exe in ambertools_executables:
            exe_path = shutil.which(exe)
            if exe_path:
                amberhome = os.path.abspath(os.path.join(os.path.dirname(exe_path), '..'))
                os.environ['AMBERHOME'] = amberhome
                message = f"$AMBERHOME was not set. It has been set to: {amberhome}"
                break
        else:
            message = (
                "$AMBERHOME is not set. Please ensure that $AMBERHOME is properly configured.\n"
                "Optionally install the conda version of AmberTools (without MPI and CUDA support):\n"
                "conda install -c conda-forge ambertools=23"
            )
    return message

def create_backmapping_tab(tab, state):
    """
    Creates the Backmapping tab with scrollable content, option frames, and action buttons.

    Args:
        tab (ttk.Frame): Parent frame for the Backmapping tab.
        state (State): State object for the backmapping process.
    """
    try:
        amberhome_message = ensure_amberhome()
    except EnvironmentError as e:
        amberhome_message = str(e)
        messagebox.showerror("Error", amberhome_message)
        return

    # Initialize state attributes
    state.backmapping_process = None
    state.backmapping_thread = None
    state.outname = None

    # Create scrollable content using a Canvas and scrollbars
    canvas = tk.Canvas(tab)
    scrollbar_v = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollbar_h = ttk.Scrollbar(tab, orient="horizontal", command=canvas.xview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar_v.pack(side="right", fill="y")
    scrollbar_h.pack(side="bottom", fill="x")

    # Info Frame for AMBERHOME status
    info_frame = ttk.LabelFrame(scrollable_frame, text="Info", padding=(10, 10))
    info_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
    info_label = ttk.Label(info_frame, text=amberhome_message, bootstyle="info")
    info_label.pack(anchor="w", padx=5, pady=5, fill="x")

    # Option selection frame (Basic/Advanced)
    options_frame = ttk.Frame(scrollable_frame)
    options_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
    scrollable_frame.grid_columnconfigure(0, weight=1)

    options_var = tk.StringVar(value="basic")

    basic_radiobutton = ttk.Radiobutton(
        options_frame, text="Basic Options", variable=options_var, value="basic",
        command=lambda: toggle_frame(basic_options_frame, advanced_options_frame, "basic")
    )
    basic_radiobutton.pack(side="left", padx=5)

    advanced_radiobutton = ttk.Radiobutton(
        options_frame, text="Advanced Options", variable=options_var, value="advanced",
        command=lambda: toggle_frame(basic_options_frame, advanced_options_frame, "advanced")
    )
    advanced_radiobutton.pack(side="left", padx=5)

    # Create option frames
    basic_options_frame, basic_entries = create_basic_options(scrollable_frame)
    basic_options_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
    advanced_options_frame, advanced_option_vars = create_advanced_options(scrollable_frame)
    advanced_options_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
    advanced_options_frame.grid_remove()

    # Action buttons (Run, Stop)
    buttons_frame = ttk.Frame(scrollable_frame)
    buttons_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

    run_backmap_button = ttk.Button(
        buttons_frame, text="Run Backmap", bootstyle="success"
    )
    run_backmap_button.pack(side="left", expand=True, fill='x', padx=5, pady=5)

    stop_backmap_button = ttk.Button(
        buttons_frame, text="Stop", bootstyle="danger", state="disabled"
    )
    stop_backmap_button.pack(side="left", expand=True, fill='x', padx=5, pady=5)

    # VMD Output Frame with Scrollbars
    vmd_output_frame = ttk.LabelFrame(scrollable_frame, text="VMD Output")
    vmd_output_frame.grid(
        row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew"
    )
    vmd_output_frame.grid_columnconfigure(0, weight=1)
    vmd_output_frame.grid_rowconfigure(0, weight=1)

    vmd_output_text = tk.Text(vmd_output_frame, wrap="none")
    vmd_output_text.grid(row=0, column=0, sticky="nsew")

    v_scrollbar = ttk.Scrollbar(
        vmd_output_frame, orient="vertical", command=vmd_output_text.yview
    )
    v_scrollbar.grid(row=0, column=1, sticky="ns")

    h_scrollbar = ttk.Scrollbar(
        vmd_output_frame, orient="horizontal", command=vmd_output_text.xview
    )
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    vmd_output_text.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    vmd_output_text.config(height=8)

    # Open VMD Button (initially disabled)
    open_vmd_button = ttk.Button(
        scrollable_frame,
        text="Open Backmap in VMD",
        bootstyle="primary",
        state="disabled",
    )
    open_vmd_button.grid(row=5, column=0, columnspan=3, padx=10, pady=15, sticky="ew")

    def open_in_vmd():
        """
        Opens the generated backmapped file in VMD.
        """
        try:
            output_file = state.outname
            if not output_file:
                messagebox.showerror("Error", "No output file available.")
                return
            if not os.path.isfile(output_file):
                output_file_pdb = output_file + ".pdb"
                if os.path.isfile(output_file_pdb):
                    output_file = output_file_pdb
                else:
                    messagebox.showerror("Error", f"Output file not found: {output_file}")
                    return
            subprocess.Popen(["vmd", output_file])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open VMD: {e}")

    open_vmd_button.configure(command=open_in_vmd)

    def reset_options():
        """
        Resets Basic and Advanced options to their default values.
        """
        basic_entries['first_entry'].delete(0, "end")
        basic_entries['first_entry'].insert(0, "0")
        basic_entries['last_entry'].delete(0, "end")
        basic_entries['last_entry'].insert(0, "-1")
        basic_entries['each_entry'].delete(0, "end")
        basic_entries['each_entry'].insert(0, "100")
        basic_entries['frames_entry'].delete(0, "end")
        basic_entries['frames_entry'].insert(0, "all")
        basic_entries['outname_entry'].delete(0, "end")
        basic_entries['outname_entry'].insert(0, "backmap")

        advanced_option_vars["No min"].set(False)
        advanced_option_vars["CUDA"].set(False)
        advanced_option_vars["GBSA"].set(False)
        advanced_option_vars["Cutoff"].set("12")
        advanced_option_vars["MPI"].set("1")
        advanced_option_vars["Maxcyc"].set("150")
        advanced_option_vars["ncyc"].set("100")

        options_var.set("basic")
        toggle_frame(basic_options_frame, advanced_options_frame, "basic")

    def stop_backmapping():
        """
        Stops the ongoing backmapping process.
        """
        if state.backmapping_process:
            try:
                state.backmapping_process.terminate()
                vmd_output_text.delete("1.0", "end")
                reset_options()
                stop_backmap_button.config(state="disabled")
                run_backmap_button.config(state="normal")
                open_vmd_button.config(state="disabled")
                vmd_output_text.insert('end', "Backmapping was stopped by the user.\n")
                vmd_output_text.see('end')
                print("Backmapping was stopped by the user.")
                state.backmapping_process = None
                state.backmapping_thread = None
                state.outname = None
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop backmapping: {e}")

    def start_backmapping():
        """
        Initiates the backmapping process in a separate thread.
        """
        run_backmap_button.config(state="disabled")
        stop_backmap_button.config(state="normal")
        vmd_output_text.delete("1.0", "end")
        state.backmapping_thread = threading.Thread(
            target=run_backmapping,
            args=(
                state,
                basic_entries,
                advanced_option_vars,
                vmd_output_text,
                open_vmd_button,
                run_backmap_button,
                stop_backmap_button,
            ),
            daemon=True,
        )
        state.backmapping_thread.start()

    run_backmap_button.configure(command=start_backmapping)
    stop_backmap_button.configure(command=stop_backmapping)

    scrollable_frame.grid_columnconfigure(0, weight=1)
    scrollable_frame.grid_rowconfigure(4, weight=1)

def run_backmapping(
        state,
        basic_entries,
        advanced_vars,
        output_widget,
        open_vmd_button,
        run_backmap_button,
        stop_backmap_button,
):
    """
    Executes the backmapping process using VMD and the required TCL scripts.

    Args:
        state (State): The state object containing process references.
        basic_entries (dict): Entry widgets for basic options.
        advanced_vars (dict): Variables for advanced options.
        output_widget (tk.Text): Text widget for output display.
        open_vmd_button (ttk.Button): Button to open output in VMD.
        run_backmap_button (ttk.Button): Start button.
        stop_backmap_button (ttk.Button): Stop button.
    """
    try:
        amberhome = ensure_amberhome()
    except EnvironmentError as e:
        output_widget.insert("end", f"Error: {str(e)}\n")
        messagebox.showerror("Error", str(e))
        run_backmap_button.config(state="normal")
        stop_backmap_button.config(state="disabled")
        return

    if not state.working_directory:
        output_widget.insert("end", "Working directory not set. Please set it first.\n")
        run_backmap_button.config(state="normal")
        stop_backmap_button.config(state="disabled")
        return

    backmap_dir = os.path.join(state.working_directory, "Backmapping")
    os.makedirs(backmap_dir, exist_ok=True)

    # Build paths to TCL scripts
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    tcl_script = os.path.join(base_dir, "TCL", "backmapping.tcl")
    sirah_tcl_path = os.path.join(base_dir, "TCL", "sirah_vmdtk.tcl")

    # Check TCL script existence
    if not os.path.exists(tcl_script) or not os.path.exists(sirah_tcl_path):
        messagebox.showerror(
            "Script Not Found",
            f"Required TCL scripts not found:\n{tcl_script}\n{sirah_tcl_path}"
        )
        run_backmap_button.config(state="normal")
        stop_backmap_button.config(state="disabled")
        return

    topology_file = os.path.abspath(state.topology_file)
    trajectory_file = os.path.abspath(state.trajectory_file)

    # Collect basic options
    first_frame = basic_entries['first_entry'].get()
    last_frame = basic_entries['last_entry'].get()
    each_frame = basic_entries['each_entry'].get() or "100"
    frames_list = basic_entries['frames_entry'].get() or "all"
    outname_entry_value = basic_entries['outname_entry'].get()
    outname = os.path.join(backmap_dir, outname_entry_value)
    state.outname = outname

    # Check for existing output files and prompt for overwrite
    expected_files = [
        f"{outname}.pdb",
        f"{outname}.prmtop",
        f"{outname}.inpcrd",
    ]
    existing_files = [f for f in expected_files if os.path.exists(f)]

    if existing_files:
        message = "The following files already exist:\n"
        message += "\n".join([os.path.basename(f) for f in existing_files])
        message += "\nDo you want to overwrite them?"
        overwrite = messagebox.askyesno("Overwrite Files?", message)
        if not overwrite:
            output_widget.insert("end", "User chose not to overwrite existing files. Backmapping canceled.\n")
            run_backmap_button.config(state="normal")
            stop_backmap_button.config(state="disabled")
            return

    # Collect advanced options
    nomin = "1" if advanced_vars["No min"].get() else "0"
    cuda = "1" if advanced_vars["CUDA"].get() else "0"
    gbsa = "1" if advanced_vars["GBSA"].get() else "0"
    cutoff = advanced_vars["Cutoff"].get()
    mpi = advanced_vars["MPI"].get()
    maxcyc = advanced_vars["Maxcyc"].get()
    ncyc = advanced_vars["ncyc"].get()

    # Build the VMD command (all paths absolute)
    vmd_command = [
        "vmd",
        "-dispdev", "text",
        "-e", tcl_script,
        "-args",
        topology_file,
        trajectory_file,
        sirah_tcl_path,
        first_frame,
        last_frame,
        each_frame,
        frames_list,
        outname,
        nomin,
        cuda,
        gbsa,
        cutoff,
        mpi,
        maxcyc,
        ncyc,
    ]

    print("VMD command:", " ".join(vmd_command))
    output_widget.insert("end", f"Executing VMD command:\n{' '.join(vmd_command)}\n")
    output_widget.see("end")

    output_queue = queue.Queue()

    def read_output(process, output_queue):
        """
        Reads the subprocess output character by character and places it in the queue.
        """
        while True:
            output = process.stdout.read(1)
            if output == '' and process.poll() is not None:
                break
            if output:
                output_queue.put(output)
                print(output, end='')

    def update_output():
        """
        Updates the output widget with data from the queue.
        """
        try:
            while True:
                output = output_queue.get_nowait()
                output_widget.insert("end", output)
                output_widget.see("end")
        except queue.Empty:
            pass
        if state.backmapping_process and state.backmapping_process.poll() is None:
            output_widget.after(100, update_output)
        else:
            if state.backmapping_process:
                if state.backmapping_process.returncode != 0:
                    output_widget.insert("end",
                        f"\nVMD exited with return code {state.backmapping_process.returncode}\n")
                    print(f"VMD exited with return code {state.backmapping_process.returncode}")
                else:
                    output_widget.insert("end", "\nBackmapping completed successfully.\n")
                    print("Backmapping completed successfully.")
                    open_vmd_button.config(state="normal")
            run_backmap_button.config(state="normal")
            stop_backmap_button.config(state="disabled")
            state.backmapping_process = None
            state.backmapping_thread = None

    def run_command():
        try:
            env = os.environ.copy()
            # THE KEY CHANGE: Launch VMD in the correct working directory
            state.backmapping_process = subprocess.Popen(
                vmd_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                cwd=backmap_dir  # Ensures all output goes into the Backmapping directory
            )
            threading.Thread(
                target=read_output,
                args=(state.backmapping_process, output_queue),
                daemon=True,
            ).start()
            update_output()
        except Exception as e:
            output_widget.insert("end", f"Error: {str(e)}\n")
            print(f"Error: {str(e)}")
            run_backmap_button.config(state="normal")
            stop_backmap_button.config(state="disabled")
            state.backmapping_process = None
            state.backmapping_thread = None
            state.outname = None

    threading.Thread(target=run_command, daemon=True).start()

def create_basic_options(parent_frame):
    """
    Creates the Basic Options frame with input fields for backmapping parameters.

    Args:
        parent_frame (ttk.Frame): Parent frame for the Basic Options.

    Returns:
        tuple: (Basic Options frame, dictionary of entry widgets)
    """
    frame = ttk.LabelFrame(parent_frame, text="Basic Options")
    entries = {}

    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(3, weight=1)
    frame.grid_columnconfigure(5, weight=1)

    ttk.Label(frame, text="First:").grid(row=0, column=0, padx=2, pady=2, sticky="e")
    entries['first_entry'] = ttk.Entry(frame, width=8)
    entries['first_entry'].insert(0, "0")
    entries['first_entry'].grid(row=0, column=1, padx=2, pady=2, sticky="ew")

    ttk.Label(frame, text="Last:").grid(row=0, column=2, padx=2, pady=2, sticky="e")
    entries['last_entry'] = ttk.Entry(frame, width=8)
    entries['last_entry'].insert(0, "-1")
    entries['last_entry'].grid(row=0, column=3, padx=2, pady=2, sticky="ew")

    ttk.Label(frame, text="Each:").grid(row=0, column=4, padx=2, pady=2, sticky="e")
    entries['each_entry'] = ttk.Entry(frame, width=8)
    entries['each_entry'].insert(0, "100")
    entries['each_entry'].grid(row=0, column=5, padx=2, pady=2, sticky="ew")

    ttk.Label(frame, text="Frames:").grid(row=1, column=0, padx=2, pady=2, sticky="e")
    entries['frames_entry'] = ttk.Entry(frame, width=30)
    entries['frames_entry'].insert(0, "all")
    entries['frames_entry'].grid(row=1, column=1, columnspan=5, padx=2, pady=2, sticky="ew")

    ttk.Label(frame, text="Outname:").grid(row=2, column=0, padx=2, pady=2, sticky="e")
    entries['outname_entry'] = ttk.Entry(frame, width=30)
    entries['outname_entry'].insert(0, "backmap")
    entries['outname_entry'].grid(row=2, column=1, columnspan=5, padx=2, pady=2, sticky="ew")

    frame.grid_rowconfigure(3, minsize=20)
    return frame, entries

def create_advanced_options(parent_frame):
    """
    Creates the Advanced Options frame with additional configurable parameters.

    Args:
        parent_frame (ttk.Frame): Parent frame to contain the Advanced Options.

    Returns:
        tuple: (Advanced Options frame, dictionary of option variables)
    """
    frame = ttk.LabelFrame(parent_frame, text="Advanced Options", padding=(5, 5))

    advanced_option_vars = {
        "No min": tk.BooleanVar(value=False),
        "CUDA": tk.BooleanVar(value=False),
        "GBSA": tk.BooleanVar(value=False),
        "Cutoff": tk.StringVar(value="12"),
        "MPI": tk.StringVar(value="1"),
        "Maxcyc": tk.StringVar(value="150"),
        "ncyc": tk.StringVar(value="100"),
    }

    checkbuttons_frame = ttk.Frame(frame)
    checkbuttons_frame.grid(row=0, column=0, columnspan=8, sticky="w", pady=5)
    ttk.Checkbutton(
        checkbuttons_frame, text="No min", variable=advanced_option_vars["No min"]
    ).pack(side="left", padx=6)
    ttk.Checkbutton(
        checkbuttons_frame, text="CUDA", variable=advanced_option_vars["CUDA"]
    ).pack(side="left", padx=6)
    ttk.Checkbutton(
        checkbuttons_frame, text="GBSA", variable=advanced_option_vars["GBSA"]
    ).pack(side="left", padx=6)

    ttk.Label(frame, text="Cutoff:").grid(
        row=1, column=0, padx=6, pady=5, sticky="e"
    )
    ttk.Entry(
        frame, textvariable=advanced_option_vars["Cutoff"], width=10
    ).grid(row=1, column=1, padx=6, pady=5, sticky="ew")

    ttk.Label(frame, text="MPI:").grid(
        row=1, column=2, padx=6, pady=5, sticky="e"
    )
    ttk.Entry(
        frame, textvariable=advanced_option_vars["MPI"], width=10
    ).grid(row=1, column=3, padx=6, pady=5, sticky="ew")

    ttk.Label(frame, text="Maxcyc:").grid(
        row=1, column=4, padx=6, pady=5, sticky="e"
    )
    ttk.Entry(
        frame, textvariable=advanced_option_vars["Maxcyc"], width=10
    ).grid(row=1, column=5, padx=6, pady=5, sticky="ew")

    ttk.Label(frame, text="ncyc:").grid(
        row=1, column=6, padx=6, pady=5, sticky="e"
    )
    ttk.Entry(
        frame, textvariable=advanced_option_vars["ncyc"], width=10
    ).grid(row=1, column=7, padx=6, pady=5, sticky="ew")

    frame.grid_rowconfigure(2, minsize=40)
    return frame, advanced_option_vars

def disable_frame_contents(frame):
    """
    Disables all child widgets within a given frame.

    Args:
        frame (ttk.Frame): The frame whose child widgets will be disabled.
    """
    for child in frame.winfo_children():
        child.configure(state="disabled")

def enable_frame_contents(frame):
    """
    Enables all child widgets within a given frame.

    Args:
        frame (ttk.Frame): The frame whose child widgets will be enabled.
    """
    for child in frame.winfo_children():
        child.configure(state="normal")

def toggle_frame(basic_frame, advanced_frame, option):
    """
    Toggles visibility between Basic and Advanced options frames.

    Args:
        basic_frame (ttk.Frame): Basic Options frame.
        advanced_frame (ttk.Frame): Advanced Options frame.
        option (str): Selected option ("basic" or "advanced").
    """
    if option == "basic":
        basic_frame.grid()
        advanced_frame.grid_remove()
    else:
        advanced_frame.grid()
        basic_frame.grid_remove()

