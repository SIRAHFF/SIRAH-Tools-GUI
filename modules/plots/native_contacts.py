"""
Contacts Plotter Application

This script provides a graphical user interface (GUI) for visualizing contact data from a specified file.
It leverages Tkinter for the GUI, Matplotlib for plotting, Pandas for data manipulation, and ttkbootstrap
for theming and styling. Users can visualize the data and save the generated plots in various formats
with customizable resolution. The application dynamically adjusts its window size based on the user's
screen resolution to ensure optimal display across different devices.

Dependencies:
    - pandas
    - matplotlib
    - tkinter
    - ttkbootstrap
    - argparse

Usage:
    python contacts_plotter.py path_to_data_file.dat --time_factor 0.02

Author:
    Your Name
Date:
    YYYY-MM-DD
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import filedialog, Toplevel, StringVar, messagebox
from tkinter import Tk, Frame, BOTH, TOP, E, W
from ttkbootstrap import Style, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


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


# -----------------------------------------------------------------------------
# Save Plot Function
# -----------------------------------------------------------------------------

def save_plot(fig, parent):
    """
    Opens a dialog window allowing the user to save the current plot with specified DPI and format.

    Args:
        fig (matplotlib.figure.Figure): The Matplotlib figure object to be saved.
        parent (Tk): The parent Tkinter window for modal dialog behavior.

    Behavior:
        - Creates a new top-level window for save options.
        - Provides input fields for DPI (resolution) and a dropdown for selecting the file format.
        - Validates user input and handles saving the plot.
        - Displays success or error messages based on the outcome.
    """

    # Create a new top-level window for save options
    save_window = Toplevel(parent)
    save_window.title("Save Plot")
    save_window.resizable(False, False)  # Disable window resizing for consistency

    # Calculate dynamic size for the save window based on screen resolution
    screen_width = parent.winfo_screenwidth()
    screen_height = parent.winfo_screenheight()
    window_width = int(screen_width * 0.3)  # 30% of screen width
    window_height = int(screen_height * 0.2)  # 20% of screen height
    save_window.geometry(f"{window_width}x{window_height}")  # Set dynamic size

    # Center the save window on the screen
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    save_window.geometry(f"+{x_position}+{y_position}")

    # -----------------------------------------------------------------------------
    # Resolution (DPI) Input
    # -----------------------------------------------------------------------------

    # Label for DPI entry
    dpi_label = ttk.Label(save_window, text="Resolution (DPI):")
    dpi_label.grid(row=0, column=0, padx=10, pady=10, sticky=E)

    # Entry field for DPI input with default value
    dpi_entry = ttk.Entry(save_window)
    dpi_entry.grid(row=0, column=1, padx=10, pady=10, sticky=W)
    dpi_entry.insert(0, "300")  # Set default DPI value

    # -----------------------------------------------------------------------------
    # Format Selection
    # -----------------------------------------------------------------------------

    # Label for format selection
    format_label = ttk.Label(save_window, text="Format:")
    format_label.grid(row=1, column=0, padx=10, pady=10, sticky=E)

    # Variable and dropdown menu for selecting file format
    format_var = StringVar(save_window)
    format_var.set("png")  # Set default format
    formats = ["png", "pdf", "svg", "eps", "jpg", "tif"]  # Supported formats
    format_menu = ttk.OptionMenu(save_window, format_var, "png", *formats)
    format_menu.grid(row=1, column=1, padx=10, pady=10, sticky=W)

    # -----------------------------------------------------------------------------
    # Confirm Save Function
    # -----------------------------------------------------------------------------

    def confirm_save():
        """
        Validates user input and saves the plot with specified DPI and format.

        Displays appropriate message boxes based on success or failure of the save operation.
        """
        # Validate DPI input
        try:
            dpi_value = int(dpi_entry.get())
            if dpi_value <= 0:
                raise ValueError("DPI must be a positive integer.")
        except ValueError as ve:
            messagebox.showerror("Invalid DPI", f"Please enter a valid DPI value.\n{ve}")
            return

        # Retrieve selected file format
        file_format = format_var.get()

        # Open file dialog for user to specify save location and file name
        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=[(f"{file_format.upper()} files", f"*.{file_format}")],
            parent=save_window,
            title="Save Plot As"
        )

        if save_path:
            try:
                # Save the figure with specified DPI and format
                fig.savefig(save_path, dpi=dpi_value, format=file_format)
                # Notify user of successful save
                messagebox.showinfo("Success", f"Plot successfully saved to:\n{save_path}")
                # Close the save dialog window
                save_window.destroy()
            except Exception as e:
                # Notify user of any errors during the save process
                messagebox.showerror("Save Error", f"Failed to save plot.\nError: {e}")

    # -----------------------------------------------------------------------------
    # Save Button
    # -----------------------------------------------------------------------------

    # Button to trigger the save operation
    save_button = ttk.Button(save_window, text="Save", command=confirm_save)
    save_button.grid(row=2, column=0, columnspan=2, pady=20)


# -----------------------------------------------------------------------------
# Plot Contacts Function
# -----------------------------------------------------------------------------

def plot_contacts_in_window(file_path, time_factor=1.0, parent=None):
    """
    Reads contact data from a file, generates a plot, and embeds it within the Tkinter GUI.

    Args:
        file_path (str): The path to the data file containing contact information.
        time_factor (float): Factor to multiply the 'Frame' column to convert it to microseconds.
        parent (Tk): The parent Tkinter window for embedding the plot.

    Behavior:
        - Parses the data file using Pandas.
        - Multiplies the 'Frame' column by the time factor.
        - Creates a Matplotlib figure with dual y-axes for different data series.
        - Embeds the plot within the Tkinter window using FigureCanvasTkAgg.
        - Adds a custom navigation toolbar without the "Save" button.
        - Provides a button to save the plot using the save_plot function.
    """

    # -----------------------------------------------------------------------------
    # Data Loading
    # -----------------------------------------------------------------------------

    try:
        # Read data from the specified file using Pandas
        data = pd.read_csv(
            file_path,
            sep=r"\s+",  # Use whitespace as the separator
            header=None,  # No header row in the data file
            skiprows=1,  # Skip the first row (assuming it's a header or irrelevant)
            names=["Frame", "Cons", "Acc", "Cont", "Native", "NonNative"]  # Assign column names
        )
    except FileNotFoundError:
        messagebox.showerror("File Not Found", f"The specified file was not found:\n{file_path}")
        if parent:
            parent.destroy()
        return
    except pd.errors.ParserError as e:
        messagebox.showerror("Parsing Error", f"Failed to parse the data file.\nError: {e}")
        if parent:
            parent.destroy()
        return
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred while reading the file.\nError: {e}")
        if parent:
            parent.destroy()
        return

    # Multiply the 'Frame' column by the time factor to convert to microseconds
    try:
        data["Frame"] = data["Frame"].astype(float) * time_factor
    except ValueError as e:
        messagebox.showerror("Data Error", f"Failed to process the 'Frame' column.\nError: {e}")
        if parent:
            parent.destroy()
        return

    # -----------------------------------------------------------------------------
    # Plot Creation
    # -----------------------------------------------------------------------------

    # Create a Matplotlib figure and primary axis
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Configure the primary y-axis for Conservation and Accuracy
    ax1.set_xlabel('Time (μs)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')

    # Plot Accuracy first
    ax1.plot(
        data["Frame"],
        data['Acc'],
        color='#ff8811',  # Deep Sky Blue
        label='Accuracy',
        linewidth=1.0,
        zorder=2
    )

    # Plot Conservation last to make it appear on top
    ax1.plot(
        data["Frame"],
        data['Cons'],
        color='#3f88c5',
        label='Conservation',
        linewidth=1.0,
        zorder=4
    )
    ax1.tick_params(axis='y')

    # Configure the secondary y-axis for the number of contacts
    ax2 = ax1.twinx()
    ax2.set_ylabel('# Contacts', fontsize=12, color='#a3b18a', fontweight='bold')  # Slate Gray
    ax2.plot(
        data['Frame'],
        data['Cont'],
        color='#a3b18a',
        linewidth=1.0,
        label="Num Contacts",
        alpha=1.0, # Semi-transparent line
        zorder=1
    )
    ax2.tick_params(axis='y', labelcolor='#a3b18a', colors='#a3b18a')

    # Cambiar el color de los spines de ax2 al color definido
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_linewidth(1.5)
    ax1.spines['bottom'].set_linewidth(1.5)

    ax2.spines['right'].set_position(('axes', 1.015))
    ax2.spines['right'].set_linewidth(1.5)
    ax2.spines['right'].set_color('#a3b18a')


    # Ajustar el zorder de los ejes
    ax1.set_zorder(3)  # ax1 encima de ax2
    ax2.set_zorder(2)  # ax2 debajo de ax1

    # Ocultar el fondo de ax1 para que no cubra ax2
    ax1.patch.set_visible(False)

    # Add legend to the primary axis
    ax1.legend(loc='upper left', fontsize=10, frameon=False)
    ax2.legend(loc='upper right', fontsize=10, frameon=False)

    # Set the x-axis limits based on the data
    ax1.set_xlim(0, data["Frame"].max())

    # Ticks del eje x y eje y de ax1
    for label in ax1.get_xticklabels() + ax1.get_yticklabels():
        label.set_fontweight('bold')

    # Ticks del eje y de ax2
    for label in ax2.get_yticklabels():
        label.set_fontweight('bold')

    # Enhance layout to prevent clipping of labels and titles
    plt.tight_layout()



    # -----------------------------------------------------------------------------
    # Embedding Plot in Tkinter
    # -----------------------------------------------------------------------------

    # Create a FigureCanvasTkAgg object to embed the Matplotlib figure in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()  # Render the plot
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=BOTH, expand=True)  # Expand to fill the window

    # -----------------------------------------------------------------------------
    # Custom Toolbar Integration
    # -----------------------------------------------------------------------------

    # Create a frame to hold the navigation toolbar
    toolbar_frame = Frame(parent)
    toolbar_frame.pack(side=TOP, fill='x')  # Align to the top and fill horizontally

    # Initialize the custom toolbar without the "Save" button
    toolbar = CustomToolbar(canvas, toolbar_frame)
    toolbar.update()  # Update the toolbar to reflect changes

    # -----------------------------------------------------------------------------
    # Save Button Integration
    # -----------------------------------------------------------------------------

    # Button to trigger the save_plot function
    save_button = ttk.Button(parent, text="Save Plot", command=lambda: save_plot(fig, parent))
    save_button.pack(pady=10)  # Add vertical padding for spacing


# -----------------------------------------------------------------------------
# Main Application Entry Point
# -----------------------------------------------------------------------------

def main():
    """
    Parses command-line arguments and initializes the Tkinter GUI application.

    The application expects:
    - A positional argument specifying the path to the data file.
    - An optional named argument for the time factor.

    It sets up the main window with ttkbootstrap styling and embeds the plot based on the data.
    """

    # -----------------------------------------------------------------------------
    # Argument Parsing
    # -----------------------------------------------------------------------------

    parser = argparse.ArgumentParser(description="Plot contacts data from a file.")
    parser.add_argument(
        "file",
        type=str,
        help="Path to the data file (e.g., timeline_nameGC_nameGC.dat)."
    )
    parser.add_argument(
        "--time_factor",
        type=float,
        default=1.0,
        help="Time factor to convert frames to microseconds (default: 1.0)."
    )
    args = parser.parse_args()  # Parse the provided arguments

    # -----------------------------------------------------------------------------
    # Tkinter Window Initialization
    # -----------------------------------------------------------------------------

    # Initialize the main Tkinter window
    root = Tk()

    # Apply ttkbootstrap styling with the "superhero" theme
    style = Style(theme="superhero")

    # Retrieve screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Define window size as a percentage of screen size (e.g., 50% width, 60% height)
    window_width = int(screen_width * 0.5)
    window_height = int(screen_height * 0.6)

    # Set the geometry of the main window
    root.geometry(f"{window_width}x{window_height}")

    # Center the main window on the screen
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    root.geometry(f"+{x_position}+{y_position}")

    # Allow the window to be resizable
    root.resizable(True, True)

    # Set the window title
    root.title("Contacts Plotter")

    # -----------------------------------------------------------------------------
    # Plot Rendering
    # -----------------------------------------------------------------------------

    # Call the function to read data and display the plot in the GUI
    plot_contacts_in_window(args.file, args.time_factor, parent=root)

    # -----------------------------------------------------------------------------
    # Start the Tkinter Event Loop
    # -----------------------------------------------------------------------------

    root.mainloop()  # Begin the Tkinter event loop to keep the window open


if __name__ == "__main__":
    main()
