import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import time
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF

def clear_entry(event):
    widget = event.widget
    if widget.get() == "Use VMD syntax, e.g., name CA, backbone":
        widget.delete(0, tk.END)
        widget.config(foreground="black")  # Cambia el color del texto a negro

def create_tooltip(widget, text):
    tooltip = tk.Toplevel(widget, bg="white", padx=5, pady=5)
    tooltip.overrideredirect(True)
    tooltip.withdraw()
    tooltip_label = tk.Label(tooltip, text=text, background="white", foreground="black", wraplength=250)
    tooltip_label.pack()

    def on_enter(event):
        x = event.widget.winfo_rootx() + 20
        y = event.widget.winfo_rooty() + 20
        tooltip.geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def on_leave(event):
        tooltip.withdraw()

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def choose_engine(state):
    state.sim_type = state.engine_var.get().upper()
    engine_settings = {
        "AMBER": ("parm7", "netcdf"),
        "GROMACS": ("gro", "xtc"),
        "NAMD": ("psf", "dcd")
    }
    state.topology_type, state.trajectory_type = engine_settings.get(state.sim_type, (None, None))

def load_topology(state, button):
    if state.topology_type is None:
        messagebox.showerror("Error", "Please choose a simulation engine before loading the topology file.")
        return

    state.topology_file = filedialog.askopenfilename(
        filetypes=[(f"{state.topology_type.upper()} files", f"*.{state.topology_type}")])
    if state.topology_file:
        button.config(text=os.path.basename(state.topology_file))

def load_trajectory(state, button):
    if state.trajectory_type is None:
        messagebox.showerror("Error", "Please choose a simulation engine before loading the trajectory file.")
        return

    filetypes = [("Trajectory files", "*.nc *.crd *.xtc *.dcd")]
    state.trajectory_file = filedialog.askopenfilename(filetypes=filetypes)
    if state.trajectory_file:
        button.config(text=os.path.basename(state.trajectory_file))

def analyze(state):
    # Código para el análisis
    pass  # Coloca aquí el código de la función analyze

def wait_for_files(state, selection1_clean, selection2_clean, selection3_clean, analysis_code):
    # Código para esperar los archivos
    pass  # Coloca aquí el código de la función wait_for_files

def plot_contacts(state, data_file, output_file_prefix):
    # Código para graficar contactos
    pass  # Coloca aquí el código de la función plot_contacts

def plot_rdf(state, data_file, output_file_prefix):
    # Código para graficar RDF
    pass  # Coloca aquí el código de la función plot_rdf

def plot_generic(state, data_file, x_label, y_label, title, output_file_prefix):
    # Código para graficar genérico
    pass  # Coloca aquí el código de la función plot_generic

def generate_pdf(state, pdf_filename, selection1, selection2, selection3):
    # Código para generar PDF
    pass  # Coloca aquí el código de la función generate_pdf

def mark_completed(var):
    var.set(True)

def open_vmd(state):
    if not state.topology_file or not state.trajectory_file:
        messagebox.showerror("Error", "Please load both topology and trajectory files before opening VMD.")
        return

    try:
        subprocess.run(["vmd", state.topology_file, state.trajectory_file])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open VMD: {str(e)}")
