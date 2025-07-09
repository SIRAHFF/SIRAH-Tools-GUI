# load_files_tab.py

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import shutil
import subprocess
from pathlib import Path
import logging

# Configure logging for debugging purposes
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def add_placeholder(entry: tk.Entry, placeholder: str, style: ttk.Style) -> None:
    entry.insert(0, placeholder)
    entry.config(foreground="grey")
    entry.placeholder = True

    def on_focus_in(event: tk.Event) -> None:
        if getattr(event.widget, 'placeholder', False):
            event.widget.delete(0, tk.END)
            current_theme = style.theme_use()
            entry.config(foreground="black" if current_theme in ["litera", "journal"] else "white")
            entry.placeholder = False

    def on_focus_out(event: tk.Event) -> None:
        if not event.widget.get():
            entry.insert(0, placeholder)
            entry.config(foreground="grey")
            entry.placeholder = True

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


def is_vmd_available() -> bool:
    available = shutil.which("vmd") is not None
    logging.debug(f"VMD availability: {available}")
    return available


def create_info_frame(tab: ttk.Frame, state: 'AnalysisState', load_topology_btn: ttk.Button,
                      load_trajectory_btn: ttk.Button, view_vmd_btn: ttk.Button) -> ttk.LabelFrame:
    info_frame = ttk.Labelframe(tab, text="Info", padding=10)
    info_frame.pack(fill="x", padx=10, pady=5)

    vmd_status_label = ttk.Label(info_frame, text="", bootstyle="secondary")
    vmd_status_label.pack(anchor="w", padx=5, pady=5)

    if is_vmd_available():
        vmd_status_label.config(text="VMD is available in the system path.", bootstyle="success")
    else:
        vmd_status_label.config(
            text="VMD is not configured in the system path. Please configure it before proceeding.",
            bootstyle="danger"
        )
        load_topology_btn.config(state="disabled")
        load_trajectory_btn.config(state="disabled")
        view_vmd_btn.config(state="disabled")
        messagebox.showwarning("VMD Not Found",
                               "VMD is not in the system path. Please configure it before proceeding.",
                               parent=state.root)

    return info_frame


def create_tooltip(widget: tk.Widget, text: str) -> None:
    tooltip = tk.Toplevel(widget, bg="white", padx=5, pady=5)
    tooltip.overrideredirect(True)
    tooltip.withdraw()
    tooltip_label = tk.Label(tooltip, text=text, background="white", foreground="black", wraplength=250)
    tooltip_label.pack()

    def on_enter(event: tk.Event) -> None:
        x = event.widget.winfo_rootx() + 20
        y = event.widget.winfo_rooty() + 20
        tooltip.geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def on_leave(event: tk.Event) -> None:
        tooltip.withdraw()

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


class AnalysisState:
    def __init__(self, root: tk.Tk, style: ttk.Style) -> None:
        self.root = root
        self.style = style
        self.topology_file: Path | None = None
        self.trajectory_file: Path | None = None
        self.working_directory: Path | None = None
        self.reference_file: Path | None = None
        self.time_step = tk.StringVar(value="20")
        self.steps_between_frames = tk.StringVar(value="5000")
        self.atom_selection1: tk.Entry | None = None
        self.atom_selection2: tk.Entry | None = None
        self.atom_selection3: tk.Entry | None = None
        self.rmsd_var = tk.BooleanVar()
        self.rmsf_var = tk.BooleanVar()
        self.rgyr_var = tk.BooleanVar()
        self.sasa_var = tk.BooleanVar()
        self.nativec_var = tk.BooleanVar()
        self.rdf_var = tk.BooleanVar()
        self.report_var = tk.BooleanVar()
        self.out_log_files: list[Path] = []

    def reset(self) -> None:
        self.topology_file = None
        self.trajectory_file = None
        self.working_directory = None
        self.reference_file = None
        self.time_step.set("20")
        self.steps_between_frames.set("5000")

        for atom_selection in [self.atom_selection1, self.atom_selection2, self.atom_selection3]:
            if atom_selection:
                atom_selection.delete(0, tk.END)
                add_placeholder(atom_selection, "Use VMD syntax, e.g., name CA, backbone", self.style)

        self.rmsd_var.set(False)
        self.rmsf_var.set(False)
        self.rgyr_var.set(False)
        self.sasa_var.set(False)
        self.nativec_var.set(False)
        self.rdf_var.set(False)
        self.report_var.set(False)
        self.out_log_files.clear()


def load_topology(state: AnalysisState, button: ttk.Button, label: ttk.Label,
                  load_system_button: ttk.Button, system_loaded_label: ttk.Label) -> None:
    initial_dir = state.working_directory or Path.home()
    file_path = filedialog.askopenfilename(
        initialdir=str(initial_dir),
        filetypes=[("Topology files", "*.*")]
    )
    if file_path:
        state.topology_file = Path(file_path)
        button.config(bootstyle="success solid")
        label.config(text=state.topology_file.name)
        # Restablecer estado a "No system loaded" en rojo
        load_system_button.config(bootstyle="primary solid")
        system_loaded_label.config(text="No system loaded", bootstyle="danger")


def load_trajectory(state: AnalysisState, button: ttk.Button, label: ttk.Label,
                    load_system_button: ttk.Button, system_loaded_label: ttk.Label) -> None:
    initial_dir = state.working_directory or Path.home()
    file_path = filedialog.askopenfilename(
        initialdir=str(initial_dir),
        filetypes=[("Trajectory files", "*.*")]
    )
    if file_path:
        state.trajectory_file = Path(file_path)
        button.config(bootstyle="success solid")
        label.config(text=state.trajectory_file.name)
        # Restablecer estado a "No system loaded" en rojo
        load_system_button.config(bootstyle="primary solid")
        system_loaded_label.config(text="No system loaded", bootstyle="danger")


def load_reference(state: AnalysisState, button: ttk.Button, label: ttk.Label) -> None:
    initial_dir = state.working_directory or Path.home()
    file_path = filedialog.askopenfilename(
        initialdir=str(initial_dir),
        filetypes=[("All files", "*.*")]
    )
    if file_path:
        state.reference_file = Path(file_path)
        button.config(bootstyle="success solid")
        label.config(text=state.reference_file.name)


def open_vmd(state: AnalysisState) -> None:
    if state.topology_file and state.trajectory_file:
        try:
            module_dir = Path(__file__).resolve().parent
            tcl_script_path = module_dir.parent / "TCL" / "sirah_vmdtk.tcl"

            if not tcl_script_path.exists():
                messagebox.showerror("Script Not Found", f"Script not found at: {tcl_script_path}", parent=state.root)
                return

            subprocess.Popen(
                ["vmd", str(state.topology_file), str(state.trajectory_file), "-e", str(tcl_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            messagebox.showerror("VMD Not Found", "VMD is not installed or not found in your system path.", parent=state.root)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while opening VMD: {e}", parent=state.root)
    else:
        messagebox.showwarning("Missing Files", "Please load both topology and trajectory files before opening VMD.", parent=state.root)


def clear_files(state: AnalysisState,
                wd_label: ttk.Label,
                topology_label: ttk.Label,
                trajectory_label: ttk.Label,
                reference_label: ttk.Label,
                set_wd_button: ttk.Button,
                new_dir_button: ttk.Button,
                load_topology_button: ttk.Button,
                load_trajectory_button: ttk.Button,
                set_reference_button: ttk.Button,
                reset_callback: callable) -> None:
    state.reset()
    if reset_callback:
        reset_callback()


def set_working_directory(state: AnalysisState, set_wd_button: ttk.Button,
                          new_dir_button: ttk.Button, wd_label: ttk.Label) -> None:
    directory = filedialog.askdirectory(
        title="Select or Create Working Directory",
        mustexist=True,
        parent=state.root
    )

    if directory:
        state.working_directory = Path(directory)
        set_wd_button.config(bootstyle="success solid")
        wd_label.config(text=str(state.working_directory))
        new_dir_button.config(state="normal")
    else:
        messagebox.showwarning(
            "No Directory Selected",
            "Please select or create a valid working directory.",
            parent=state.root
        )


def create_new_directory(state: AnalysisState, new_dir_button: ttk.Button,
                         wd_label: ttk.Label) -> None:
    initial_dir = state.working_directory

    new_dir_name = simpledialog.askstring(
        "New Directory",
        "Enter new directory name:",
        parent=state.root
    )

    if new_dir_name:
        new_dir_path = initial_dir / new_dir_name
        try:
            new_dir_path.mkdir(parents=True, exist_ok=True)
            state.working_directory = new_dir_path
            wd_label.config(text=str(new_dir_path))
            new_dir_button.config(bootstyle="success solid")
        except OSError as e:
            messagebox.showerror("Error", f"Failed to create directory: {e}", parent=state.root)


def load_system_action(state: AnalysisState, button: ttk.Button, reset_callback: callable,
                       load_topology_button: ttk.Button, topology_label: ttk.Label,
                       load_trajectory_button: ttk.Button, trajectory_label: ttk.Label,
                       system_loaded_label: ttk.Label) -> None:
    valid_topology_exts = {'.psf', '.pdb', '.top', '.tpr', '.prmtop', '.parm7', '.cms', '.gro'}
    valid_trajectory_exts = {'.xtc', '.trr', '.dcd', '.nc', '.mdcrd', '.dtr', '.pdb', '.crd'}

    if state.working_directory is None or state.topology_file is None or state.trajectory_file is None:
        messagebox.showerror("Error", "Please ensure working directory, topology, and trajectory files are loaded before using 'Load System'.", parent=state.root)
        return

    topo_ext = state.topology_file.suffix.lower()
    traj_ext = state.trajectory_file.suffix.lower()

    if topo_ext not in valid_topology_exts:
        messagebox.showerror("Invalid Topology File",
                             f"The chosen topology file '{state.topology_file.name}' is not a recognized topology format.\nAllowed: {', '.join(valid_topology_exts)}",
                             parent=state.root)
        load_topology_button.config(bootstyle="primary solid")
        topology_label.config(text="Not loaded")
        state.topology_file = None
        return

    if traj_ext not in valid_trajectory_exts:
        messagebox.showerror("Invalid Trajectory File",
                             f"The chosen trajectory file '{state.trajectory_file.name}' is not a recognized trajectory format.\nAllowed: {', '.join(valid_trajectory_exts)}",
                             parent=state.root)
        load_trajectory_button.config(bootstyle="primary solid")
        trajectory_label.config(text="Not loaded")
        state.trajectory_file = None
        return

    if not reset_callback:
        messagebox.showerror("Error", "No reset callback provided to reset other tabs.", parent=state.root)
        return

    reset_callback()
    button.config(bootstyle="success solid")
    messagebox.showinfo("System Loaded", "The system has been loaded successfully.", parent=state.root)
    system_loaded_label.config(text="System Loaded", bootstyle="success")


def create_load_files_tab(tab: ttk.Frame, state: AnalysisState, reset_callback: callable) -> callable:
    if reset_callback is None:
        raise ValueError("reset_callback must be provided")

    file_frame = ttk.Labelframe(tab, text="Load Files", padding=10)
    file_frame.pack(fill="x", padx=10, pady=5)

    # Working Directory Frame
    wd_frame = ttk.Frame(file_frame)
    wd_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))

    set_wd_button = ttk.Button(
        wd_frame,
        text="Set Working Directory",
        command=lambda: set_working_directory(state, set_wd_button, new_dir_button, wd_label),
        bootstyle="primary solid",
        width=30,
    )
    set_wd_button.grid(row=0, column=0, padx=5, sticky="w")

    help_label_wd = ttk.Label(
        wd_frame,
        text="i",
        font=("Times", 14, "bold italic"),
        foreground="gray",
        cursor="hand2",
    )
    help_label_wd.grid(row=0, column=1, padx=5)
    create_tooltip(help_label_wd, "Set the working directory for your analysis.")

    wd_label = ttk.Label(wd_frame, text="Not set", bootstyle="secondary")
    wd_label.grid(row=0, column=2, padx=5, sticky="w")

    new_dir_button = ttk.Button(
        wd_frame,
        text="New Directory",
        command=lambda: create_new_directory(state, new_dir_button, wd_label),
        bootstyle="primary solid",
        width=30,
        state="disabled",
    )
    new_dir_button.grid(row=1, column=0, padx=5, pady=(5, 0), sticky="w")

    # Topology File Frame (Set Topology)
    topo_frame = ttk.Frame(file_frame)
    topo_frame.grid(row=1, column=0, sticky="w", pady=(0, 5))

    load_topology_button = ttk.Button(
        topo_frame,
        text="Set Topology",
        bootstyle="primary solid",
        width=30,
    )
    load_topology_button.grid(row=0, column=0, padx=5, sticky="w")

    help_label_topo = ttk.Label(
        topo_frame,
        text="i",
        font=("Times", 14, "bold italic"),
        foreground="gray",
        cursor="hand2",
    )
    help_label_topo.grid(row=0, column=1, padx=5)
    create_tooltip(help_label_topo, "Set the topology file for your analysis.")

    topology_label = ttk.Label(topo_frame, text="Not loaded", bootstyle="secondary")
    topology_label.grid(row=0, column=2, padx=5, sticky="w")

    # Trajectory File Frame (Set Trajectory)
    traj_frame = ttk.Frame(file_frame)
    traj_frame.grid(row=2, column=0, sticky="w", pady=(0, 5))

    load_trajectory_button = ttk.Button(
        traj_frame,
        text="Set Trajectory",
        bootstyle="primary solid",
        width=30,
    )
    load_trajectory_button.grid(row=0, column=0, padx=5, sticky="w")

    help_label_traj = ttk.Label(
        traj_frame,
        text="i",
        font=("Times", 14, "bold italic"),
        foreground="gray",
        cursor="hand2",
    )
    help_label_traj.grid(row=0, column=1, padx=5)
    create_tooltip(help_label_traj, "Set the trajectory file for your analysis.")

    trajectory_label = ttk.Label(traj_frame, text="Not loaded", bootstyle="secondary")
    trajectory_label.grid(row=0, column=2, padx=5, sticky="w")

    # Load System Button
    load_system_button = ttk.Button(
        traj_frame,
        text="Load System",
        bootstyle="primary solid",
        width=30,
    )
    load_system_button.grid(row=1, column=0, padx=5, pady=(5, 0), sticky="w")

    # Etiqueta para el estado del sistema (por defecto "No system loaded" en rojo)
    system_loaded_label = ttk.Label(traj_frame, text="No system loaded", bootstyle="danger")
    system_loaded_label.grid(row=1, column=2, padx=5, sticky="w")

    # Configurar comandos
    load_topology_button.config(
        command=lambda: load_topology(state, load_topology_button, topology_label, load_system_button, system_loaded_label)
    )
    load_trajectory_button.config(
        command=lambda: load_trajectory(state, load_trajectory_button, trajectory_label, load_system_button, system_loaded_label)
    )
    load_system_button.config(
        command=lambda: load_system_action(state,
                                           load_system_button,
                                           reset_callback,
                                           load_topology_button, topology_label,
                                           load_trajectory_button, trajectory_label,
                                           system_loaded_label)
    )

    # Optional Parameters Frame
    optional_frame = ttk.Labelframe(tab, text="Optional", padding=10)
    optional_frame.pack(fill="x", padx=10, pady=5)

    # Reference File Frame
    ref_frame = ttk.Frame(optional_frame)
    ref_frame.pack(fill="x", pady=5)

    set_reference_button = ttk.Button(
        ref_frame,
        text="Set Reference Structure",
        command=lambda: load_reference(state, set_reference_button, reference_label),
        bootstyle="primary solid",
        width=30,
    )
    set_reference_button.grid(row=0, column=0, padx=5, sticky="w")

    help_label_ref = ttk.Label(
        ref_frame,
        text="i",
        font=("Times", 14, "bold italic"),
        foreground="gray",
        cursor="hand2",
    )
    help_label_ref.grid(row=0, column=1, padx=5)
    create_tooltip(help_label_ref, "Set a reference structure for the analysis.")

    reference_label = ttk.Label(ref_frame, text="Not loaded", bootstyle="secondary")
    reference_label.grid(row=0, column=2, padx=5, sticky="w")

    # Simulation Parameters Frame
    time_step_frame = ttk.Frame(optional_frame)
    time_step_frame.pack(fill="x", pady=5)

    time_step_label = ttk.Label(time_step_frame, text="Time Step (fs)")
    time_step_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

    time_step_entry = ttk.Entry(time_step_frame, width=10, textvariable=state.time_step)
    time_step_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    help_label_time_step = ttk.Label(
        time_step_frame,
        text="i",
        font=("Times", 14, "bold italic"),
        foreground="gray",
        cursor="hand2",
    )
    help_label_time_step.grid(row=0, column=2, padx=5)
    create_tooltip(help_label_time_step, "Time step for the simulation analysis in femtoseconds.")

    steps_label = ttk.Label(time_step_frame, text="Steps Between Frames")
    steps_label.grid(row=0, column=3, padx=5, pady=5, sticky="e")

    steps_entry = ttk.Entry(time_step_frame, width=10, textvariable=state.steps_between_frames)
    steps_entry.grid(row=0, column=4, padx=5, pady=5, sticky="w")

    help_label_steps = ttk.Label(
        time_step_frame,
        text="i",
        font=("Times", 14, "bold italic"),
        foreground="gray",
        cursor="hand2",
    )
    help_label_steps.grid(row=0, column=5, padx=5)
    create_tooltip(help_label_steps, "Number of steps between frames for analysis.")

    # Control Buttons Frame
    buttons_frame = ttk.Frame(tab)
    buttons_frame.pack(fill="x", pady=(10, 5))

    buttons_inner_frame = ttk.Frame(buttons_frame)
    buttons_inner_frame.pack(expand=True)

    view_vmd_button = ttk.Button(
        buttons_inner_frame,
        text="View in VMD",
        command=lambda: open_vmd(state),
        bootstyle="info solid",
        width=15,
        padding=(10, 10)
    )
    view_vmd_button.pack(side="left", padx=10)

    def reset_tab():
        wd_label.config(text="Not set")
        set_wd_button.config(bootstyle="primary solid")
        new_dir_button.config(state="disabled", bootstyle="primary solid")

        topology_label.config(text="Not loaded")
        load_topology_button.config(bootstyle="primary solid")

        trajectory_label.config(text="Not loaded")
        load_trajectory_button.config(bootstyle="primary solid")

        reference_label.config(text="Not loaded")
        set_reference_button.config(bootstyle="primary solid")

        state.time_step.set("20")
        state.steps_between_frames.set("5000")

        if is_vmd_available():
            view_vmd_button.config(state="normal", bootstyle="info solid")
        else:
            view_vmd_button.config(state="disabled", bootstyle="disabled")

        load_system_button.config(bootstyle="primary solid")
        system_loaded_label.config(text="No system loaded", bootstyle="danger")

        img_canvas.delete("all")
        resize_image(width=img_canvas.winfo_width(), height=img_canvas.winfo_height())

    reset_button = ttk.Button(
        buttons_inner_frame,
        text="Reset",
        command=lambda: clear_files(
            state,
            wd_label,
            topology_label,
            trajectory_label,
            reference_label,
            set_wd_button,
            new_dir_button,
            load_topology_button,
            load_trajectory_button,
            set_reference_button,
            reset_tab
        ),
        bootstyle="danger solid",
        width=15,
        padding=(10, 10)
    )
    reset_button.pack(side="left", padx=10)

    info_frame = create_info_frame(tab, state, load_topology_button, load_trajectory_button, view_vmd_button)

    img_frame = ttk.Frame(tab)
    img_frame.pack(expand=True, fill="both")

    module_dir = Path(__file__).resolve().parent
    img_path = module_dir.parent / "img" / "sirahtools-logo.png"

    if not img_path.exists():
        messagebox.showerror("Image Load Error", f"Image not found at: {img_path}", parent=state.root)
        logging.error(f"Image not found at: {img_path}")
        return

    try:
        original_image = Image.open(img_path)
        logging.info(f"Image loaded successfully from: {img_path}")
    except Exception as e:
        messagebox.showerror("Image Load Error", f"Failed to load image: {e}", parent=state.root)
        logging.exception("Failed to load image.")
        return

    img_photo = None

    def resize_image(event: tk.Event = None, width: int = None, height: int = None) -> None:
        nonlocal img_photo
        if event:
            canvas_width = event.width
            canvas_height = event.height
        else:
            canvas_width = width if width else img_canvas.winfo_width()
            canvas_height = height if height else img_canvas.winfo_height()

        if canvas_width <= 0 or canvas_height <= 0:
            return

        new_width = max(int(canvas_width * 0.8), 1)
        new_height = max(int(canvas_height * 0.8), 1)

        try:
            resized_image = original_image.copy()
            resized_image.thumbnail((new_width, new_height), Image.LANCZOS)
            img_photo = ImageTk.PhotoImage(resized_image)
            img_canvas.delete("all")
            x = (canvas_width - resized_image.width) // 2
            y = (canvas_height - resized_image.height) // 2
            img_canvas.create_image(x, y, anchor="nw", image=img_photo)
        except Exception as e:
            logging.exception("Error during image resizing.")

    img_canvas = tk.Canvas(img_frame, bg="white")
    img_canvas.pack(expand=True, fill="both")
    img_canvas.bind("<Configure>", resize_image)
    img_canvas.after(100, lambda: resize_image(width=img_canvas.winfo_width(), height=img_canvas.winfo_height()))

    return reset_tab
