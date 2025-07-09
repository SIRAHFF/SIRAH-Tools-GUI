"""
Contact Map Plotter Application

This script provides a graphical user interface (GUI) for generating and visualizing contact maps
from specified data files. It leverages Tkinter for the GUI, Matplotlib for plotting, Pandas for data
handling, and ttkbootstrap for enhanced theming and styling. Users can visualize contact data and
save the generated plots in various formats with customizable resolution. The application dynamically
adjusts its window size based on the user's screen resolution to ensure optimal display across
different devices.

Dependencies:
    - numpy
    - pandas
    - matplotlib
    - seaborn
    - tkinter
    - ttkbootstrap
    - argparse
    - logging

Usage:
    python contact_map_plotter.py matrix_length.txt percentage_data.dat

Author:
    Your Name
Date:
    YYYY-MM-DD
"""

import argparse
import logging
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import Style, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from collections import Counter
import os
import sys

# -----------------------------------------------------------------------------
# Custom Toolbar Class
# -----------------------------------------------------------------------------

class CustomToolbar(NavigationToolbar2Tk):
    """
    Customizes the Matplotlib navigation toolbar by removing the "Save" button.

    Inherits from Matplotlib's NavigationToolbar2Tk and overrides the toolitems to exclude
    the "Save" button, preventing redundancy since saving is handled separately within the application.
    """
    # Exclude the "Save" button from the toolbar
    toolitems = [t for t in NavigationToolbar2Tk.toolitems if t[0] != 'Save']

    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)

# -----------------------------------------------------------------------------
# Data Reading Functions
# -----------------------------------------------------------------------------

def read_matrix_length(file_path):
    """
    Reads the matrix_length.txt file and extracts selection labels and matrix dimensions.

    Args:
        file_path (str): Path to the matrix_length.txt file.

    Returns:
        tuple: A tuple containing (sel1, sel2, rows, cols) if successful,
               otherwise (None, None, None, None).
    """
    sel1 = sel2 = ""
    size1 = size2 = 0

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        if len(lines) < 2:
            messagebox.showerror("Error", "The file matrix_length.txt must contain at least two lines.")
            logging.error("matrix_length.txt has fewer than two lines.")
            return None, None, None, None

        # Extract labels for sel1 and sel2, and the size of the matrix
        sel1 = lines[0].strip().split('"')[1] if '"' in lines[0] else "Selection 1"
        sel2 = lines[1].strip().split('"')[1] if '"' in lines[1] else "Selection 2"

        try:
            size1 = int(lines[0].strip().split()[-1])  # Extract the last value as size
            size2 = int(lines[1].strip().split()[-1])
        except (IndexError, ValueError) as e:
            messagebox.showerror("Error", f"Error parsing matrix_length.txt: {e}")
            logging.error(f"Error parsing matrix_length.txt: {e}")
            return None, None, None, None

        # Define the size of the matrix
        rows = size1
        cols = size2

        logging.info(f"Read matrix_length.txt: sel1='{sel1}', sel2='{sel2}', rows={rows}, columns={cols}")
        return sel1, sel2, rows, cols

    except FileNotFoundError:
        messagebox.showerror("Error", f"matrix_length.txt file not found: {file_path}")
        logging.error(f"matrix_length.txt file not found: {file_path}")
        return None, None, None, None
    except Exception as e:
        messagebox.showerror("Error", f"Error reading matrix_length.txt: {e}")
        logging.error(f"Error reading matrix_length.txt: {e}")
        return None, None, None, None


def read_percentage_file(file_path, rows, cols):
    """
    Reads the percentage_*.dat file using pandas and extracts residue indices and contact percentages.

    Args:
        file_path (str): Path to the percentage_*.dat file.
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.

    Returns:
        tuple: A tuple containing (resid1, resid2, frac_percent) if successful,
               otherwise (None, None, None).
    """
    try:
        # Read the file with columns Resid 1, Atom 1, Resid 2, Atom 2, Frac(%), NFrames
        data = pd.read_csv(
            file_path,
            sep='\s+',  # Separator by spaces
            header=None,
            skiprows=1,  # Skip the first row if it's an unwanted header
            names=["Resid 1", "Atom 1", "Resid 2", "Atom 2", "Frac(%)", "NFrames"]
        )

        # Log the first few rows for debugging
        logging.info(f"First rows of percentage file:\n{data.head()}")

        # Filter the necessary columns and drop rows with missing values
        data_filtered = data[['Resid 1', 'Resid 2', 'Frac(%)']].dropna()
        logging.info(f"Filtered data:\n{data_filtered.head()}")

        # Group by 'Resid 1' and 'Resid 2' and get the maximum 'Frac(%)'
        max_contacts = data_filtered.groupby(['Resid 1', 'Resid 2']).max().reset_index()
        logging.info(f"Grouped maximum contacts:\n{max_contacts.head()}")

        # Handle 'Frac(%)' if it contains the '%' symbol
        max_contacts['Frac(%)'] = max_contacts['Frac(%)'].astype(str).str.replace('%', '').astype(float)

        # Extract relevant columns and convert them to appropriate types
        resid1 = max_contacts['Resid 1'].astype(int).values
        resid2 = max_contacts['Resid 2'].astype(int).values
        frac_percent = max_contacts['Frac(%)'].astype(float).values

        # Debugging: Log some values of Frac(%)
        logging.info(f"First Frac(%) values: {frac_percent[:5]}")

        # Log some data for debugging
        logging.info(f"Resid1: {resid1[:5]}")
        logging.info(f"Resid2: {resid2[:5]}")
        logging.info(f"Frac (%): {frac_percent[:5]}")

        return resid1, resid2, frac_percent

    except FileNotFoundError:
        messagebox.showerror("Error", f"percentage_*.dat file not found: {file_path}")
        logging.error(f"percentage_*.dat file not found: {file_path}")
        return None, None, None
    except Exception as e:
        messagebox.showerror("Error", f"Error reading percentage_*.dat: {e}")
        logging.error(f"Error reading percentage_*.dat: {e}")
        return None, None, None


def is_symmetric_based_on_dimensions(rows, cols):
    """
    Determines if the matrix is symmetric based on its dimensions.

    Args:
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.

    Returns:
        bool: True if the matrix is symmetric, False otherwise.
    """
    symmetric = rows == cols
    logging.info(f"Is the matrix symmetric based on dimensions? {symmetric}")
    return symmetric

# -----------------------------------------------------------------------------
# Plotting Functions
# -----------------------------------------------------------------------------

def plot_symmetric_contact_map(resid1, resid2, sel1, sel2, percentage, cmap='viridis', figsize=(5, 5)):
    """
    Generates and plots a symmetric contact matrix based on percentage data.

    Args:
        resid1 (array-like): Residue indices 1.
        resid2 (array-like): Residue indices 2.
        sel1 (str): Label for the Y-axis.
        sel2 (str): Label for the X-axis.
        percentage (array-like): Contact percentages.
        cmap (str, optional): Colormap for the plot. Defaults to 'viridis'.
        figsize (tuple, optional): Figure size. Defaults to (5, 5).

    Returns:
        matplotlib.figure.Figure: The generated figure, or None in case of an error.
    """
    try:
        fig, ax = plt.subplots(figsize=figsize)
        # For symmetric matrices, define the size based on the maximum residue
        max_residue = max(max(resid1, default=0), max(resid2, default=0))
        min_residue = min(min(resid1, default=1), min(resid2, default=1))


        if max_residue == 0:
            messagebox.showerror("Error", "No residues found to plot.")
            logging.error("No residues found to plot.")
            plt.close(fig)
            return None

        contact_map = np.zeros((max_residue, max_residue))

        for r1, r2, perc in zip(resid1, resid2, percentage):
            contact_map[r1 - 1, r2 - 1] = perc
            contact_map[r2 - 1, r1 - 1] = perc  # Ensure symmetry

        cax = ax.imshow(contact_map, cmap=cmap, origin='lower', aspect='equal')

        #Set limits of axis
        ax.set_xlim(min_residue, max_residue -1)
        ax.set_ylim(min_residue, max_residue -1)

        ax.set_title('Contact Map - Percentage (Symmetric)', fontsize=10)
        ax.set_xlabel(sel1, fontsize=10)
        ax.set_ylabel(sel2, fontsize=10)

        fig.colorbar(cax, ax=ax, label='Contact Percentage (%)')

        # Manually adjust the layout
        plt.tight_layout()

        logging.info("Symmetric plot generated successfully.")
        return fig

    except ValueError as ve:
        messagebox.showerror("Error", f"Error plotting contact matrix: {ve}")
        logging.error(f"Error plotting contact matrix: {ve}")
        plt.close(fig)
        return None


def plot_asymmetric_contact_map(resid1, resid2, percentage, rows, cols, sel1, sel2, cmap='viridis', figsize=(6, 4)):
    """
    Generates and plots an asymmetric contact matrix.

    Args:
        resid1 (array-like): Residue indices 1.
        resid2 (array-like): Residue indices 2.
        percentage (array-like): Contact percentages.
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.
        sel1 (str): Label for the Y-axis.
        sel2 (str): Label for the X-axis.
        cmap (str, optional): Colormap for the plot. Defaults to 'viridis'.
        figsize (tuple, optional): Figure size. Defaults to (6, 4).

    Returns:
        matplotlib.figure.Figure: The generated figure, or None in case of an error.
    """
    try:
        # Create a DataFrame from the provided data
        max_contacts = pd.DataFrame({
            'Resid 1': resid1,
            'Resid 2': resid2,
            'Frac(%)': percentage
        })

        # Count the frequency of each value in the "Resid 1" and "Resid 2" columns
        all_values = list(max_contacts['Resid 1']) + list(max_contacts['Resid 2'])
        value_counts = Counter(all_values)

        # Function to reorder "Resid 1" and "Resid 2" to maximize repetitions of the most common value in "Resid 1"
        def maximize_resid(row):
            if value_counts[row['Resid 1']] < value_counts[row['Resid 2']]:
                return row['Resid 2'], row['Resid 1']
            else:
                return row['Resid 1'], row['Resid 2']

        # Apply the function to each row to reorder the values
        max_contacts['Resid 1'], max_contacts['Resid 2'] = zip(*max_contacts.apply(maximize_resid, axis=1))

        # Sort the DataFrame in descending order so that the most common values are at the top
        max_contacts.sort_values(by=['Resid 1'], ascending=False, inplace=True)

        # Reset the DataFrame index
        max_contacts.reset_index(drop=True, inplace=True)

        # Convert "Resid 1" and "Resid 2" to integers
        max_contacts[['Resid 1', 'Resid 2']] = max_contacts[['Resid 1', 'Resid 2']].astype(int)

        # Create the "Resid 1" vs "Resid 2" matrix with "Frac(%)" values
        matrix = max_contacts.pivot_table(index='Resid 1', columns='Resid 2', values='Frac(%)', aggfunc='mean', fill_value=0)

        # Create the figure and axes
        fig, ax = plt.subplots(figsize=figsize)

        # Plot the matrix using seaborn
        sns.heatmap(matrix, cmap=cmap, ax=ax, cbar_kws={'label': 'Frac (%)'}, square=False)

        ax.set_title(f'Contact Matrix between {sel1} and {sel2}', fontsize=8)
        ax.set_ylabel(sel2, fontsize=10)
        ax.set_xlabel(sel1, fontsize=10)



        # Manually adjust the layout
        plt.tight_layout()

        return fig

    except ValueError as ve:
        messagebox.showerror("Error", f"Error plotting contact matrix: {ve}")
        logging.error(f"Error plotting contact matrix: {ve}")
        plt.close(fig)
        return None


def plot_contact_map_based_on_symmetry(resid1, resid2, percentage, rows, cols, sel1, sel2, cmap='viridis', symmetric=False, figsize=None):
    """
    Determines whether to plot a symmetric or asymmetric contact matrix based on validation.

    Args:
        resid1 (array-like): Residue indices 1.
        resid2 (array-like): Residue indices 2.
        percentage (array-like): Contact percentages.
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.
        sel1 (str): Label for the Y-axis.
        sel2 (str): Label for the X-axis.
        cmap (str, optional): Colormap for the plot. Defaults to 'viridis'.
        symmetric (bool, optional): Indicates if the matrix is symmetric. Defaults to False.
        figsize (tuple, optional): Figure size. Defaults to None.

    Returns:
        matplotlib.figure.Figure: The generated figure, or None in case of an error.
    """
    if symmetric:
        if figsize is None:
            figsize = (5, 5)
        fig = plot_symmetric_contact_map(resid1, resid2, sel1, sel2, percentage, cmap=cmap, figsize=figsize)
    else:
        if figsize is None:
            figsize = (6, 4)
        fig = plot_asymmetric_contact_map(resid1, resid2, percentage, rows, cols, sel1, sel2, cmap=cmap, figsize=figsize)

    return fig

# -----------------------------------------------------------------------------
# Save Plot Functions
# -----------------------------------------------------------------------------

def save_plot(resid1, resid2, percentage, rows, cols, sel1, sel2, cmap='viridis', dpi=300, filename="plot.png", symmetric=False):
    """
    Generates and saves the plot, maintaining the correct aspect ratio.

    Args:
        resid1 (array-like): Residue indices 1.
        resid2 (array-like): Residue indices 2.
        percentage (array-like): Contact percentages.
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.
        sel1 (str): Label for the Y-axis.
        sel2 (str): Label for the X-axis.
        cmap (str, optional): Colormap for the plot. Defaults to 'viridis'.
        dpi (int, optional): DPI for saving the plot. Defaults to 300.
        filename (str, optional): Filename for saving the plot. Defaults to "plot.png".
        symmetric (bool, optional): Indicates if the matrix is symmetric. Defaults to False.
    """
    try:
        # Close any existing figures to avoid conflicts
        plt.close('all')

        # Generate the plot with appropriate figsize based on symmetry
        if symmetric:
            figsize = (5, 5)
        else:
            figsize = (6, 4)

        fig = plot_contact_map_based_on_symmetry(
            resid1, resid2, percentage, rows, cols, sel1, sel2,
            cmap=cmap, symmetric=symmetric, figsize=figsize
        )

        if fig is not None:
            # Save the figure
            fig.savefig(filename, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            messagebox.showinfo("Saved", f"Plot saved as {filename} with DPI={dpi}")
            logging.info(f"Plot saved as {filename} with DPI={dpi}")

    except Exception as e:
        messagebox.showerror("Error", f"Error saving the plot: {str(e)}")
        logging.error(f"Error saving the plot: {str(e)}")


def save_plot_with_user_dpi_and_format(resid1, resid2, percentage, rows, cols, sel1, sel2, cmap='viridis', parent=None, symmetric=False):
    """
    Opens a dialog for the user to specify DPI, filename, format, and save location,
    then saves the plot accordingly.

    Args:
        resid1 (array-like): Residue indices 1.
        resid2 (array-like): Residue indices 2.
        percentage (array-like): Contact percentages.
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.
        sel1 (str): Label for the Y-axis.
        sel2 (str): Label for the X-axis.
        cmap (str, optional): Colormap for the plot. Defaults to 'viridis'.
        parent (tk.Toplevel, optional): Parent window for the dialog. Defaults to None.
        symmetric (bool, optional): Indicates if the matrix is symmetric. Defaults to False.

    Returns:
        None
    """
    try:
        # Create a custom save dialog window
        save_window = tk.Toplevel(parent)
        save_window.title("Save Plot")
        save_window.resizable(False, False)  # Disable resizing

        # Obtain screen dimensions for dynamic sizing
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        window_width = int(screen_width * 0.3)  # 30% of screen width
        window_height = int(screen_height * 0.2)  # 20% of screen height
        save_window.geometry(f"{window_width}x{window_height}")

        # Center the save window on the screen
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        save_window.geometry(f"+{x_position}+{y_position}")

        # Apply ttkbootstrap style
        style = Style(theme="superhero")

        # Define fonts
        widget_font = ('DejaVu Sans', 10)  # Vector font compatible with Linux, size 10

        # -----------------------------------------------------------------------------
        # DPI Entry
        # -----------------------------------------------------------------------------

        dpi_label = ttk.Label(save_window, text="Resolution (DPI):", font=widget_font)
        dpi_label.grid(row=0, column=0, padx=10, pady=10, sticky='e')

        dpi_entry = ttk.Entry(save_window, font=widget_font)
        dpi_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        dpi_entry.insert(0, "150")  # Default DPI value

        # -----------------------------------------------------------------------------
        # Format Selection
        # -----------------------------------------------------------------------------

        format_label = ttk.Label(save_window, text="Format:", font=widget_font)
        format_label.grid(row=1, column=0, padx=10, pady=10, sticky='e')

        # Supported formats
        format_var = tk.StringVar(save_window)
        format_var.set("png")  # Default format
        formats = ["png", "pdf", "svg", "eps", "jpg", "tif"]
        format_menu = ttk.OptionMenu(save_window, format_var, "png", *formats)
        format_menu.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        # -----------------------------------------------------------------------------
        # Save Confirmation Function
        # -----------------------------------------------------------------------------

        def confirm_save():
            """
            Validates user input and saves the plot with the specified DPI and format.

            Displays appropriate dialog boxes based on the success or failure of the save operation.
            """
            # Validate DPI input
            try:
                dpi_value = int(dpi_entry.get())
                if dpi_value <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Resolution must be a positive integer.")
                return

            # Get the selected file format
            file_format = format_var.get()

            # Open dialog to specify file location and name
            save_path = filedialog.asksaveasfilename(
                defaultextension=f".{file_format}",
                filetypes=[(f"{file_format.upper()} files", f"*.{file_format}"), ("All Files", "*.*")],
                parent=save_window
            )

            if save_path:
                try:
                    # Generate and save the plot
                    save_plot(
                        resid1, resid2, percentage, rows, cols, sel1, sel2,
                        cmap=cmap, dpi=dpi_value, filename=save_path, symmetric=symmetric
                    )
                    save_window.destroy()  # Close the save dialog
                except Exception as e:
                    messagebox.showerror("Error", f"Error saving the plot:\n{e}")
                    logging.error(f"Error saving the plot: {e}")

        # -----------------------------------------------------------------------------
        # Save Button
        # -----------------------------------------------------------------------------

        save_button = ttk.Button(save_window, text="Save", command=confirm_save, style='Primary.TButton')
        save_button.grid(row=2, column=0, columnspan=2, pady=20)

        # Make the save window modal
        save_window.grab_set()
        parent.wait_window(save_window)

    except Exception as e:
        messagebox.showerror("Error", f"Error saving the plot: {str(e)}")
        logging.error(f"Error saving the plot: {str(e)}")

# -----------------------------------------------------------------------------
# Plot Window Function
# -----------------------------------------------------------------------------

def open_plot_window(root, resid1, resid2, percentage, rows, cols, sel1, sel2):
    """
    Opens a new window to display the plot with colormap options and save functionality.

    Args:
        root (tk.Tk): The main Tkinter root window.
        resid1 (array-like): Residue indices 1.
        resid2 (array-like): Residue indices 2.
        percentage (array-like): Contact percentages.
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.
        sel1 (str): Label for the Y-axis.
        sel2 (str): Label for the X-axis.
    """
    # Create a new Tkinter window within the main window
    plot_window = tk.Toplevel(root)
    plot_window.title("Contact Map Plot")

    # Set a fixed appropriate size for the window
    window_width = 1000  # Width in pixels
    window_height = 800  # Height in pixels
    plot_window.geometry(f"{window_width}x{window_height}")

    # Allow the window to be resizable
    plot_window.resizable(True, True)

    # Define fonts
    widget_font = ('DejaVu Sans', 10)  # Vector font compatible with Linux, size 10

    # Create a top frame for controls and toolbar
    top_frame = ttk.Frame(plot_window)
    top_frame.pack(side='top', pady=10, padx=10, fill='x')

    # Create subframes to organize controls and toolbar
    controls_frame = ttk.Frame(top_frame)
    controls_frame.pack(side='left', fill='x', expand=True)

    toolbar_frame = ttk.Frame(top_frame)
    toolbar_frame.pack(side='right')

    # Create a Combobox for selecting the colormap
    cmap_var = tk.StringVar(value='viridis')
    cmap_label = ttk.Label(controls_frame, text="Colormap:", font=widget_font)
    cmap_label.pack(side='left', padx=(0, 5))  # Minimal right padding

    cmap_combobox = ttk.Combobox(
        controls_frame,
        textvariable=cmap_var,
        values=plt.colormaps(),
        state="readonly",
        font=widget_font
    )
    cmap_combobox.set("viridis")  # Default colormap
    cmap_combobox.pack(side='left', padx=(0, 10))  # Minimal left padding

    # Create a button to save the plot
    save_button = ttk.Button(controls_frame, text="Save Plot", style='Primary.TButton')
    save_button.pack(side='left')  # No padding needed

    # Determine if the matrix is symmetric
    symmetric = is_symmetric_based_on_dimensions(rows, cols)

    # Create the figure for visualization with appropriate size
    if symmetric:
        figsize = (5, 5)
    else:
        figsize = (6, 4)

    fig = plot_contact_map_based_on_symmetry(
        resid1, resid2, percentage, rows, cols, sel1, sel2,
        cmap=cmap_var.get(),
        symmetric=symmetric,
        figsize=figsize
    )
    if fig is None:
        logging.error("Failed to generate the initial figure.")
        return

    # Create the canvas
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(padx=10, pady=10, fill='both', expand=True)

    # Create and pack the custom toolbar in the toolbar frame
    toolbar = CustomToolbar(canvas, toolbar_frame)
    toolbar.update()
    toolbar.pack()

    # Assign the toolbar as an attribute of plot_window
    plot_window.toolbar = toolbar

    # Store the figure and canvas in the window for future updates
    plot_window.fig = fig
    plot_window.canvas = canvas

    def generate_plot(event=None):
        """
        Generates and displays the plot based on the selected colormap.
        """
        # Generate a new figure based on the current colormap selection
        if symmetric:
            figsize = (5, 5)
        else:
            figsize = (6, 4)

        new_fig = plot_contact_map_based_on_symmetry(
            resid1, resid2, percentage, rows, cols, sel1, sel2,
            cmap=cmap_var.get(),
            symmetric=symmetric,
            figsize=figsize
        )
        if new_fig is not None:
            try:
                # Clear the existing canvas
                plot_window.canvas.get_tk_widget().destroy()
                plot_window.toolbar.destroy()

                # Create a new canvas
                canvas = FigureCanvasTkAgg(new_fig, master=plot_window)
                canvas.draw()
                canvas_widget = canvas.get_tk_widget()
                canvas_widget.pack(padx=10, pady=10, fill='both', expand=True)

                # Create a new custom toolbar in the toolbar frame
                toolbar = CustomToolbar(canvas, toolbar_frame)
                toolbar.update()
                toolbar.pack()

                # Assign the new toolbar as an attribute of plot_window
                plot_window.toolbar = toolbar

                # Update the references
                plot_window.fig = new_fig
                plot_window.canvas = canvas
                logging.info("Plot updated with new colormap.")
            except AttributeError as ae:
                messagebox.showerror("Error", f"Error updating the plot: {ae}")
                logging.error(f"Error updating the plot: {ae}")

    # Bind the Combobox selection change to the plot generation function
    cmap_combobox.bind("<<ComboboxSelected>>", generate_plot)

    # Configure the save button to save the current plot with user-specified DPI and format
    save_button.config(command=lambda: save_plot_with_user_dpi_and_format(
        resid1, resid2, percentage, rows, cols, sel1, sel2,
        cmap=cmap_var.get(),
        parent=plot_window,
        symmetric=symmetric
    ))

    # Function to properly close the window and terminate the process
    def on_closing():
        plot_window.destroy()
        root.destroy()  # Terminate the Tkinter main loop

    # Bind the window close event to the on_closing function
    plot_window.protocol("WM_DELETE_WINDOW", on_closing)

# -----------------------------------------------------------------------------
# Main Function
# -----------------------------------------------------------------------------

def main():
    """
    Main function to load files, configure logging, and open the Tkinter window with the plot.
    """
    # Define command-line arguments
    parser = argparse.ArgumentParser(description='Generate contact matrix from files.')
    parser.add_argument('matrix_length', type=str, help='matrix_length.txt file')
    parser.add_argument('percentage_file', type=str, help='percentage_*.dat file')

    # Parse arguments
    args = parser.parse_args()

    # Determine the directory where the log file should be saved
    # Assuming that both input files are in the 'contacts' directory
    matrix_length_path = os.path.abspath(args.matrix_length)
    percentage_file_path = os.path.abspath(args.percentage_file)

    # Extract the directory path from the matrix_length.txt file
    contacts_dir = os.path.dirname(matrix_length_path)

    # Ensure that the contacts directory exists
    if not os.path.isdir(contacts_dir):
        messagebox.showerror("Error", f"The contacts directory does not exist: {contacts_dir}")
        sys.exit(1)

    # Define the log file path in the contacts directory
    log_file_path = os.path.join(contacts_dir, 'contacts_matrix.log')

    # Configure logging to write to the log file in the contacts directory
    logging.basicConfig(
        filename=log_file_path,
        filemode='w',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Remove default console handlers to prevent logging to the console
    logging.getLogger().handlers = [handler for handler in logging.getLogger().handlers if isinstance(handler, logging.FileHandler)]

    # Initialize ttkbootstrap with the "superhero" theme
    style = Style(theme='superhero')

    # Create the main Tkinter window
    root = style.master
    root.withdraw()  # Hide the main window, as only the plot window will be used

    # Read files to obtain data
    sel1, sel2, rows, cols = read_matrix_length(args.matrix_length)
    if not all([sel1, sel2, rows, cols]):
        logging.error("Error reading matrix_length.txt. Terminating execution.")
        messagebox.showerror("Error", "Error reading matrix_length.txt. Check the log file.")
        return

    resid1, resid2, percentage = read_percentage_file(args.percentage_file, rows, cols)
    if not all([resid1 is not None, resid2 is not None, percentage is not None]):
        logging.error("Error reading the percentage file. Terminating execution.")
        messagebox.showerror("Error", "Error reading the percentage file. Check the log file.")
        return

    # Log the dimensions of the matrix
    logging.info(f"Matrix dimensions: {rows}x{cols}")

    # Open the Tkinter window to display the plot
    open_plot_window(root, resid1, resid2, percentage, rows, cols, sel1, sel2)

    # Ensure the application terminates correctly when the window is closed
    root.mainloop()  # Run the Tkinter main loop

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
