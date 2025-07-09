"""
Heatmap Viewer Application

This script provides a graphical user interface (GUI) for viewing and interacting with heatmap data.
It utilizes Tkinter for the GUI, Matplotlib for plotting, Pandas for data manipulation, and ttkbootstrap
for enhanced theming and styling. Users can navigate through different frames of heatmap data, adjust
colormaps, save plots in various formats with customizable resolution, and create animated GIFs from
selected frames. The application ensures that all logs are saved within the designated 'contacts' directory
for organized record-keeping and debugging.

Dependencies:
    - numpy
    - pandas
    - matplotlib
    - seaborn
    - tkinter
    - ttkbootstrap
    - argparse
    - logging
    - PIL
    - imageio

Usage:
    python contacts_by_frame.py data_file length_file

Author:
    Your Name
Date:
    YYYY-MM-DD
"""

import seaborn as sns
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from tkinter import (
    TOP, BOTTOM, BOTH, filedialog, simpledialog, LEFT, RIGHT, messagebox,
    X, Y, YES, NO, CENTER, N, S, E, W, Toplevel, Entry, Label, Frame, Button
)
import argparse
import sys
import shlex
import os
import shutil
from PIL import Image
import imageio
import threading
import logging

from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk  # Correct import

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
# Main Application Function
# -----------------------------------------------------------------------------

def main():
    """
    Initializes and runs the Heatmap Viewer application.
    Parses command-line arguments, loads data, sets up the GUI, and handles user interactions.
    """
    # -----------------------------------------------------------------------------
    # Parse Command-Line Arguments
    # -----------------------------------------------------------------------------

    parser = argparse.ArgumentParser(description='Heatmap Viewer')
    parser.add_argument('data_file', help='Path to the data file')
    parser.add_argument('length_file', help='Path to the length file')
    args = parser.parse_args()

    # -----------------------------------------------------------------------------
    # Determine Logging Directory and Configure Logging
    # -----------------------------------------------------------------------------

    # Determine the directory where the log file should be saved
    # Assuming that both input files are in the 'contacts' directory
    data_file_path = os.path.abspath(args.data_file)
    length_file_path = os.path.abspath(args.length_file)

    # Extract the directory path from the length_file_path
    contacts_dir = os.path.dirname(length_file_path)

    # Ensure that the contacts directory exists
    if not os.path.isdir(contacts_dir):
        messagebox.showerror("Error", f"The contacts directory does not exist: {contacts_dir}")
        sys.exit(1)

    # Define the log file path in the contacts directory
    log_file_path = os.path.join(contacts_dir, 'heatmap_viewer.log')

    # Configure logging to write to the log file in the contacts directory
    logging.basicConfig(
        filename=log_file_path,
        filemode='w',  # Overwrite the log file each time the program runs
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Remove default console handlers to prevent logging to the console
    logging.getLogger().handlers = [handler for handler in logging.getLogger().handlers if isinstance(handler, logging.FileHandler)]

    logging.info("Heatmap Viewer application started.")

    # -----------------------------------------------------------------------------
    # Load the Data File
    # -----------------------------------------------------------------------------

    try:
        data = pd.read_csv(args.data_file, sep="\s+", header=None)
        logging.info("Data loaded successfully.")
        logging.info(f"Data dimensions: {data.shape}")
    except FileNotFoundError:
        logging.error(f"Data file {args.data_file} not found.")
        messagebox.showerror("File Not Found", f"Data file {args.data_file} not found.")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logging.error(f"Data file {args.data_file} is empty.")
        messagebox.showerror("Empty File", f"Data file {args.data_file} is empty.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while reading the data file: {e}")
        messagebox.showerror("Error", f"An error occurred while reading the data file: {e}")
        sys.exit(1)

    # Skip the first column as it's not used
    data = data.iloc[:, 1:]
    logging.info(f"Data dimensions after skipping the first column: {data.shape}")

    # -----------------------------------------------------------------------------
    # Read the Sizes and Labels from the Length File
    # -----------------------------------------------------------------------------

    try:
        with open(args.length_file, 'r') as f:
            lines = f.readlines()
            if len(lines) != 2:
                logging.error(f"Expected 2 lines in file {args.length_file}, but got {len(lines)}.")
                messagebox.showerror("Invalid Length File", f"Expected 2 lines in file {args.length_file}, but got {len(lines)}.")
                sys.exit(1)

            tokens1 = shlex.split(lines[0].strip())
            tokens2 = shlex.split(lines[1].strip())

            if len(tokens1) < 3 or len(tokens2) < 3:
                logging.error(f"Invalid format in {args.length_file}. Each line must have at least 3 columns.")
                messagebox.showerror("Invalid Length File", f"Invalid format in file {args.length_file}. Each line must have at least 3 columns.")
                sys.exit(1)

            label1 = tokens1[1]
            size1 = int(tokens1[2])
            label2 = tokens2[1]
            size2 = int(tokens2[2])

            logging.info(f"Label1: {label1}, Size1: {size1}")
            logging.info(f"Label2: {label2}, Size2: {size2}")

    except ValueError:
        logging.error(f"Invalid value in file {args.length_file}. Sizes must be integers.")
        messagebox.showerror("Invalid Length File", f"Invalid value in file {args.length_file}. Sizes must be integers.")
        sys.exit(1)
    except FileNotFoundError:
        logging.error(f"Length file {args.length_file} not found.")
        messagebox.showerror("File Not Found", f"Length file {args.length_file} not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading the length file: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred while reading the length file: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------------
    # Determine Axis Labels Based on Size Comparison
    # -----------------------------------------------------------------------------

    if size1 >= size2:
        x_label = label1
        x_size = size1
        y_label = label2
        y_size = size2
    else:
        x_label = label2
        x_size = size2
        y_label = label1
        y_size = size1

    logging.info(f"x_size: {x_size}, y_size: {y_size}")

    expected_columns = x_size * y_size

    logging.info(f"Number of columns in data: {data.shape[1]}")
    logging.info(f"Expected number of columns (x_size * y_size): {expected_columns}")

    if data.shape[1] < expected_columns:
        logging.error("Data file does not have enough columns for the specified matrix size.")
        messagebox.showerror("Insufficient Data", "Data file does not have enough columns for the specified matrix size.")
        sys.exit(1)

    # -----------------------------------------------------------------------------
    # Compute Global Minimum and Maximum for Consistent Color Scaling
    # -----------------------------------------------------------------------------

    data_subset = data.iloc[:, :expected_columns]
    global_min = data_subset.values.min()
    global_max = data_subset.values.max()

    logging.info(f"Global min: {global_min}, Global max: {global_max}")

    # Handle case where all data values are identical
    if global_min == global_max:
        logging.warning("All data values are the same. The heatmap will show a single color.")
        global_min -= 0.001
        global_max += 0.001

    # Initialize with the first frame
    initial_frame = 0
    data_row = data_subset.iloc[initial_frame, :]

    # Reshape data into matrix dimensions
    matrix_data = data_row.values.reshape(y_size, x_size)
    df_initial = pd.DataFrame(matrix_data)

    logging.info(f"Initial matrix dimensions: {df_initial.shape}")
    logging.debug(f"Initial matrix:\n{df_initial}")

    # -----------------------------------------------------------------------------
    # Define Font Preferences
    # -----------------------------------------------------------------------------

    plot_font = 'Arial'
    widget_font = 'Arial'

    # --- Define Figure Parameters ---
    # Adjust figure size based on matrix symmetry
    if x_size == y_size:
        fig_size = (6, 5)  # Inches
    else:
        fig_size = (6, 3)  # Inches

    fig_dpi = 100  # Dots per inch
    fig_width_px = int(fig_size[0] * fig_dpi * 1.5)
    fig_height_px = int(fig_size[1] * fig_dpi * 1.5)

    # Create matplotlib figure and axis
    fig = Figure(figsize=fig_size, dpi=fig_dpi)
    ax = fig.add_subplot(111)

    # Generate initial heatmap with consistent color scaling
    heatmap_obj = ax.imshow(
        df_initial.values, cmap="viridis",
        vmin=global_min, vmax=global_max, aspect='auto',
        origin='lower',
        extent=[0.5, x_size + 0.5, 0.5, y_size + 0.5]
    )

    # Set axis labels
    ax.set_xlabel(x_label, fontsize=12, fontfamily=plot_font)
    ax.set_ylabel(y_label, fontsize=12, fontfamily=plot_font)

    # Set axis limits
    ax.set_xlim(0.5, x_size + 0.5)
    ax.set_ylim(0.5, y_size + 0.5)

    def generate_ticks(size):
        """
        Generates tick positions based on the size of the axis, limiting to a maximum of 15 ticks.

        Parameters:
            size (int): The size of the axis.

        Returns:
            list: A list of tick positions.
        """
        max_ticks = 15
        if size <= max_ticks:
            ticks = list(range(size))  # 0, 1, 2, ..., size-1
        else:
            step = size / float(max_ticks)
            ticks = [int(round(i * step)) for i in range(max_ticks)]
            # Ensure unique ticks and within bounds
            ticks = sorted(set(ticks))
            if ticks[-1] >= size:
                ticks[-1] = size - 1
        return ticks

    def set_axis_ticks():
        """
        Configures the ticks for both X and Y axes based on the data size, limiting to a maximum of 15 ticks.
        """
        # X-axis ticks
        x_ticks = generate_ticks(x_size)
        x_tick_labels = [str(i + 1) for i in x_ticks]
        x_ticks_centered = [i + 1 for i in x_ticks]  # Center ticks
        ax.set_xticks(x_ticks_centered)
        ax.set_xticklabels(x_tick_labels, rotation=45)

        # Y-axis ticks
        y_ticks = generate_ticks(y_size)
        y_tick_labels = [str(i + 1) for i in y_ticks]
        y_ticks_centered = [i + 1 for i in y_ticks]  # Center ticks
        ax.set_yticks(y_ticks_centered)
        ax.set_yticklabels(y_tick_labels)

    set_axis_ticks()

    # Set initial title
    ax.set_title("Distance Frame 0", fontsize=16, fontfamily=plot_font)

    # Add colorbar with label
    cbar = fig.colorbar(heatmap_obj, ax=ax)
    cbar.set_label('Distance (Å)', fontsize=12, fontfamily=plot_font)

    # Adjust layout to prevent label clipping
    fig.tight_layout()

    # --- Initialize the Main Application Window Using ttkbootstrap ---
    window = ttk.Window(themename="superhero")

    # Retrieve screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Set window dimensions based on figure size and additional space for controls
    window_width = fig_width_px + 20  # Additional space for borders and controls
    window_height = fig_height_px + 200  # Additional space for controls and padding
    window.geometry(f"{window_width}x{window_height}")

    window.title("Heatmap Viewer")
    logging.info("GUI created.")

    # Create a main frame to organize all GUI elements
    main_frame = ttk.Frame(window)
    main_frame.pack(fill=BOTH, expand=True)

    # Prevent the frame from resizing based on its content
    main_frame.pack_propagate(0)

    # Configure custom styles for widgets
    style = ttk.Style()
    style.configure('Custom.TLabel', foreground='white', font=(widget_font, 12, 'bold'))
    style.configure('Custom.TButton', font=(widget_font, 12, 'bold'))
    style.configure('Custom.Horizontal.TScale', font=(widget_font, 12))
    style.configure('Custom.TCombobox', font=(widget_font, 12))

    # -----------------------------------------------------------------------------
    # Plot Updating Functions
    # -----------------------------------------------------------------------------

    def update(val):
        """
        Updates the heatmap based on the selected frame.

        Parameters:
            val (str): The current value of the slider as a string.
        """
        frame = int(float(val))
        logging.info(f"Updating to frame: {frame}")
        # Validate frame index
        if frame < 0 or frame >= data.shape[0]:
            logging.warning(f"Frame {frame} is out of bounds.")
            return

        # Retrieve and reshape data for the selected frame
        data_row = data_subset.iloc[frame, :]
        matrix_data = data_row.values.reshape(y_size, x_size)
        df_new = pd.DataFrame(matrix_data)

        logging.debug(f"Updated matrix dimensions: {df_new.shape}")
        logging.debug(f"Updated matrix (Frame {frame}):\n{df_new}")

        # Update the heatmap data
        heatmap_obj.set_data(df_new.values)

        # Update the plot title
        ax.set_title(f"Distance Frame {frame}", fontsize=16, fontfamily=plot_font)

        # Redraw the canvas to reflect changes
        canvas.draw_idle()

    def update_cmap(event):
        """
        Updates the colormap of the heatmap based on user selection.

        Parameters:
            event: The event object (not used).
        """
        nonlocal current_cmap
        selected_cmap = cmap_combobox.get()
        current_cmap = selected_cmap
        logging.info(f"Colormap updated to: {current_cmap}")

        # Update the heatmap's colormap
        heatmap_obj.set_cmap(current_cmap)

        # Redraw the canvas to apply the new colormap
        canvas.draw_idle()

    # -----------------------------------------------------------------------------
    # Save Plot Function
    # -----------------------------------------------------------------------------

    def save_plot():
        """
        Opens a dialog to save the current heatmap plot with user-specified DPI and format.
        """
        # Create a modal save dialog window
        save_dialog = ttk.Toplevel(window)
        save_dialog.title("Save Plot")
        save_dialog.grab_set()  # Make this dialog modal

        # Label and entry for DPI input
        dpi_label = ttk.Label(
            save_dialog, text="Enter the quality (DPI) for saving:",
            font=(widget_font, 10), anchor='w'
        )
        dpi_label.pack(pady=(10, 0), padx=10)
        dpi_entry = ttk.Entry(save_dialog, font=(widget_font, 10))
        dpi_entry.pack(pady=(0, 10), padx=10)

        # Label and combobox for format selection
        format_label = ttk.Label(
            save_dialog, text="Select format:",
            font=(widget_font, 10), anchor='w'
        )
        format_label.pack(padx=10)
        formats = ['png', 'pdf', 'svg', 'jpg', 'tif']
        format_combobox = ttk.Combobox(
            save_dialog, values=formats, state="readonly",
            font=(widget_font, 10)
        )
        format_combobox.set(formats[0])  # Set default format
        format_combobox.pack(pady=(0, 10), padx=10)

        # Frame to contain Save and Cancel buttons
        button_frame = ttk.Frame(save_dialog)
        button_frame.pack(pady=(10, 10))

        def on_save():
            """
            Validates user input and saves the plot with specified DPI and format.
            """
            dpi_value = dpi_entry.get()
            selected_format = format_combobox.get()

            # Validate DPI input
            try:
                dpi = int(dpi_value)
                if dpi < 72 or dpi > 600:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid DPI", "Please enter a DPI value between 72 and 600.")
                logging.error("User entered invalid DPI value for saving plot.")
                return

            # Configure file types based on selected format
            filetypes = [(f"{selected_format.upper()} files", f"*.{selected_format}"), ("All files", "*.*")]
            defaultextension = f".{selected_format}"

            # Open save file dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=defaultextension,
                filetypes=filetypes,
                parent=save_dialog
            )
            if file_path:
                try:
                    # Determine figure size based on matrix symmetry
                    if x_size == y_size:
                        save_figsize = (6, 5)
                    else:
                        save_figsize = (6, 3)

                    # Create a new figure for saving
                    save_fig = Figure(figsize=save_figsize, dpi=fig_dpi)
                    save_ax = save_fig.add_subplot(111)

                    # Retrieve the current frame from the slider
                    frame = int(slider_ttk.get())
                    data_row = data_subset.iloc[frame, :]
                    matrix_data = data_row.values.reshape(y_size, x_size)
                    df_save = pd.DataFrame(matrix_data)

                    # Create the heatmap with the selected colormap
                    heatmap_save = save_ax.imshow(
                        df_save.values, cmap=current_cmap,
                        vmin=global_min, vmax=global_max, aspect='auto',
                        origin='lower',
                        extent=[0.5, x_size + 0.5, 0.5, y_size + 0.5]
                    )

                    # Set axis labels
                    save_ax.set_xlabel(x_label, fontsize=12, fontfamily=plot_font)
                    save_ax.set_ylabel(y_label, fontsize=12, fontfamily=plot_font)

                    # Set axis limits
                    save_ax.set_xlim(0.5, x_size + 0.5)
                    save_ax.set_ylim(0.5, y_size + 0.5)

                    def set_axis_ticks_for_save(ax):
                        """
                        Configures the ticks for the saved plot.

                        Parameters:
                            ax: The axis object to configure.
                        """
                        # X-axis ticks
                        x_ticks = generate_ticks(x_size)
                        x_tick_labels = [str(i + 1) for i in x_ticks]
                        x_ticks_centered = [i + 1 for i in x_ticks]  # Center ticks
                        ax.set_xticks(x_ticks_centered)
                        ax.set_xticklabels(x_tick_labels, rotation=45)

                        # Y-axis ticks
                        y_ticks = generate_ticks(y_size)
                        y_tick_labels = [str(i + 1) for i in y_ticks]
                        y_ticks_centered = [i + 1 for i in y_ticks]  # Center ticks
                        ax.set_yticks(y_ticks_centered)
                        ax.set_yticklabels(y_tick_labels)

                    set_axis_ticks_for_save(save_ax)

                    # Set plot title
                    save_ax.set_title(f"Distance Frame {frame}", fontsize=16, fontfamily=plot_font)

                    # Add colorbar
                    cbar = save_fig.colorbar(heatmap_save, ax=save_ax)
                    cbar.set_label('Distance (Å)', fontsize=12, fontfamily=plot_font)

                    # Adjust layout to prevent clipping
                    save_fig.tight_layout()

                    # Save the figure with the specified DPI and format
                    save_fig.savefig(file_path, dpi=dpi, format=selected_format, bbox_inches='tight')
                    logging.info(f"Plot saved to: {file_path} with DPI: {dpi} and format: {selected_format}")
                    messagebox.showinfo("Plot Saved", f"Plot successfully saved to:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error Saving", f"An error occurred while saving the plot: {e}")
                    logging.error(f"An error occurred while saving the plot: {e}")
                finally:
                    save_dialog.destroy()
            else:
                # User canceled the save dialog
                logging.info("User canceled the save plot dialog.")
                save_dialog.destroy()

        # Confirm and Cancel buttons
        save_button_control = ttk.Button(button_frame, text="Save", command=on_save)
        save_button_control.pack(side=LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=save_dialog.destroy)
        cancel_button.pack(side=LEFT, padx=5)

        # Center the save dialog over the main window
        save_dialog.transient(window)
        window.wait_window(save_dialog)

    # -----------------------------------------------------------------------------
    # GIF Creation Function
    # -----------------------------------------------------------------------------

    def create_gif():
        """
        Initiates the GIF creation process, allowing users to specify a range of frames.
        """
        # Prompt user for DPI
        dpi = simpledialog.askinteger(
            "Input DPI",
            "Enter the quality (DPI) for the images:",
            parent=window,
            minvalue=72,
            maxvalue=600
        )
        if dpi is None:
            # User canceled the DPI input
            logging.info("User canceled the DPI input for GIF creation.")
            return

        # Prompt user to enter start and end frames
        frame_range = frame_range_dialog()
        if frame_range is None:
            # User canceled the frame range input
            logging.info("User canceled the frame range selection for GIF creation.")
            return

        start_frame, end_frame = frame_range
        logging.info(f"User selected frame range: {start_frame} to {end_frame}")

        # Validate frame range
        if start_frame < 0 or end_frame >= data.shape[0] or start_frame > end_frame:
            messagebox.showerror(
                "Invalid Frame Range",
                f"Please enter a valid frame range between 0 and {data.shape[0] - 1}, "
                f"with start frame <= end frame."
            )
            logging.error("User entered an invalid frame range for GIF creation.")
            return

        # Ask user if they want to delete images after GIF creation
        delete_images = messagebox.askyesno(
            "Delete Images",
            "Do you want to delete the individual images after creating the GIF?"
        )
        logging.info(f"User chose to {'delete' if delete_images else 'keep'} individual images after GIF creation.")

        # Create Contacts/GIF directory if it doesn't exist
        contacts_dir = os.path.join(os.getcwd(), "Contacts")
        gif_dir = os.path.join(contacts_dir, "GIF")
        os.makedirs(gif_dir, exist_ok=True)  # Creates both Contacts and GIF directories if necessary
        logging.info(f"GIF directory set at: {gif_dir}")

        # Prepare list to hold image file paths
        image_files = []

        # Disable the Create Gif button to prevent multiple clicks
        create_gif_button.config(state='disabled')

        # Create a progress bar to indicate GIF creation progress
        progress = ttk.Progressbar(
            main_frame, orient='horizontal', mode='determinate',
            maximum=end_frame - start_frame + 1, length=400
        )
        progress.pack(pady=10)

        def process_frames():
            """
            Processes each selected frame: saves the image and updates the progress bar.
            Creates the GIF after processing all frames.
            """
            try:
                for idx, frame in enumerate(range(start_frame, end_frame + 1)):
                    # Update the slider to the current frame
                    slider_ttk.set(frame)
                    window.update_idletasks()

                    # Construct the filename for the current frame
                    image_filename = f"frame_{frame:04d}.png"
                    image_path = os.path.join(gif_dir, image_filename)

                    # Save the current frame as an image
                    fig.savefig(image_path, dpi=dpi, format='png', bbox_inches='tight')
                    image_files.append(image_path)
                    logging.debug(f"Saved frame {frame} as {image_path}")

                    # Update the progress bar
                    progress['value'] = idx + 1
                    window.update_idletasks()

                # Create GIF using imageio
                gif_path = os.path.join(gif_dir, "animation.gif")
                with imageio.get_writer(gif_path, mode='I', duration=0.5) as writer:
                    for image_file in image_files:
                        image = imageio.imread(image_file)
                        writer.append_data(image)
                logging.info(f"GIF created at: {gif_path}")

                messagebox.showinfo("GIF Created", f"GIF has been created at {gif_path}")
                logging.info(f"User notified of successful GIF creation at {gif_path}")

                # Delete images if the user chose to
                if delete_images:
                    for image_file in image_files:
                        os.remove(image_file)
                        logging.debug(f"Deleted image file: {image_file}")
                    messagebox.showinfo("Images Deleted", "Individual images have been deleted.")
                    logging.info("User notified of successful deletion of individual images.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                logging.error(f"An error occurred during GIF creation: {e}")
            finally:
                # Remove the progress bar and re-enable the button
                progress.destroy()
                create_gif_button.config(state='normal')
                logging.info("GIF creation process completed.")

        # Run the frame processing in a separate thread to keep the GUI responsive
        threading.Thread(target=process_frames).start()

    # -----------------------------------------------------------------------------
    # Frame Range Dialog Function
    # -----------------------------------------------------------------------------

    def frame_range_dialog():
        """
        Opens a dialog allowing the user to specify the start and end frames for GIF creation.

        Returns:
            tuple: A tuple containing the start and end frame indices as integers.
                   Returns None if the user cancels the dialog.
        """
        # Create a modal dialog window for frame range input
        range_dialog = ttk.Toplevel(window)
        range_dialog.title("Select Frame Range")
        range_dialog.grab_set()  # Make this dialog modal

        # Instruction label
        instruction_label = ttk.Label(
            range_dialog,
            text="Enter the start and end frames for the GIF:",
            font=(widget_font, 10),
            anchor='w'
        )
        instruction_label.pack(pady=(10, 5), padx=10)

        # Frame for start frame input
        start_frame_frame = ttk.Frame(range_dialog)
        start_frame_frame.pack(padx=10, pady=(0, 5), fill=X, expand=True)

        start_frame_label = ttk.Label(
            start_frame_frame,
            text="Start Frame:",
            font=(widget_font, 10),
            width=15,
            anchor='w'
        )
        start_frame_label.pack(side=LEFT)
        start_frame_entry = ttk.Entry(start_frame_frame, font=(widget_font, 10))
        start_frame_entry.pack(side=LEFT, fill=X, expand=True)

        # Frame for end frame input
        end_frame_frame = ttk.Frame(range_dialog)
        end_frame_frame.pack(padx=10, pady=(0, 10), fill=X, expand=True)

        end_frame_label = ttk.Label(
            end_frame_frame,
            text="End Frame:",
            font=(widget_font, 10),
            width=15,
            anchor='w'
        )
        end_frame_label.pack(side=LEFT)
        end_frame_entry = ttk.Entry(end_frame_frame, font=(widget_font, 10))
        end_frame_entry.pack(side=LEFT, fill=X, expand=True)

        # Frame to contain Confirm and Cancel buttons
        button_frame = ttk.Frame(range_dialog)
        button_frame.pack(pady=(0, 10))

        def on_confirm():
            """
            Retrieves the entered start and end frames, validates them, and closes the dialog.
            """
            start = start_frame_entry.get()
            end = end_frame_entry.get()

            try:
                start_int = int(start)
                end_int = int(end)
                if start_int < 0 or end_int >= data.shape[0]:
                    raise ValueError
                if start_int > end_int:
                    messagebox.showerror("Invalid Range", "Start frame must be less than or equal to end frame.")
                    logging.error("User entered a start frame greater than the end frame.")
                    return
            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    f"Please enter valid integer frame numbers between 0 and {data.shape[0] - 1}, "
                    f"with start frame <= end frame."
                )
                logging.error("User entered invalid frame numbers for GIF creation.")
                return

            # Store the result and close the dialog
            range_dialog.result = (start_int, end_int)
            logging.info(f"User confirmed frame range: {start_int} to {end_int}")
            range_dialog.destroy()

        def on_cancel():
            """
            Cancels the frame range input and closes the dialog.
            """
            range_dialog.result = None
            logging.info("User canceled the frame range selection dialog.")
            range_dialog.destroy()

        # Confirm and Cancel buttons
        confirm_button = ttk.Button(button_frame, text="Confirm", command=on_confirm)
        confirm_button.pack(side=LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
        cancel_button.pack(side=LEFT, padx=5)

        # Wait for the dialog window to close
        window.wait_window(range_dialog)

        # Retrieve the result
        return getattr(range_dialog, 'result', None)

    # -----------------------------------------------------------------------------
    # Window Closing Handler
    # -----------------------------------------------------------------------------

    def on_closing():
        """
        Handles the window closing event.
        Writes the execution completion to the log and shows a success message to the user.
        """
        logging.info("Heatmap Viewer application is closing.")
        messagebox.showinfo("Exit", "Execution completed successfully.")
        logging.info("Execution completed successfully.")
        logging.shutdown()
        window.destroy()

    # Bind the window close event to the on_closing function
    window.protocol("WM_DELETE_WINDOW", on_closing)

    # -----------------------------------------------------------------------------
    # Upper Section: Controls (Slider, Colormap Combobox, Save Button, Create Gif Button)
    # -----------------------------------------------------------------------------

    # Frame to contain control widgets
    control_frame = ttk.Frame(main_frame)
    control_frame.pack(side=TOP, fill=X, padx=10, pady=10)

    # Internal frame for the frame slider and its label
    slider_frame = ttk.Frame(control_frame)
    slider_frame.pack(side=LEFT, fill=X, expand=True)

    # Label for the frame slider
    slider_label = ttk.Label(slider_frame, text="Frame", style='Custom.TLabel')
    slider_label.pack(side=LEFT)

    # Slider to navigate through frames
    slider_ttk = ttk.Scale(
        slider_frame, from_=0, to=data.shape[0] - 1, orient='horizontal',
        length=200, command=update, style='Custom.Horizontal.TScale'
    )
    slider_ttk.pack(side=LEFT, fill=X, expand=True, padx=(5, 10))
    slider_ttk.set(initial_frame)  # Initialize slider position

    # Combobox for selecting colormap
    cmap_combobox = ttk.Combobox(
        control_frame, values=sorted(plt.colormaps()), state="readonly",
        font=(widget_font, 12), style='Custom.TCombobox'
    )
    cmap_combobox.set("viridis")  # Set default colormap
    current_cmap = "viridis"  # Variable to track current colormap
    cmap_combobox.pack(side=LEFT, padx=(0, 10))

    # Bind the colormap selection event to update_cmap function
    cmap_combobox.bind("<<ComboboxSelected>>", update_cmap)

    # Button to save the current plot
    save_button = ttk.Button(
        control_frame, text="Save Plot", command=save_plot, style='Custom.TButton'
    )
    save_button.pack(side=LEFT, padx=(0, 10))

    # Button to initiate GIF creation
    create_gif_button = ttk.Button(
        control_frame, text="Create Gif", command=create_gif, style='Custom.TButton'
    )
    create_gif_button.pack(side=LEFT, padx=(10, 0))

    # -----------------------------------------------------------------------------
    # Central Section: Heatmap Display
    # -----------------------------------------------------------------------------

    # Integrate the matplotlib figure into the Tkinter canvas
    canvas = FigureCanvasTkAgg(fig, master=main_frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()

    # Set the canvas size to match the figure dimensions
    canvas_widget.pack(side=TOP, fill=None, expand=False)
    canvas_widget.config(width=fig_width_px, height=fig_height_px)  # Adjust canvas size

    # Render the initial heatmap on the canvas
    canvas.draw()

    # Display the GUI window
    logging.info("Displaying the GUI.")
    window.mainloop()

if __name__ == "__main__":
    main()
