import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import subprocess
import threading
import os
import queue

def create_ss_analysis_tab(tab, state):
    """
    Create the Secondary Structure (SS) analysis tab within the given parent widget.

    This tab includes:
    - Input parameters for analysis (first, last, selection, each).
    - A toggle for calculating Psi/Phi angles.
    - A textbox to display VMD output.
    - Buttons to run the SS analysis and generate associated plots.
    - The ability to change output file names.
    - An always-enabled button to run the Psi/Phi analysis independently.

    :param tab: The parent widget (tab) in which the SS analysis UI is created.
    :param state: An object holding the application state (working_directory, topology_file, etc.).
    """
    # Main frame for the tab
    main_frame = ttk.Frame(tab)
    main_frame.pack(fill='both', expand=True)

    # Set up scrollable frame
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    def on_frame_configure(event):
        """
        Update the scroll region when the frame size changes.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_frame_configure)
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Configure columns for responsiveness
    scrollable_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

    # Input fields: first and last
    first_label = ttk.Label(scrollable_frame, text="First:")
    first_label.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="e")
    first_entry = ttk.Entry(scrollable_frame)
    first_entry.insert(0, "0")  # Default value
    first_entry.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")

    last_label = ttk.Label(scrollable_frame, text="Last:")
    last_label.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="e")
    last_entry = ttk.Entry(scrollable_frame)
    last_entry.insert(0, "-1")  # Default value
    last_entry.grid(row=0, column=3, padx=(0, 5), pady=5, sticky="w")

    # Toggle for Ramachandran (Psi/Phi)
    ramach_var = tk.BooleanVar(value=False)
    ramach_checkbutton = ttk.Checkbutton(
        scrollable_frame, text="Calculate Psi/Phi", variable=ramach_var, bootstyle="danger-round-toggle"
    )
    ramach_checkbutton.grid(row=0, column=4, padx=10, pady=5)

    # Input fields: selection and each
    selection_label = ttk.Label(scrollable_frame, text="Selection:")
    selection_label.grid(row=1, column=0, padx=(5, 0), pady=5, sticky="e")
    selection_entry = ttk.Entry(scrollable_frame)
    selection_entry.insert(0, "all")
    selection_entry.grid(row=1, column=1, padx=(0, 5), pady=5, sticky="w")

    each_label = ttk.Label(scrollable_frame, text="Each:")
    each_label.grid(row=1, column=2, padx=(5, 0), pady=5, sticky="e")
    each_entry = ttk.Entry(scrollable_frame)
    each_entry.insert(0, "1")
    each_entry.grid(row=1, column=3, padx=(0, 5), pady=5, sticky="w")

    # VMD output text box
    vmd_output_frame = ttk.LabelFrame(scrollable_frame, text="VMD Output")
    vmd_output_frame.grid(row=2, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

    vmd_output_height = 10
    text_box = tk.Text(vmd_output_frame, width=80, height=vmd_output_height, wrap="none")
    text_box.grid(row=0, column=0, sticky="nsew")

    v_scrollbar = ttk.Scrollbar(vmd_output_frame, orient="vertical", command=text_box.yview)
    v_scrollbar.grid(row=0, column=1, sticky="ns")

    h_scrollbar = ttk.Scrollbar(vmd_output_frame, orient="horizontal", command=text_box.xview)
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    text_box.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    vmd_output_frame.grid_columnconfigure(0, weight=1)
    vmd_output_frame.grid_rowconfigure(0, weight=1)

    def analyze_psi_phi():
        """
        Run the ramach.py script to analyze Psi/Phi angles.
        This button will remain enabled at all times regardless of the state.
        """
        if not state.working_directory:
            # The user has requested that this button works even without setting the directory,
            # but we can still show a warning or proceed. Here we just run if possible.
            messagebox.showwarning(
                "Warning",
                "No working directory set. The analysis may fail."
            )

        script_dir = os.path.dirname(os.path.abspath(__file__))
        ramach_script_path = os.path.join(script_dir, 'ramach.py')

        if not os.path.isfile(ramach_script_path):
            messagebox.showerror("Error", f"ramach.py not found at {ramach_script_path}")
            return

        try:
            subprocess.Popen(["python", ramach_script_path], cwd=state.working_directory if state.working_directory else None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run ramach.py: {e}")

    def run_ss_analysis():
        """
        Run the SS analysis by executing a VMD script (sirah_ss.tcl).
        """
        # Disable only the SS and plot buttons, NOT the Psi/Phi button
        ss_button.config(state="disabled")
        plot_matrix_button.config(state="disabled")
        plot_by_frame_button.config(state="disabled")
        plot_by_res_button.config(state="disabled")
        # We do NOT disable psi_phi_button here, so it stays enabled

        text_box.delete('1.0', 'end')

        if not state.topology_file or not state.trajectory_file:
            messagebox.showerror(
                "Error",
                "Please load both topology and trajectory files before running the analysis."
            )
            ss_button.config(state="normal")
            return

        if not state.working_directory:
            messagebox.showerror(
                "Error",
                "Please set the working directory in the Load Files tab before running the analysis."
            )
            ss_button.config(state="normal")
            return

        first = first_entry.get()
        last = last_entry.get()
        selection = selection_entry.get()
        each = each_entry.get()
        ramach = "1" if ramach_var.get() else "0"

        # Handle output filenames based on user choice
        if change_outfiles_var.get():
            byframe = byframe_entry.get()
            byres = byres_entry.get()
            global_out = global_entry.get()
            mtx = mtx_entry.get()
            psi = psi_entry.get() if ramach_var.get() else ""
            phi = phi_entry.get() if ramach_var.get() else ""
        else:
            byframe = "ss_by_frame.xvg"
            byres = "ss_by_res.xvg"
            global_out = "ss_global.xvg"
            mtx = "ss.mtx"
            psi = "psi.mtx" if ramach_var.get() else ""
            phi = "phi.mtx" if ramach_var.get() else ""

        script_dir = os.path.dirname(os.path.abspath(__file__))
        tcl_dir = os.path.join(script_dir, '..', 'TCL')
        script_path = os.path.join(tcl_dir, 'sirah_ss.tcl')

        output_dir = os.path.join(state.working_directory, 'ss_analysis')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        expected_files = []
        if change_outfiles_var.get():
            expected_files.append(byframe)
            expected_files.append(byres)
            expected_files.append(global_out)
            expected_files.append(mtx)
            if ramach_var.get():
                expected_files.append(psi)
                expected_files.append(phi)
        else:
            expected_files.append("ss_by_frame.xvg")
            expected_files.append("ss_by_res.xvg")
            expected_files.append("ss_global.xvg")
            expected_files.append("ss.mtx")
            if ramach_var.get():
                expected_files.append("psi.mtx")
                expected_files.append("phi.mtx")

        expected_files = [os.path.join(output_dir, f) for f in expected_files if f != ""]

        existing_files = [f for f in expected_files if os.path.exists(f)]

        if existing_files:
            message = "The following files already exist:\n"
            message += "\n".join([os.path.basename(f) for f in existing_files])
            message += "\nDo you want to overwrite them?"

            overwrite = messagebox.askyesno("Overwrite Files?", message)

            if not overwrite:
                ss_button.config(state="normal")
                return

        cmd = [
            "vmd",
            "-dispdev", "text",
            "-e", script_path,
            "-args",
            os.path.abspath(state.topology_file),
            os.path.abspath(state.trajectory_file),
            first,
            last,
            selection,
            each,
            ramach,
            tcl_dir,
            output_dir,
            byframe,
            byres,
            global_out,
            mtx,
            psi,
            phi
        ]

        output_queue = queue.Queue()

        def read_output(process, output_queue):
            """
            Read output from the process and put it into a queue for the UI to display.
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
            Update the text box with process output from the queue.
            """
            try:
                while True:
                    output = output_queue.get_nowait()
                    text_box.insert("end", output)
                    text_box.see("end")
                text_box.update_idletasks()
            except queue.Empty:
                pass
            if process and process.poll() is None:
                text_box.after(100, update_output)
            else:
                # Process finished
                if process:
                    if process.returncode != 0:
                        text_box.insert("end", f"\nVMD exited with return code {process.returncode}\n")
                        print(f"VMD exited with return code {process.returncode}")
                    else:
                        text_box.insert("end", "\nSS Analysis completed successfully.\n")
                        print("SS Analysis completed successfully.")
                        # Enable plot buttons after successful analysis
                        plot_matrix_button.config(state="normal")
                        plot_by_frame_button.config(state="normal")
                        plot_by_res_button.config(state="normal")
                        # psi_phi_button remains always enabled
                ss_button.config(state="normal")

        def run_command():
            nonlocal process
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    cwd=output_dir
                )

                threading.Thread(target=read_output, args=(process, output_queue), daemon=True).start()
                update_output()

            except Exception as e:
                text_box.insert("end", f"Error: {str(e)}\n")
                print(f"Error: {str(e)}")
                ss_button.config(state="normal")
                # Plot buttons remain disabled if error occurs

        process = None
        threading.Thread(target=run_command).start()

    # Run SS Analysis button
    ss_button = ttk.Button(
        scrollable_frame, text="Run SS Analysis", bootstyle="success", command=run_ss_analysis
    )
    ss_button.grid(row=1, column=4, padx=10, pady=5)

    # Out Files Frame
    outfiles_frame = ttk.LabelFrame(scrollable_frame, text="Output Files")
    outfiles_frame.grid(row=3, column=0, columnspan=5, padx=10, pady=10, sticky="ew")
    outfiles_frame.columnconfigure((0, 1, 2, 3), weight=1)

    change_outfiles_var = tk.BooleanVar(value=False)
    change_outfiles_checkbutton = ttk.Checkbutton(
        outfiles_frame, text="Change Output Files Names", variable=change_outfiles_var, bootstyle="round-toggle"
    )
    change_outfiles_checkbutton.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w")

    # Output files entries
    byframe_label = ttk.Label(outfiles_frame, text="By Frame:")
    byframe_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
    byframe_entry = ttk.Entry(outfiles_frame)
    byframe_entry.insert(0, "ss_by_frame.xvg")
    byframe_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    byres_label = ttk.Label(outfiles_frame, text="By Res:")
    byres_label.grid(row=1, column=2, padx=5, pady=5, sticky="e")
    byres_entry = ttk.Entry(outfiles_frame)
    byres_entry.insert(0, "ss_by_res.xvg")
    byres_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

    global_label = ttk.Label(outfiles_frame, text="Global:")
    global_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
    global_entry = ttk.Entry(outfiles_frame)
    global_entry.insert(0, "ss_global.xvg")
    global_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    mtx_label = ttk.Label(outfiles_frame, text="Matrix:")
    mtx_label.grid(row=2, column=2, padx=5, pady=5, sticky="e")
    mtx_entry = ttk.Entry(outfiles_frame)
    mtx_entry.insert(0, "ss.mtx")
    mtx_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")

    psi_label = ttk.Label(outfiles_frame, text="Psi:")
    psi_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
    psi_entry = ttk.Entry(outfiles_frame)
    psi_entry.insert(0, "psi.mtx")
    psi_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    psi_entry.config(state="disabled")

    phi_label = ttk.Label(outfiles_frame, text="Phi:")
    phi_label.grid(row=3, column=2, padx=5, pady=5, sticky="e")
    phi_entry = ttk.Entry(outfiles_frame)
    phi_entry.insert(0, "phi.mtx")
    phi_entry.grid(row=3, column=3, padx=5, pady=5, sticky="w")
    phi_entry.config(state="disabled")

    def toggle_psi_phi():
        """
        Update the state of PSI/PHI entries based on whether psi/phi calculation is enabled.
        """
        update_psi_phi_entries()

    def toggle_outfiles_entries():
        """
        Enable or disable outfiles entries depending on whether the user wants to change them.
        Reset to defaults if disabled.
        """
        if change_outfiles_var.get():
            state_var = "normal"
        else:
            state_var = "disabled"
            byframe_entry.config(state="normal")
            byframe_entry.delete(0, tk.END)
            byframe_entry.insert(0, "ss_by_frame.xvg")

            byres_entry.config(state="normal")
            byres_entry.delete(0, tk.END)
            byres_entry.insert(0, "ss_by_res.xvg")

            global_entry.config(state="normal")
            global_entry.delete(0, tk.END)
            global_entry.insert(0, "ss_global.xvg")

            mtx_entry.config(state="normal")
            mtx_entry.delete(0, tk.END)
            mtx_entry.insert(0, "ss.mtx")

            if ramach_var.get():
                psi_entry.config(state="normal")
                psi_entry.delete(0, tk.END)
                psi_entry.insert(0, "psi.mtx")

                phi_entry.config(state="normal")
                phi_entry.delete(0, tk.END)
                phi_entry.insert(0, "phi.mtx")
            else:
                psi_entry.delete(0, tk.END)
                phi_entry.delete(0, tk.END)

        byframe_entry.config(state=state_var)
        byres_entry.config(state=state_var)
        global_entry.config(state=state_var)
        mtx_entry.config(state=state_var)
        update_psi_phi_entries()

    def update_psi_phi_entries():
        """
        Enable psi_entry and phi_entry only if both changing output files and ramach_var are active.
        Otherwise disable or reset them.
        """
        if change_outfiles_var.get() and ramach_var.get():
            psi_entry.config(state="normal")
            phi_entry.config(state="normal")
        else:
            if not change_outfiles_var.get():
                psi_entry.config(state="disabled")
                psi_entry.delete(0, tk.END)
                psi_entry.insert(0, "psi.mtx")

                phi_entry.config(state="disabled")
                phi_entry.delete(0, tk.END)
                phi_entry.insert(0, "phi.mtx")
            else:
                psi_entry.config(state="disabled")
                phi_entry.config(state="disabled")

    toggle_outfiles_entries()

    ramach_checkbutton.config(command=toggle_psi_phi)
    change_outfiles_checkbutton.config(command=toggle_outfiles_entries)

    # Analysis frame for plot and Psi/Phi analysis
    analysis_frame = ttk.LabelFrame(scrollable_frame, text="Analysis")
    analysis_frame.grid(row=5, column=0, columnspan=5, padx=10, pady=10, sticky="ew")
    analysis_frame.columnconfigure((0, 1, 2, 3), weight=1)

    def plot_matrix():
        """
        Plot the SS matrix using ss_plots.py with the matrix file.
        """
        output_dir = os.path.join(state.working_directory, 'ss_analysis')
        mtx_file = os.path.join(output_dir, mtx_entry.get() if change_outfiles_var.get() else "ss.mtx")

        if not os.path.isfile(mtx_file):
            messagebox.showerror("Error", f"Matrix file not found: {mtx_file}")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        plots_dir = os.path.join(script_dir, 'plots')
        ss_plots_script = os.path.join(plots_dir, 'ss_plots.py')

        try:
            each_value = float(each_entry.get())
        except ValueError:
            messagebox.showerror("Error", "The value of 'Each' must be a number.")
            return

        try:
            time_step = getattr(state, 'time_step', None)
            steps_between_frames = getattr(state, 'steps_between_frames', None)
            # Default values if not set
            time_step_value = time_step.get() if isinstance(time_step, tk.Variable) else "20"
            steps_between_frames_value = steps_between_frames.get() if steps_between_frames else "5000"
        except ValueError:
            messagebox.showerror("Error", "Invalid value for time step or steps between frames.")
            return

        dt_factor = float(time_step_value) * float(steps_between_frames_value) * 0.000000001 * each_value

        cmd = [
            "python",
            ss_plots_script,
            "-t", "mtx",
            "-i", mtx_file,
            "-dt", str(dt_factor)
        ]

        threading.Thread(target=lambda: subprocess.Popen(cmd)).start()

    def plot_by_frame():
        """
        Plot the SS by frame using ss_plots.py.
        """
        output_dir = os.path.join(state.working_directory, 'ss_analysis')
        by_frame_file = os.path.join(output_dir, byframe_entry.get() if change_outfiles_var.get() else "ss_by_frame.xvg")

        if not os.path.isfile(by_frame_file):
            messagebox.showerror("Error", f"By Frame file not found: {by_frame_file}")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        plots_dir = os.path.join(script_dir, 'plots')
        ss_plots_script = os.path.join(plots_dir, 'ss_plots.py')

        try:
            each_value = float(each_entry.get())
        except ValueError:
            messagebox.showerror("Error", "The value of 'Each' must be a number.")
            return

        try:
            time_step = getattr(state, 'time_step', None)
            steps_between_frames = getattr(state, 'steps_between_frames', None)
            time_step_value = time_step.get() if isinstance(time_step, tk.Variable) else "20"
            steps_between_frames_value = steps_between_frames.get() if steps_between_frames else "5000"
        except ValueError:
            messagebox.showerror("Error", "Invalid value for time step or steps between frames.")
            return

        dt_factor = float(time_step_value) * float(steps_between_frames_value) * 0.000000001 * each_value

        cmd = [
            "python",
            ss_plots_script,
            "-t", "frame",
            "-i", by_frame_file,
            "-dt", str(dt_factor)
        ]

        threading.Thread(target=lambda: subprocess.Popen(cmd)).start()

    def plot_by_res():
        """
        Plot the SS by residues using ss_plots.py.
        """
        output_dir = os.path.join(state.working_directory, 'ss_analysis')
        by_res_file = os.path.join(output_dir, byres_entry.get() if change_outfiles_var.get() else "ss_by_res.xvg")

        if not os.path.isfile(by_res_file):
            messagebox.showerror("Error", f"By Res file not found: {by_res_file}")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        plots_dir = os.path.join(script_dir, 'plots')
        ss_plots_script = os.path.join(plots_dir, 'ss_plots.py')

        cmd = [
            "python",
            ss_plots_script,
            "-t", "res",
            "-i", by_res_file
        ]

        threading.Thread(target=lambda: subprocess.Popen(cmd)).start()

    # Create and place the buttons in the analysis frame
    plot_matrix_button = ttk.Button(
        analysis_frame, text="Plot Matrix", bootstyle="primary", command=plot_matrix, state="disabled"
    )
    plot_by_frame_button = ttk.Button(
        analysis_frame, text="Plot By Frame", bootstyle="primary", command=plot_by_frame, state="disabled"
    )
    plot_by_res_button = ttk.Button(
        analysis_frame, text="Plot By Res", bootstyle="primary", command=plot_by_res, state="disabled"
    )
    # The Analyze Psi/Phi button is always enabled
    psi_phi_button = ttk.Button(
        analysis_frame, text="Analyze Psi/Phi", bootstyle="success", command=analyze_psi_phi
    )

    plot_matrix_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    plot_by_frame_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    plot_by_res_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
    psi_phi_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    analysis_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def disable_plot_buttons():
        """
        Disable all plot buttons.
        The Psi/Phi button is not disabled to ensure it is always available.
        """
        plot_matrix_button.config(state="disabled")
        plot_by_frame_button.config(state="disabled")
        plot_by_res_button.config(state="disabled")
        # Do not disable psi_phi_button here

    # Initially disable plot buttons until analysis is run, psi_phi_button stays enabled
    disable_plot_buttons()
