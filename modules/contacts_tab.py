"""
Contacts Analysis Module

This module provides functionalities to perform contact analysis using VMD (Visual Molecular Dynamics)
and various custom scripts. It includes a graphical user interface (GUI) built with Tkinter and ttkbootstrap,
allowing users to configure analysis parameters, execute contact analysis, and generate relevant plots.

Features:
    - Execute contact analysis with user-defined selections, skip values, and cutoff distances.
    - Run additional analysis scripts for native contacts conservation, contact maps, and distance maps by frame.
    - Display VMD output within the GUI.
    - Log all operations and errors for debugging and record-keeping.

Dependencies:
    - os
    - tkinter
    - ttkbootstrap
    - subprocess
    - threading
    - logging
    - glob

Usage:
    Integrate this module within a larger Tkinter application to provide contact analysis capabilities.

Author:
    SIRAH TEAM

Date:
    2024
"""

import os
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import subprocess
import threading
import logging
import glob

# Configure the logging system
logging.basicConfig(
    filename='contact_analysis.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global variable to store the running VMD process
vmd_process = None
stop_event = threading.Event()  # Event to signal when to stop the process


def stop_vmd_process():
    """
    Signals the worker thread to stop the VMD process.
    """
    global stop_event
    stop_event.set()  # Signal to stop the process
    logging.info("Stop event set.")
    # Optionally, inform the user that the stop command has been sent
    messagebox.showinfo("Stopping", "Attempting to stop the calculation.")


def run_contacts_analysis(state, sel1_entry, sel2_entry, skip_entry, cutoff_entry,
                          calc_distance_matrix_value, vmd_output):
    """
    Executes contact analysis using VMD with the provided selections, skip, and cutoff values.
    """
    global vmd_process, stop_event

    # Reset stop_event before starting the process
    stop_event.clear()

    selection1 = sel1_entry.get().strip()
    selection2 = sel2_entry.get().strip()
    skip = skip_entry.get().strip()
    cutoff = cutoff_entry.get().strip()
    reference_file = getattr(state, 'reference_file', None)
    reference_file_value = reference_file if reference_file else "None"

    # Input Validation
    if not selection1 or not selection2 or not skip.isdigit() or int(skip) <= 0 or not cutoff:
        messagebox.showerror(
            "Input Error",
            "Please provide valid selections, a positive skip value, and a cutoff distance."
        )
        return

    logging.info(
        f"Preparing to execute contact analysis with Selection1='{selection1}', Selection2='{selection2}', "
        f"Skip={skip}, Cutoff={cutoff}, CalculateDistanceMatrix={int(calc_distance_matrix_value)}"
    )

    skip = int(skip)

    # Verify that topology and trajectory files are loaded
    if not hasattr(state, 'topology_file') or not hasattr(state, 'trajectory_file') \
            or not state.topology_file or not state.trajectory_file:
        messagebox.showerror(
            "File Error",
            "Please load the topology and trajectory files in the 'Load Files' tab."
        )
        return

    # Create the "Contacts" directory
    contacts_dir = os.path.join(state.working_directory, "Contacts")
    os.makedirs(contacts_dir, exist_ok=True)

    # Adjust the path to the TCL script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Move up two levels to find 'TCL'
    tcl_script_path = os.path.join(base_dir, "TCL", "contacts_distance.tcl")
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "TCL")

    if not os.path.exists(tcl_script_path):
        messagebox.showerror(
            "Script Not Found",
            f"The TCL script was not found: {tcl_script_path}"
        )
        logging.error(f"TCL script not found: {tcl_script_path}")
        return

    # Clean selections for file naming
    sel1_clean = selection1.replace(" ", "")
    sel2_clean = selection2.replace(" ", "")

    # Generate the list of expected output files
    expected_files = []

    expected_files.append(os.path.join(contacts_dir, f"contacts_length_{sel1_clean}_{sel2_clean}.dat"))
    expected_files.append(os.path.join(contacts_dir, f"distbyframe_{sel1_clean}_{sel2_clean}.dat"))
    expected_files.append(os.path.join(contacts_dir, f"percentage_{sel1_clean}_{sel2_clean}.dat"))
    expected_files.append(os.path.join(contacts_dir, f"contacts_{sel1_clean}_{sel2_clean}.dat"))
    expected_files.append(os.path.join(contacts_dir, f"timeline_{sel1_clean}_{sel2_clean}.dat"))
    expected_files.append(os.path.join(contacts_dir, f"distance_length_{sel1_clean}_{sel2_clean}.dat"))

    # If Calculate Distance Matrix is selected, additional files may be generated
    if calc_distance_matrix_value:
        expected_files.append(os.path.join(contacts_dir, f"distance_matrix_{sel1_clean}_{sel2_clean}.dat"))

    # Check if the files exist
    existing_files = [f for f in expected_files if os.path.exists(f)]

    if existing_files:
        message = "The following files already exist:\n"
        message += "\n".join([os.path.basename(f) for f in existing_files])
        message += "\nDo you want to overwrite them?"

        overwrite = messagebox.askyesno("Overwrite Files?", message)

        if not overwrite:
            # User does not want to overwrite, cancel the analysis
            logging.info("User chose not to overwrite existing files. Analysis canceled.")
            return

    # Command to execute VMD with the provided arguments
    command = [
        "vmd", "-dispdev", "text", "-e", tcl_script_path, "-args",
        state.topology_file,
        state.trajectory_file,
        selection1,
        selection2,
        str(skip),
        str(cutoff),
        contacts_dir,
        str(int(calc_distance_matrix_value)),
        reference_file_value,
        script_dir
    ]

    # Function to update the VMD output text box
    def update_text_box(output):
        def inner():
            vmd_output.config(state=tk.NORMAL)
            vmd_output.insert(tk.END, output)
            vmd_output.see(tk.END)
            vmd_output.config(state=tk.DISABLED)
            print(output, end="")  # <--- Imprime en la terminal como en Analysis
        vmd_output.after(0, inner)


    # Function to show a message box in the main thread
    def show_message(title, message, error=False):
        """
        Displays a message box with the given title and message in the main thread.
        """
        def inner():
            if error:
                messagebox.showerror(title, message)
            else:
                messagebox.showinfo(title, message)

        vmd_output.after(0, inner)

    # Function to execute the VMD command in a separate thread
    def run_command():
        """
        Executes the VMD command and handles output and errors in a thread.
        """
        global vmd_process
        try:
            vmd_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=state.working_directory
            )

            # Continuously read from the process output
            while True:
                if stop_event.is_set():  # Stop processing if stop_event is triggered
                    vmd_process.terminate()  # Attempt to terminate the process
                    try:
                        vmd_process.wait(timeout=5)  # Wait for the process to finish
                    except subprocess.TimeoutExpired:
                        vmd_process.kill()  # Force kill if terminate doesn't work
                    update_text_box("Process stopped by user.\n")
                    logging.info("Process stopped by user.")
                    show_message("Process Stopped", "The calculation was canceled.")
                    return

                line = vmd_process.stdout.readline()
                if not line:  # Exit if no more output
                    break
                update_text_box(line)

            vmd_process.wait()  # Wait for process to complete normally

            # Check if the process was terminated
            if vmd_process.returncode != 0 and not stop_event.is_set():
                logging.error(f"VMD exited with return code {vmd_process.returncode}")
                show_message("Error", f"VMD exited with return code {vmd_process.returncode}.", error=True)
                return

            # Verify generated files
            if not stop_event.is_set():
                percentage_pattern = os.path.join(contacts_dir, f"percentage_{sel1_clean}_{sel2_clean}.dat")
                if os.path.exists(percentage_pattern):
                    logging.info(f"Analysis completed and files saved in {contacts_dir}")
                    show_message(
                        "Success",
                        f"Analysis completed and files saved in {contacts_dir}"
                    )
                    # Update the state to indicate successful analysis
                    state.run_analysis_successful.set(True)
                else:
                    update_text_box("No percentage files were generated.\n")
                    show_message(
                        "Output Error",
                        "No percentage files were found.",
                        error=True
                    )

        except subprocess.TimeoutExpired:
            logging.error("The VMD process timed out.")
            update_text_box("The VMD process was forcefully terminated.\n")
        except Exception as e:
            logging.error(f"Error in VMD process: {str(e)}")
            update_text_box(f"Error occurred: {str(e)}\n")
            show_message("Error", f"An error occurred while running VMD:\n{str(e)}", error=True)
        finally:
            vmd_process = None  # Ensure vmd_process is cleared
            # Ensure the progress window is destroyed in the main thread
            if hasattr(state, 'progress_window') and state.progress_window:
                vmd_output.after(0, state.progress_window.destroy)

    # Run the command in a separate daemon thread
    threading.Thread(target=run_command, daemon=True).start()

def run_contacts_by_frame(state, sel1, sel2):
    """
    Executes the 'contacts_by_frame.py' script with the required arguments using necessary files.

    Args:
        state (object): Application state containing working_directory.
        sel1 (str): User-defined Selection 1.
        sel2 (str): User-defined Selection 2.
    """
    contacts_dir = os.path.join(state.working_directory, "Contacts")

    # Clean selections by removing spaces
    sel1_clean = sel1.replace(" ", "")
    sel2_clean = sel2.replace(" ", "")

    # Construct file names
    distbyframe_file_name = f"distbyframe_{sel1_clean}_{sel2_clean}.dat"
    length_file_name = f"distance_length_{sel1_clean}_{sel2_clean}.dat"

    distbyframe_file = os.path.join(contacts_dir, distbyframe_file_name)
    length_file = os.path.join(contacts_dir, length_file_name)

    # Verify that the required files exist
    if not os.path.exists(distbyframe_file):
        messagebox.showerror(
            "File Not Found",
            f"File '{distbyframe_file_name}' not found in {contacts_dir}."
        )
        logging.error(f"File '{distbyframe_file_name}' not found in {contacts_dir}.")
        return

    if not os.path.exists(length_file):
        messagebox.showerror(
            "File Not Found",
            f"File '{length_file_name}' not found in {contacts_dir}."
        )
        logging.error(f"File '{length_file_name}' not found in {contacts_dir}.")
        return

    # Path to the 'contacts_by_frame.py' script
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "modules", "plots", "contacts_by_frame.py"
    )

    if not os.path.exists(script_path):
        messagebox.showerror(
            "Script Not Found",
            f"The script 'contacts_by_frame.py' was not found at {script_path}."
        )
        logging.error(f"Script 'contacts_by_frame.py' not found at {script_path}.")
        return

    # Command to execute the 'contacts_by_frame.py' script
    command = [
        "python", script_path, distbyframe_file, length_file
    ]

    def show_message(message, title="Info"):
        """
        Displays a message box with the given message and title.
        """
        messagebox.showinfo(title, message)

    # Function to execute the script
    def run_script():
        """
        Executes the 'contacts_by_frame.py' script in a separate thread and handles output and errors.
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=state.working_directory
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info(
                    f"'contacts_by_frame.py' executed successfully.\nOutput:\n{stdout}"
                )
                show_message(
                    f"'contacts_by_frame.py' executed successfully.\n\nOutput:\n{stdout}"
                )
            else:
                logging.error(
                    f"Error executing 'contacts_by_frame.py':\n{stderr}"
                )
                messagebox.showerror(
                    "Script Execution Error",
                    f"Error executing 'contacts_by_frame.py':\n{stderr}"
                )

        except Exception as e:
            messagebox.showerror(
                "Execution Error",
                f"An error occurred while executing 'contacts_by_frame.py': {str(e)}"
            )
            logging.error(f"Error executing 'contacts_by_frame.py': {str(e)}")

    # Run the script in a separate daemon thread
    threading.Thread(target=run_script, daemon=True).start()


def run_native_contacts_conservation(state, sel1, sel2, skip):
    """
    Executes the 'native_contacts.py' script with the required arguments using the generated timeline file.

    Args:
        state (object): Application state containing working_directory.
        sel1 (str): User-defined Selection 1.
        sel2 (str): User-defined Selection 2.
        skip (str): Skip value as a string.
    """
    contacts_dir = os.path.join(state.working_directory, "Contacts")

    # Clean selections by removing spaces
    sel1_clean = sel1.replace(" ", "")
    sel2_clean = sel2.replace(" ", "")

    # Locate the timeline file
    timeline_file_name = f"timeline_{sel1_clean}_{sel2_clean}.dat"
    timeline_file = os.path.join(contacts_dir, timeline_file_name)

    # Retrieve time_step, steps_between_frames, and reference_file from state
    time_step = getattr(state, 'time_step', None)
    steps_between_frames = getattr(state, 'steps_between_frames', None)
    reference_file = getattr(state, 'reference_file', None)

    # Get their values
    time_step_value = time_step.get() if isinstance(time_step, tk.Variable) else "20"
    steps_between_frames_value = steps_between_frames.get() if steps_between_frames else "5000"

    # Calculate the time factor to convert frames to microseconds
    try:
        frames_to_time = float(steps_between_frames_value) * float(time_step_value) * 1e-9 * float(skip)
    except ValueError as e:
        messagebox.showerror(
            "Calculation Error",
            f"Failed to calculate time factor.\nError: {str(e)}"
        )
        logging.error(f"Time factor calculation error: {str(e)}")
        return

    if not os.path.exists(timeline_file):
        messagebox.showerror(
            "File Not Found",
            f"File '{timeline_file_name}' not found in {contacts_dir}."
        )
        logging.error(f"File '{timeline_file_name}' not found in {contacts_dir}.")
        return

    # Path to the 'native_contacts.py' script
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "modules", "plots", "native_contacts.py"
    )

    if not os.path.exists(script_path):
        messagebox.showerror(
            "Script Not Found",
            f"The script 'native_contacts.py' was not found at {script_path}."
        )
        logging.error(f"Script 'native_contacts.py' not found at {script_path}.")
        return

    # Command to execute the 'native_contacts.py' script
    command = [
        "python", script_path, timeline_file, "--time_factor", str(frames_to_time)
    ]

    def show_message(message, title="Info"):
        """
        Displays a message box with the given message and title.
        """
        messagebox.showinfo(title, message)

    # Function to execute the script
    def run_script():
        """
        Executes the 'native_contacts.py' script in a separate thread and handles output and errors.
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=state.working_directory
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info(
                    f"'native_contacts.py' executed successfully.\nOutput:\n{stdout}"
                )
                show_message(
                    f"'native_contacts.py' executed successfully.\n\nOutput:\n{stdout}"
                )
            else:
                logging.error(
                    f"Error executing 'native_contacts.py':\n{stderr}"
                )
                messagebox.showerror(
                    "Script Execution Error",
                    f"Error executing 'native_contacts.py':\n{stderr}"
                )

        except Exception as e:
            messagebox.showerror(
                "Execution Error",
                f"An error occurred while executing 'native_contacts.py': {str(e)}"
            )
            logging.error(f"Error executing 'native_contacts.py': {str(e)}")

    # Run the script in a separate daemon thread
    threading.Thread(target=run_script, daemon=True).start()


def run_matrix_contacts(state, sel1, sel2):
    """
    Executes the 'matrix_contacts.py' script with the required arguments using length and percentage files.

    Args:
        state (object): Application state containing working_directory.
        sel1 (str): User-defined Selection 1.
        sel2 (str): User-defined Selection 2.
    """
    contacts_dir = os.path.join(state.working_directory, "Contacts")

    # Clean selections by removing spaces
    sel1_clean = sel1.replace(" ", "")
    sel2_clean = sel2.replace(" ", "")

    # Construct file names
    length_file_name = f"contacts_length_{sel1_clean}_{sel2_clean}.dat"
    percentage_file_name = f"percentage_{sel1_clean}_{sel2_clean}.dat"

    length_file = os.path.join(contacts_dir, length_file_name)
    percentage_file = os.path.join(contacts_dir, percentage_file_name)

    # Verify that the required files exist
    if not os.path.exists(length_file):
        messagebox.showerror(
            "File Not Found",
            f"File '{length_file_name}' not found in {contacts_dir}."
        )
        logging.error(f"File '{length_file_name}' not found in {contacts_dir}.")
        return

    if not os.path.exists(percentage_file):
        messagebox.showerror(
            "File Not Found",
            f"File '{percentage_file_name}' not found in {contacts_dir}."
        )
        logging.error(f"File '{percentage_file_name}' not found in {contacts_dir}.")
        return

    # Path to the 'matrix_contacts.py' script
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "modules", "plots", "matrix_contacts.py"
    )

    if not os.path.exists(script_path):
        messagebox.showerror(
            "Script Not Found",
            f"The script 'matrix_contacts.py' was not found at {script_path}."
        )
        logging.error(f"Script 'matrix_contacts.py' not found at {script_path}.")
        return

    # Command to execute the 'matrix_contacts.py' script
    command = [
        "python", script_path, length_file, percentage_file
    ]

    def show_message(message, title="Info"):
        """
        Displays a message box with the given message and title.
        """
        messagebox.showinfo(title, message)

    # Function to execute the script
    def run_script():
        """
        Executes the 'matrix_contacts.py' script in a separate thread and handles output and errors.
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=contacts_dir
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info(
                    f"'matrix_contacts.py' executed successfully.\nOutput:\n{stdout}"
                )
                show_message(
                    f"'matrix_contacts.py' executed successfully.\n\nOutput:\n{stdout}"
                )
            else:
                logging.error(
                    f"Error executing 'matrix_contacts.py':\n{stderr}"
                )
                messagebox.showerror(
                    "Script Execution Error",
                    f"Error executing 'matrix_contacts.py':\n{stderr}"
                )

        except Exception as e:
            messagebox.showerror(
                "Execution Error",
                f"An error occurred while executing 'matrix_contacts.py': {str(e)}"
            )
            logging.error(f"Error executing 'matrix_contacts.py': {str(e)}")

    # Run the script in a separate daemon thread
    threading.Thread(target=run_script, daemon=True).start()


def create_contacts_tab(tab, state):
    """
    Creates the Contacts tab in the GUI with configurations, analysis execution, and analysis buttons.

    Args:
        tab (ttk.Frame): The parent tab frame.
        state (object): Application state containing working_directory and file information.
    """
    # Variable to track if the contact analysis has been successfully run
    state.run_analysis_successful = tk.BooleanVar(value=False)

    # Configuration Section
    settings_frame = ttk.Labelframe(tab, text="Settings", padding=(10, 5))
    settings_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
    settings_frame.columnconfigure(0, weight=1)
    settings_frame.columnconfigure(1, weight=1)
    settings_frame.columnconfigure(2, weight=1)
    settings_frame.columnconfigure(3, weight=1)

    # Entry fields for Selection 1, Selection 2, Skip, Cutoff
    ttk.Label(settings_frame, text="Selection 1:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    sel1_entry = ttk.Entry(settings_frame)
    sel1_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    sel1_entry.insert(0, "name GC")

    ttk.Label(settings_frame, text="Selection 2:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    sel2_entry = ttk.Entry(settings_frame)
    sel2_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    sel2_entry.insert(0, "name GC")

    ttk.Label(settings_frame, text="Skip:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    skip_entry = ttk.Entry(settings_frame)
    skip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    skip_entry.insert(0, "100")

    ttk.Label(settings_frame, text="Cutoff (Å):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
    cutoff_entry = ttk.Entry(settings_frame)
    cutoff_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
    cutoff_entry.insert(0, "8.00")

    # Create a BooleanVar for the "Calculate Distance Matrix" Checkbutton
    calc_distance_matrix = tk.BooleanVar()
    calc_distance_matrix.set(False)

    # Execution Section
    run_frame = ttk.Labelframe(tab, text="Run", padding=(10, 5))
    run_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
    run_frame.columnconfigure(0, weight=1)
    run_frame.columnconfigure(1, weight=3)

    # Toggle Button for Calculate Distance Matrix
    toggle_button = ttk.Checkbutton(
        run_frame,
        text="Calculate Distance Matrix",
        variable=calc_distance_matrix,
        bootstyle="success-round-toggle"
    )
    toggle_button.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="ew")

    # Warning Message
    warning_label = ttk.Label(
        run_frame,
        text="Warning: This operation may be slow!",
        foreground="red"
    )
    warning_label.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="ew")

    # Run Contact Analysis Button
    run_button = ttk.Button(
        run_frame,
        text="Run Contact Analysis",
        bootstyle="success",
        command=lambda: run_contacts_analysis(
            state,
            sel1_entry,
            sel2_entry,
            skip_entry,
            cutoff_entry,
            calc_distance_matrix.get(),
            vmd_output
        )
    )
    run_button.grid(row=2, column=0, padx=10, pady=(5, 5), sticky="ew")

    # Stop Button
    stop_button = ttk.Button(
        run_frame,
        text="Stop",
        bootstyle="danger",
        command=stop_vmd_process
    )
    stop_button.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

    # VMD Output Text Box
    vmd_output_frame = ttk.Frame(run_frame, relief="solid", borderwidth=1)
    vmd_output_frame.grid(row=0, column=1, rowspan=4, padx=10, pady=5, sticky="nsew")
    vmd_output = tk.Text(vmd_output_frame, width=50, height=12, wrap="none")
    vmd_output.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(vmd_output_frame, orient="vertical", command=vmd_output.yview)
    scrollbar.pack(side="right", fill="y")
    vmd_output.configure(yscrollcommand=scrollbar.set)
    vmd_output.config(state=tk.DISABLED)

    # Analysis Section
    analysis_frame = ttk.Labelframe(tab, text="Analysis", padding=(10, 5))
    analysis_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
    analysis_frame.columnconfigure(0, weight=1)
    analysis_frame.columnconfigure(1, weight=1)
    analysis_frame.columnconfigure(2, weight=1)

    # Analysis Buttons Initially Disabled
    native_contacts_button = ttk.Button(
        analysis_frame,
        text="Native Contacts Conservation",
        command=lambda: run_native_contacts_conservation(
            state,
            sel1_entry.get(),
            sel2_entry.get(),
            skip_entry.get()
        )
    )
    native_contacts_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    native_contacts_button.config(state='disabled')  # Disabled initially

    contact_map_button = ttk.Button(
        analysis_frame,
        text="Contact Map",
        command=lambda: run_matrix_contacts(
            state,
            sel1_entry.get(),
            sel2_entry.get()
        )
    )
    contact_map_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
    contact_map_button.config(state='disabled')  # Disabled initially

    distance_map_button = ttk.Button(
        analysis_frame,
        text="Distance Map By Frame",
        command=lambda: run_contacts_by_frame(
            state,
            sel1_entry.get(),
            sel2_entry.get()
        )
    )
    distance_map_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
    distance_map_button.config(state='disabled')  # Disabled initially

    # Update the state of the "Distance Map By Frame" button dynamically
    def update_distance_map_button(*args):
        if calc_distance_matrix.get() and state.run_analysis_successful.get():
            distance_map_button.config(state='normal')
        else:
            distance_map_button.config(state='disabled')

    # Enable analysis buttons when contact analysis is successful
    def on_run_analysis_success(*args):
        if state.run_analysis_successful.get():
            native_contacts_button.config(state='normal')
            contact_map_button.config(state='normal')
            update_distance_map_button()

    # Configure dynamic button states
    state.run_analysis_successful.trace_add('write', on_run_analysis_success)
    calc_distance_matrix.trace_add('write', update_distance_map_button)
    update_distance_map_button()
