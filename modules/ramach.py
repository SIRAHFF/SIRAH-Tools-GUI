# -*- coding: utf-8 -*-

"""
Ramachandran Plot Visualization Tool
------------------------------------

A Python GUI application for visualizing Ramachandran plots based on PSI and PHI angle data from molecular simulations.

Version: 1.0.0
Authors: SIRAH TEAM <sirahff.com>
Date: October 8, 2024

Features:
- Load PSI and PHI angle data matrices.
- Visualize Ramachandran plots for individual frames.
- Display histograms of Φ (Phi) and Ψ (Psi) angles per frame or per residue.
- Interactive plot with hover functionality to display residue information.
- Toggle density background based on all frames (when multiple frames are available).
- Save plots and histograms in various formats (PNG, JPG, PDF, etc.).
- Compatible with single-frame and multi-frame datasets.
- Reset functionality to restore the application to its initial state.
- **New Feature:** The "Go to Frame" entry now updates the plot immediately when its value changes and displays an error message if the input is invalid.
- **New Feature:** The frame slider and "Go to Frame" entry are always visible but only enabled after loading the data.
- **New Feature:** Added a "Hide Ramach" button to toggle the visibility of the scatter plot.
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttkb
from ttkbootstrap import Window
from ttkbootstrap.dialogs import Messagebox, Querybox
from ttkbootstrap.constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import colors
import numpy as np
import matplotlib.pyplot as plt

# Version and authorship information
__version__ = "1.0.0"
__author__ = "SIRAH TEAM <sirahff.com>"

# Custom toolbar class without the 'Save' icon
class CustomToolbar(NavigationToolbar2Tk):
    """
    A custom toolbar for the Matplotlib figure, excluding the 'Save' button.
    """
    # Remove the 'Save' tool item from the toolbar
    toolitems = [
        t for t in NavigationToolbar2Tk.toolitems if t[0] != 'Save'
    ]

class RamachandranApp:
    """
    A GUI application for visualizing Ramachandran plots based on PSI and PHI angle data.
    """
    def __init__(self, root):
        """
        Initialize the application with the main window and UI components.

        Args:
            root (tk.Tk): The root window of the Tkinter application.
        """
        self.root = root
        self.root.title("Ramachandran Plot Visualization Tool")

        # Data matrices and flags
        self.psi_matrix = None          # Matrix to store PSI angles
        self.phi_matrix = None          # Matrix to store PHI angles
        self.all_phi = None             # Flattened PHI angles for all frames
        self.all_psi = None             # Flattened PSI angles for all frames
        self.density_displayed = False  # Flag to control density plot display
        self.hist_fig = None            # Figure for histograms (per frame)
        self.ax_hist_phi = None         # Axis for the PHI histogram (per frame)
        self.ax_hist_psi = None         # Axis for the PSI histogram (per frame)
        self.hist_canvas = None         # Canvas for the histograms (per frame)
        self.hist_window_open = False   # Flag to track if histogram window is open
        self.single_frame = False       # Flag to detect if the data has only one frame
        self.scatter = None             # Reference to the scatter plot
        self.scatter_visible = True     # Flag to track visibility of scatter plot

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        """
        Configure custom styles for the UI elements using ttkbootstrap.
        """
        self.style = ttkb.Style()
        button_font = ('', 11)  # Font for buttons
        label_font = ('', 11, 'bold')  # Bold font for labels
        entry_font = ('', 11, 'bold')  # Bold font for entries

        # Apply font to base styles
        self.style.configure('TButton', font=button_font)
        self.style.configure('TLabel', font=label_font)
        self.style.configure('TEntry', font=entry_font)
        self.style.configure('Error.TLabel', font=entry_font, foreground='red')  # Style for error messages

    def setup_ui(self):
        """
        Set up the user interface components.
        """
        # Main frame to hold all widgets
        self.main_frame = ttkb.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame for control buttons at the top
        self.frame_controls = ttkb.Frame(self.main_frame)
        self.frame_controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Load PSI button
        self.psi_button = ttkb.Button(
            self.frame_controls,
            text="Load PSI",
            command=self.load_psi_file,
            bootstyle="warning"
        )
        self.psi_button.grid(row=0, column=0, padx=10, pady=5)

        # Load PHI button
        self.phi_button = ttkb.Button(
            self.frame_controls,
            text="Load PHI",
            command=self.load_phi_file,
            bootstyle="warning"
        )
        self.phi_button.grid(row=0, column=1, padx=10, pady=5)

        # Show/Hide Density button
        self.show_density_button = ttkb.Button(
            self.frame_controls,
            text="Show Density",
            command=self.toggle_density,
            bootstyle="secondary",
            state='disabled'  # Initially disabled
        )
        self.show_density_button.grid(row=0, column=2, padx=10, pady=5)

        # Hide Ramach button
        self.hide_ramach_button = ttkb.Button(
            self.frame_controls,
            text="Hide Ramach",
            command=self.toggle_scatter_plot,
            bootstyle="secondary",
            state='disabled'  # Initially disabled
        )
        self.hide_ramach_button.grid(row=0, column=3, padx=10, pady=5)

        # Histogram per Frame button
        self.plot_histograms_button = ttkb.Button(
            self.frame_controls,
            text="Histogram per Frame",
            command=self.show_histograms,
            bootstyle="secondary",
            state='disabled'  # Initially disabled
        )
        self.plot_histograms_button.grid(row=0, column=4, padx=10, pady=5)

        # Histogram per Residue button
        self.histogram_res_button = ttkb.Button(
            self.frame_controls,
            text="Histogram per Residue",
            command=self.show_histograms_per_res,
            bootstyle="secondary"
        )
        self.histogram_res_button.grid(row=0, column=5, padx=10, pady=5)

        # Ramachandran per Residue button
        self.ramach_res_button = ttkb.Button(
            self.frame_controls,
            text="Ramachandran per Residue",
            command=self.show_ramachandran_per_res,
            bootstyle="secondary"
        )
        self.ramach_res_button.grid(row=0, column=6, padx=10, pady=5)

        # Frame slider label
        self.frame_slider_label = ttkb.Label(
            self.frame_controls,
            text="Frame"
        )
        self.frame_slider_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")

        # Frame slider
        self.frame_slider = ttkb.Scale(
            self.frame_controls,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            command=self.on_frame_change,
            state='disabled'  # Initially disabled
        )
        self.frame_slider.grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky="ew")

        # Frame entry label
        self.frame_entry_label = ttkb.Label(
            self.frame_controls,
            text="Go to Frame:"
        )
        self.frame_entry_label.grid(row=1, column=5, padx=5, pady=5, sticky="e")

        # Frame entry (Entry Widget with StringVar)
        self.frame_entry_var = tk.StringVar()
        self.frame_entry = ttkb.Entry(
            self.frame_controls,
            width=10,
            textvariable=self.frame_entry_var,
            state='disabled'  # Initially disabled
        )
        self.frame_entry.grid(row=1, column=6, padx=5, pady=5, sticky="w")
        # Bind the variable trace to update the plot when the value changes
        self.frame_entry_var.trace_add('write', self.on_frame_entry_change)

        # Error message label for frame entry
        self.frame_error_label = ttkb.Label(
            self.frame_controls,
            text="",
            style='Error.TLabel'
        )
        self.frame_error_label.grid(row=1, column=7, padx=5, pady=5, sticky="w")

        # Middle frame to hold the canvas and side widgets
        self.middle_frame = ttkb.Frame(self.main_frame)
        self.middle_frame.pack(fill=tk.BOTH, expand=True)

        # Frame for entries and buttons on the right
        right_frame = ttkb.Frame(self.middle_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=10)

        # Entries frame inside the right frame
        entries_frame = ttkb.Frame(right_frame)
        entries_frame.pack(side=tk.TOP, fill=tk.Y, padx=5, pady=5)

        # Residue label and entry
        res_label = ttkb.Label(entries_frame, text="Residue:")
        res_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.res_entry = ttkb.Entry(entries_frame, width=10, state='readonly')
        self.res_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Psi angle label and entry
        psi_label = ttkb.Label(entries_frame, text="Psi:")
        psi_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.psi_entry = ttkb.Entry(entries_frame, width=10, state='readonly')
        self.psi_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Phi angle label and entry
        phi_label = ttkb.Label(entries_frame, text="Phi:")
        phi_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.phi_entry = ttkb.Entry(entries_frame, width=10, state='readonly')
        self.phi_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Chain length label and entry
        len_chain_label = ttkb.Label(entries_frame, text="Chain Length:")
        len_chain_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.len_chain_entry = ttkb.Entry(entries_frame, width=10, state='readonly')
        self.len_chain_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Frame for Save and Reset buttons inside right frame
        buttons_frame = ttkb.Frame(right_frame)
        buttons_frame.pack(side=tk.TOP, fill=tk.X, pady=20)

        # Save Plot button
        self.save_plot_button = ttkb.Button(
            buttons_frame,
            text="Save Plot",
            command=self.save_plot,
            bootstyle="info"
        )
        self.save_plot_button.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)

        # Reset button
        self.reset_button = ttkb.Button(
            buttons_frame,
            text="Reset",
            command=self.reset_app,
            bootstyle="danger"
        )
        self.reset_button.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)

        # Frame for the canvas and toolbar on the left
        canvas_frame = ttkb.Frame(self.middle_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Main plot figure and canvas
        # Reduce the figure size by 30%
        original_figsize = (8, 6)
        reduced_figsize = (original_figsize[0] * 0.7, original_figsize[1] * 0.7)
        self.fig, self.ax = plt.subplots(figsize=reduced_figsize)
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toolbar for the plot
        toolbar = CustomToolbar(self.canvas, canvas_frame)
        toolbar.update()
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def update_ui_for_single_frame(self):
        """
        Update the UI components based on whether the data has a single frame.
        Disable or hide elements that depend on multiple frames if necessary.
        """
        if self.single_frame:
            # Disable the frame slider and entry
            self.frame_slider.config(state='disabled')
            self.frame_entry.config(state='disabled')
            # Disable buttons that require multiple frames
            self.plot_histograms_button.configure(state='disabled')
            self.show_density_button.configure(state='disabled')
            self.hide_ramach_button.configure(state='normal')  # Enable the button
        else:
            # Enable the frame slider and entry
            self.frame_slider.config(state='normal')
            self.frame_entry.config(state='normal')
            # Enable buttons
            self.plot_histograms_button.configure(state='normal')
            self.show_density_button.configure(state='normal')
            self.hide_ramach_button.configure(state='normal')

    def load_matrix(self, filepath):
        """
        Load a matrix from a file, ensuring it is two-dimensional.

        Args:
            filepath (str): Path to the file to load.

        Returns:
            numpy.ndarray: The loaded matrix, or None if loading failed.
        """
        try:
            # Load the data, skipping comments and headers
            matrix = np.loadtxt(filepath, comments='#', skiprows=2)
            if matrix is not None:
                # Ensure the matrix is 2D
                if matrix.ndim == 1:
                    matrix = matrix[np.newaxis, :]
                # Display the chain length, ignoring the first column
                self.len_chain_entry.config(state='normal')
                self.len_chain_entry.delete(0, tk.END)
                self.len_chain_entry.insert(0, matrix.shape[1] - 1)
                self.len_chain_entry.config(state='readonly')
            return matrix
        except Exception as e:
            Messagebox.show_error(
                title="File Loading Error",
                message=f"Could not load the file: {e}"
            )
            return None

    def load_psi_file(self):
        """
        Prompt the user to select and load a PSI matrix file.
        """
        filepath = filedialog.askopenfilename(title="Select the PSI matrix file")
        if filepath:
            self.psi_matrix = self.load_matrix(filepath)
            if self.psi_matrix is not None:
                self.psi_button.configure(bootstyle="success")
                self.check_matrices()
        else:
            Messagebox.show_info(
                title="No File Selected",
                message="No PSI file was selected."
            )

    def load_phi_file(self):
        """
        Prompt the user to select and load a PHI matrix file.
        """
        filepath = filedialog.askopenfilename(title="Select the PHI matrix file")
        if filepath:
            self.phi_matrix = self.load_matrix(filepath)
            if self.phi_matrix is not None:
                self.phi_button.configure(bootstyle="success")
                self.check_matrices()
        else:
            Messagebox.show_info(
                title="No File Selected",
                message="No PHI file was selected."
            )

    def check_matrices(self):
        """
        Check if both PSI and PHI matrices are loaded and update the plot accordingly.
        """
        if self.psi_matrix is not None and self.phi_matrix is not None:
            # Determine if there is only one frame
            if self.psi_matrix.shape[0] == 1:
                self.single_frame = True
            else:
                self.single_frame = False

            self.update_ui_for_single_frame()

            # Flatten the matrices, ignoring the first column
            self.all_phi = self.phi_matrix[:, 1:].flatten()
            self.all_psi = self.psi_matrix[:, 1:].flatten()
            self.update_plot(0)
            if not self.single_frame:
                max_frame = self.psi_matrix.shape[0] - 1
                self.frame_slider.config(to=max_frame)
                self.frame_entry_var.set("0")
            else:
                self.frame_slider.config(to=0)
        else:
            Messagebox.show_warning(
                title="Warning",
                message="Make sure to load both PSI and PHI files."
            )

    def calculate_histograms(self, frame_index):
        """
        Calculate and display histograms for a specific frame.

        Args:
            frame_index (int): The index of the frame to use.
        """
        if self.single_frame:
            return  # Do nothing for single-frame data
        if self.psi_matrix is not None and self.phi_matrix is not None:
            # Ignore the first column
            psi = self.psi_matrix[frame_index, 1:]
            phi = self.phi_matrix[frame_index, 1:]
            mask = (phi != 0) & (psi != 0)
            phi = phi[mask]
            psi = psi[mask]

            if self.ax_hist_phi is not None and self.ax_hist_psi is not None:
                self.ax_hist_phi.clear()
                self.ax_hist_psi.clear()

                self.ax_hist_phi.hist(phi, bins=30, color='#1E88E5', alpha=0.7, range=(-180, 180))
                self.ax_hist_psi.hist(psi, bins=30, color='#43A047', alpha=0.7, range=(-180, 180))

                self.ax_hist_phi.set_xlim(-180, 180)
                self.ax_hist_psi.set_xlim(-180, 180)
                self.ax_hist_phi.set_xticks(np.arange(-180, 181, 60))
                self.ax_hist_psi.set_xticks(np.arange(-180, 181, 60))

                self.ax_hist_phi.set_title(f'Frame {frame_index}: $\Phi$')
                self.ax_hist_psi.set_title(f'Frame {frame_index}: $\Psi$')

                self.ax_hist_phi.set_xlabel(r'$\Phi$ (°)')
                self.ax_hist_psi.set_xlabel(r'$\Psi$ (°)')
                self.ax_hist_phi.set_ylabel('Counts')
                self.ax_hist_psi.set_ylabel('')

                self.hist_canvas.draw()

    def calculate_histograms_residue(self, residue_index, ax_hist_phi, ax_hist_psi, hist_canvas):
        """
        Calculate and display histograms for a specific residue across all frames.

        Args:
            residue_index (int): The index of the residue to use.
            ax_hist_phi (matplotlib.axes.Axes): The axes for the PHI histogram.
            ax_hist_psi (matplotlib.axes.Axes): The axes for the PSI histogram.
            hist_canvas (FigureCanvasTkAgg): The canvas to draw the histograms on.
        """
        if self.psi_matrix is not None and self.phi_matrix is not None:
            # Ignore the first column
            psi = self.psi_matrix[:, residue_index + 1]
            phi = self.phi_matrix[:, residue_index + 1]
            mask = (phi != 0) & (psi != 0)
            phi = phi[mask]
            psi = psi[mask]

            ax_hist_phi.clear()
            ax_hist_psi.clear()

            ax_hist_phi.hist(phi, bins=30, color='#1E88E5', alpha=0.7, range=(-180, 180))
            ax_hist_psi.hist(psi, bins=30, color='#43A047', alpha=0.7, range=(-180, 180))

            ax_hist_phi.set_xlim(-180, 180)
            ax_hist_psi.set_xlim(-180, 180)
            ax_hist_phi.set_xticks(np.arange(-180, 181, 60))
            ax_hist_psi.set_xticks(np.arange(-180, 181, 60))

            ax_hist_phi.set_title(f'Residue {residue_index + 1}: $\Phi$')
            ax_hist_psi.set_title(f'Residue {residue_index + 1}: $\Psi$')

            ax_hist_phi.set_xlabel(r'$\Phi$ (°)')
            ax_hist_psi.set_xlabel(r'$\Psi$ (°)')
            ax_hist_phi.set_ylabel('Counts')
            ax_hist_psi.set_ylabel('')

            hist_canvas.draw()

    def show_histograms(self):
        """
        Display histograms for the current frame in a new window.
        """
        # Check if data is loaded
        if self.psi_matrix is None or self.phi_matrix is None:
            Messagebox.show_error(
                title="Error",
                message="Please load both PSI and PHI matrices first."
            )
            return

        if self.single_frame:
            Messagebox.show_info(
                title="Information",
                message="Histograms per frame are not available for single-frame data."
            )
            return

        # Create a new window for the histograms
        hist_window = ttkb.Toplevel(self.root)
        hist_window.title("Histograms per Frame")
        hist_window.geometry("800x800")

        # Set flag to indicate histogram window is open
        self.hist_window_open = True

        # Handle window close event to reset flag
        def on_close():
            self.hist_window_open = False
            hist_window.destroy()

        hist_window.protocol("WM_DELETE_WINDOW", on_close)

        # Save Histograms button
        save_hist_button = ttkb.Button(
            hist_window,
            text="Save Histograms",
            command=self.save_histograms,
            bootstyle="secondary"
        )
        save_hist_button.pack(side=tk.TOP, padx=10, pady=5)

        # Create figures for the histograms
        # Reduce the figure size by 30%
        original_hist_figsize = (8, 6)
        reduced_hist_figsize = (original_hist_figsize[0] * 0.7, original_hist_figsize[1] * 0.7)
        self.hist_fig, (self.ax_hist_phi, self.ax_hist_psi) = plt.subplots(1, 2, figsize=reduced_hist_figsize)
        self.ax_hist_phi.set_xlim(-180, 180)
        self.ax_hist_psi.set_xlim(-180, 180)
        self.ax_hist_phi.set_xticks(np.arange(-180, 181, 60))
        self.ax_hist_psi.set_xticks(np.arange(-180, 181, 60))

        self.ax_hist_phi.set_xlabel(r'$\Phi$ (°)')
        self.ax_hist_psi.set_xlabel(r'$\Psi$ (°)')
        self.ax_hist_phi.set_ylabel('Counts')
        self.ax_hist_psi.set_ylabel('')

        # Create canvas for the histograms
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=hist_window)
        self.hist_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Calculate and display the histograms for the current frame
        frame_index = int(self.frame_slider.get())
        self.calculate_histograms(frame_index)

    def show_histograms_per_res(self):
        """
        Display histograms for a specific residue across all frames in a new window.
        """
        if self.psi_matrix is None or self.phi_matrix is None:
            Messagebox.show_error(
                title="Error",
                message="Please load both PSI and PHI matrices first."
            )
            return

        # Prompt user for residue index
        residue_index = Querybox.get_integer(
            title="Residue Index",
            prompt="Enter residue index (starting from 1):",
            parent=self.root
        )
        if residue_index is None:
            return
        residue_index -= 1  # Adjust for zero-based indexing
        if residue_index < 0 or residue_index >= self.psi_matrix.shape[1] - 1:
            Messagebox.show_error(
                title="Error",
                message="Invalid residue index."
            )
            return

        # Create a new window for the histograms
        hist_window = ttkb.Toplevel(self.root)
        hist_window.title(f"Histograms for Residue {residue_index + 1}")
        hist_window.geometry("800x600")

        # Create figures for the histograms
        # Reduce the figure size by 30%
        original_hist_figsize = (8, 6)
        reduced_hist_figsize = (original_hist_figsize[0] * 0.7, original_hist_figsize[1] * 0.7)
        hist_fig, (ax_hist_phi, ax_hist_psi) = plt.subplots(1, 2, figsize=reduced_hist_figsize)
        ax_hist_phi.set_xlim(-180, 180)
        ax_hist_psi.set_xlim(-180, 180)
        ax_hist_phi.set_xticks(np.arange(-180, 181, 60))
        ax_hist_psi.set_xticks(np.arange(-180, 181, 60))

        ax_hist_phi.set_xlabel(r'$\Phi$ (°)')
        ax_hist_psi.set_xlabel(r'$\Psi$ (°)')
        ax_hist_phi.set_ylabel('Counts')
        ax_hist_psi.set_ylabel('')

        # Create canvas for the histograms
        hist_canvas = FigureCanvasTkAgg(hist_fig, master=hist_window)
        hist_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Save Histograms button
        def save_histograms():
            """
            Save the currently displayed histograms to a file.
            """
            # Prompt user for file format
            file_format = Querybox.get_string(
                title="Format",
                prompt="Enter the format (png, jpg, pdf, etc.):",
                initialvalue="png"
            )
            if not file_format:
                return

            # Prompt user for DPI
            dpi = Querybox.get_integer(
                title="DPI",
                prompt="Enter DPI (resolution):",
                initialvalue=300,
                minvalue=1
            )

            # Ask for save location
            save_path = filedialog.asksaveasfilename(
                defaultextension=f".{file_format}",
                filetypes=[(f"{file_format.upper()} files", f"*.{file_format}")]
            )
            if save_path:
                hist_fig.savefig(save_path, format=file_format, dpi=dpi)
                Messagebox.show_info(
                    title="Save Successful",
                    message=f"Histograms saved as {save_path}"
                )

        save_hist_button = ttkb.Button(
            hist_window,
            text="Save Histograms",
            command=save_histograms,
            bootstyle="secondary"
        )
        save_hist_button.pack(side=tk.TOP, padx=10, pady=5)

        # Calculate and display the histograms for the selected residue
        self.calculate_histograms_residue(residue_index, ax_hist_phi, ax_hist_psi, hist_canvas)

    def plot_density_background(self):
        """
        Plot the density background based on all frames for the density visualization.
        """
        if self.all_phi is not None and self.all_psi is not None:
            self.ax.hist2d(
                self.all_phi,
                self.all_psi,
                bins=75,
                range=[[-180, 180], [-180, 180]],
                cmap='GnBu',
                norm=colors.LogNorm(),
                alpha=0.5
            )

    def update_plot(self, frame_index):
        """
        Update the main Ramachandran plot based on the selected frame.

        Args:
            frame_index (int): The index of the frame to plot.
        """
        if self.single_frame:
            frame_index = 0
        else:
            frame_index = int(frame_index)

        if self.psi_matrix is not None and self.phi_matrix is not None:
            # Ignore the first column
            psi = self.psi_matrix[frame_index, 1:]
            phi = self.phi_matrix[frame_index, 1:]
            mask = (phi != 0) & (psi != 0)
            phi = phi[mask]
            psi = psi[mask]

            # Clear the previous plot
            self.ax.clear()
            self.ax.set_facecolor('white')
            self.ax.set_xlabel(r'$\Phi$ (°)')
            self.ax.set_ylabel(r'$\Psi$ (°)')
            self.ax.set_xlim([-180, 180])
            self.ax.set_ylim([-180, 180])
            self.ax.axhline(0, color='gray', linestyle='--')
            self.ax.axvline(0, color='gray', linestyle='--')

            # Plot density background if enabled
            if self.density_displayed and not self.single_frame:
                self.plot_density_background()

            # Scatter plot of the angles
            self.scatter = self.ax.scatter(
                phi,
                psi,
                color='#FF8C00',
                s=45,
                marker='H',
                edgecolor='black',
                linewidth=0.7,
                visible=self.scatter_visible
            )

            self.ax.set_title(f'Frame {frame_index}')

            def on_hover(event):
                """
                Display residue information when hovering over a point in the plot.
                """
                if event.inaxes == self.ax:
                    cont, ind = self.scatter.contains(event)
                    if cont:
                        index = ind["ind"][0]
                        # Update residue information entries
                        self.res_entry.config(state='normal')
                        self.res_entry.delete(0, tk.END)
                        self.res_entry.insert(0, str(index + 1))
                        self.res_entry.config(state='readonly')

                        self.psi_entry.config(state='normal')
                        self.psi_entry.delete(0, tk.END)
                        self.psi_entry.insert(0, f"{psi[index]:.2f}")
                        self.psi_entry.config(state='readonly')

                        self.phi_entry.config(state='normal')
                        self.phi_entry.delete(0, tk.END)
                        self.phi_entry.insert(0, f"{phi[index]:.2f}")
                        self.phi_entry.config(state='readonly')

                    self.canvas.draw_idle()

            # Connect hover event to the plot
            self.fig.canvas.mpl_connect("motion_notify_event", on_hover)

            # Redraw the canvas
            self.canvas.draw()

    def on_frame_change(self, event):
        """
        Event handler for frame slider changes.
        """
        if not self.single_frame:
            frame_index = int(self.frame_slider.get())
            self.update_plot(frame_index)
            self.frame_entry_var.set(str(frame_index))
            # Update histograms if the histogram window is open
            if self.hist_window_open:
                self.calculate_histograms(frame_index)

    def on_frame_entry_change(self, *args):
        """
        Event handler for frame entry changes.
        """
        if not self.single_frame:
            value = self.frame_entry_var.get()
            if value == '':
                self.frame_error_label.config(text="")
                return
            try:
                frame_index = int(value)
                max_frame = self.psi_matrix.shape[0] - 1
                if 0 <= frame_index <= max_frame:
                    self.frame_slider.set(frame_index)
                    self.update_plot(frame_index)
                    self.frame_error_label.config(text="")
                    # Update histograms if the histogram window is open
                    if self.hist_window_open:
                        self.calculate_histograms(frame_index)
                else:
                    # Display error message
                    self.frame_error_label.config(text=f"Invalid frame (0-{max_frame})")
            except ValueError:
                # Display error message
                self.frame_error_label.config(text="Invalid input")

    def toggle_density(self):
        """
        Toggle the display of the density background in the plot.
        """
        # Check if data is loaded
        if self.psi_matrix is None or self.phi_matrix is None:
            Messagebox.show_error(
                title="Error",
                message="Please load both PSI and PHI matrices first."
            )
            return

        if self.single_frame:
            Messagebox.show_info(
                title="Information",
                message="Density plot is not available for single-frame data."
            )
            return
        self.density_displayed = not self.density_displayed
        # Update button text
        if self.density_displayed:
            self.show_density_button.config(text="Hide Density")
        else:
            self.show_density_button.config(text="Show Density")
        self.update_plot(self.frame_slider.get())

    def toggle_scatter_plot(self):
        """
        Toggle the visibility of the scatter plot (Ramachandran points).
        """
        if self.scatter is not None:
            self.scatter_visible = not self.scatter_visible
            self.scatter.set_visible(self.scatter_visible)
            self.canvas.draw()
            # Update button text
            if self.scatter_visible:
                self.hide_ramach_button.config(text="Hide Ramach")
            else:
                self.hide_ramach_button.config(text="Show Ramach")
        else:
            Messagebox.show_error(
                title="Error",
                message="No scatter plot to hide. Please load data first."
            )

    def save_histograms(self):
        """
        Save the currently displayed histograms (per frame) to a file.
        """
        if self.hist_fig is None:
            Messagebox.show_error(
                title="Error",
                message="No histograms available to save."
            )
            return

        # Prompt user for file format
        file_format = Querybox.get_string(
            title="Format",
            prompt="Enter the format (png, jpg, pdf, etc.):",
            initialvalue="png"
        )
        if not file_format:
            return

        # Prompt user for DPI
        dpi = Querybox.get_integer(
            title="DPI",
            prompt="Enter DPI (resolution):",
            initialvalue=300,
            minvalue=1
        )

        # Ask for save location
        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=[(f"{file_format.upper()} files", f"*.{file_format}")]
        )
        if save_path:
            self.hist_fig.savefig(save_path, format=file_format, dpi=dpi)
            Messagebox.show_info(
                title="Save Successful",
                message=f"Histograms saved as {save_path}"
            )

    def save_plot(self):
        """
        Save the main Ramachandran plot to a file.
        """
        # Prompt user for file format
        file_format = Querybox.get_string(
            title="Format",
            prompt="Enter the format (png, jpg, pdf, etc.):",
            initialvalue="png"
        )
        if not file_format:
            return

        # Prompt user for DPI
        dpi = Querybox.get_integer(
            title="DPI",
            prompt="Enter DPI (resolution):",
            initialvalue=300,
            minvalue=1
        )

        # Ask for save location
        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=[(f"{file_format.upper()} files", f"*.{file_format}")]
        )
        if save_path:
            self.fig.savefig(save_path, format=file_format, dpi=dpi)
            Messagebox.show_info(
                title="Save Successful",
                message=f"Plot saved as {save_path}"
            )

    def show_ramachandran_per_res(self):
        """
        Display a Ramachandran plot for a specific residue across all frames.
        """
        if self.psi_matrix is None or self.phi_matrix is None:
            Messagebox.show_error(
                title="Error",
                message="Please load both PSI and PHI matrices first."
            )
            return

        # Prompt user for residue index
        residue_index = Querybox.get_integer(
            title="Residue Index",
            prompt="Enter residue index (starting from 1):",
            parent=self.root
        )
        if residue_index is None:
            return
        residue_index -= 1  # Adjust for zero-based indexing
        if residue_index < 0 or residue_index >= self.psi_matrix.shape[1] - 1:
            Messagebox.show_error(
                title="Error",
                message="Invalid residue index."
            )
            return

        # Create a new window for the Ramachandran plot
        ramach_window = ttkb.Toplevel(self.root)
        ramach_window.title(f"Ramachandran Plot for Residue {residue_index + 1}")
        ramach_window.geometry("800x600")

        # Create figure for the Ramachandran plot
        # Reduce the figure size by 30%
        original_ramach_figsize = (8, 6)
        reduced_ramach_figsize = (original_ramach_figsize[0] * 0.7, original_ramach_figsize[1] * 0.7)
        ramach_fig, ramach_ax = plt.subplots(figsize=reduced_ramach_figsize)
        ramach_canvas = FigureCanvasTkAgg(ramach_fig, master=ramach_window)
        ramach_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Extract angle data for the selected residue
        psi = self.psi_matrix[:, residue_index + 1]  # Ignore the first column
        phi = self.phi_matrix[:, residue_index + 1]  # Ignore the first column
        mask = (phi != 0) & (psi != 0)
        phi = phi[mask]
        psi = psi[mask]

        # Plot the Ramachandran plot
        ramach_ax.scatter(
            phi,
            psi,
            color='#FF8C00',
            s=45,
            marker='H',
            edgecolor='black',
            linewidth=0.7
        )
        ramach_ax.set_xlim([-180, 180])
        ramach_ax.set_ylim([-180, 180])
        ramach_ax.axhline(0, color='gray', linestyle='--')
        ramach_ax.axvline(0, color='gray', linestyle='--')
        ramach_ax.set_xlabel(r'$\Phi$ (°)')
        ramach_ax.set_ylabel(r'$\Psi$ (°)')
        ramach_ax.set_title(f'Residue {residue_index + 1}: Ramachandran Plot')

        ramach_canvas.draw()

        # Save Ramachandran Plot button
        def save_plot():
            """
            Save the per-residue Ramachandran plot to a file.
            """
            # Prompt user for file format
            file_format = Querybox.get_string(
                title="Format",
                prompt="Enter the format (png, jpg, pdf, etc.):",
                initialvalue="png"
            )
            if not file_format:
                return

            # Prompt user for DPI
            dpi = Querybox.get_integer(
                title="DPI",
                prompt="Enter DPI (resolution):",
                initialvalue=300,
                minvalue=1
            )

            # Ask for save location
            save_path = filedialog.asksaveasfilename(
                defaultextension=f".{file_format}",
                filetypes=[(f"{file_format.upper()} files", f"*.{file_format}")]
            )
            if save_path:
                ramach_fig.savefig(save_path, format=file_format, dpi=dpi)
                Messagebox.show_info(
                    title="Save Successful",
                    message=f"Ramachandran plot for Residue {residue_index + 1} saved as {save_path}"
                )

        save_ramach_button = ttkb.Button(
            ramach_window,
            text="Save Ramachandran Plot",
            command=save_plot,
            bootstyle="secondary"
        )
        save_ramach_button.pack(side=tk.TOP, padx=10, pady=5)

    def reset_app(self):
        """
        Reset the application to its initial state.
        Clears loaded data, resets plots, and restores UI components.
        """
        # Reset data variables
        self.psi_matrix = None
        self.phi_matrix = None
        self.all_phi = None
        self.all_psi = None
        self.single_frame = False
        self.density_displayed = False
        self.hist_fig = None
        self.ax_hist_phi = None
        self.ax_hist_psi = None
        self.hist_canvas = None
        self.hist_window_open = False
        self.scatter = None
        self.scatter_visible = True

        # Destroy all widgets in the root window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Re-initialize the UI components
        self.setup_styles()
        self.setup_ui()

def apply_window_configuration(root):
    """
    Apply aspect ratio and adjust the window size based on screen resolution.

    Args:
        root (ttkbootstrap.Window): The main application window.
    """
    # Get the screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Define the desired aspect ratio (width:height)
    ASPECT_RATIO = 4.5 / 3.0  # Adjust as needed

    # Determine the maximum desired size as a percentage of the screen
    max_width_percentage = 0.70  # For example, 70% of the screen width

    # Reduce the maximum height percentage by 20%
    original_max_height_percentage = 0.9  # Original value
    max_height_percentage = original_max_height_percentage * 0.8  # Reduce by 20%

    # Calculate the maximum window size
    max_window_width = int(screen_width * max_width_percentage)
    max_window_height = int(screen_height * max_height_percentage)

    # Calculate the size based on the aspect ratio
    window_width = max_window_width
    window_height = int(window_width / ASPECT_RATIO)

    # Adjust if calculated height exceeds maximum height
    if window_height > max_window_height:
        window_height = max_window_height
        window_width = int(window_height * ASPECT_RATIO)

    # Set minimum window size (optional)
    MIN_WIDTH = 600
    MIN_HEIGHT = 600

    window_width = max(window_width, MIN_WIDTH)
    window_height = max(window_height, MIN_HEIGHT)

    # Center the window on the screen
    x_position = int((screen_width - window_width) / 2)
    y_position = int((screen_height - window_height) / 2)

    # Apply the geometry to the window
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Make the window resizable and ensure elements adjust accordingly
    root.minsize(MIN_WIDTH, MIN_HEIGHT)

if __name__ == "__main__":
    # Create the main application window with a chosen theme
    root = Window(themename="superhero")

    # Apply window configuration (aspect ratio and size)
    apply_window_configuration(root)

    app = RamachandranApp(root)
    root.mainloop()
