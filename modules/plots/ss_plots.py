import argparse
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import seaborn as sns
import os
import sys
from tqdm import tqdm  # Ensure tqdm is installed: pip install tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def configure_plot():
    """
    Configures global matplotlib parameters with cross-platform font settings.
    """
    # List of alternative fonts
    available_fonts = ['Nimbus Sans', 'Arial', 'DejaVu Sans', 'Helvetica', 'Liberation Sans']
    # Select the first available font
    font_family = None
    for font in available_fonts:
        # Check if the font is available in the system fonts
        if any(font.lower() in f.lower() for f in mpl.font_manager.get_font_names()):
            font_family = font
            break
    if font_family is None:
        # Fallback to sans-serif if no specific font is available
        font_family = 'sans-serif'

    # Set matplotlib parameters
    mpl.rcParams['font.family'] = font_family
    mpl.rcParams['axes.labelsize'] = 14
    mpl.rcParams['xtick.labelsize'] = 14
    mpl.rcParams['ytick.labelsize'] = 14
    mpl.rcParams['legend.fontsize'] = 14


def create_legend_elements(has_H, has_E, has_C, H_col, E_col, C_col):
    """
    Creates legend elements based on the presence of H, E, C structures.
    """
    legend_elements = []
    if has_H:
        legend_elements.append(Line2D([0], [0], marker='s', color='w', label='H',
                                      markersize=12, markerfacecolor=H_col, markeredgecolor=H_col))
    if has_E:
        legend_elements.append(Line2D([0], [0], marker='s', color='w', label='E',
                                      markersize=12, markerfacecolor=E_col, markeredgecolor=E_col))
    if has_C:
        legend_elements.append(Line2D([0], [0], marker='s', color='w', label='C',
                                      markersize=12, markerfacecolor=C_col, markeredgecolor=C_col))
    return legend_elements


def plot_ss_data(filename, plot_type, dpi=300, tu='us', dt=1e-04,
                 H_col='darkviolet', E_col='yellow', C_col='aqua',
                 out='ss_mtx.png', width=10, height=8,
                 x_label_fontsize=14, y_label_fontsize=14,
                 y_num_major_ticks=10, x_num_major_ticks=10,
                 x_tick_size=12, y_tick_size=12, title=None,
                 title_size=16, y_max=None):
    """
    Plots secondary structure data from an input file.

    Parameters:
        filename (str): Input file name.
        plot_type (str): Type of plot: 'frame', 'res', or 'mtx'.
        dpi (int): DPI for saving the figure.
        tu (str): Time unit ('us' or 'ns').
        dt (float): Time between consecutive frames.
        H_col (str): Color for H structures.
        E_col (str): Color for E structures.
        C_col (str): Color for C structures.
        out (str): Output image file name.
        width (float): Width of the image in inches.
        height (float): Height of the image in inches.
        x_label_fontsize (int): Font size for x-axis labels.
        y_label_fontsize (int): Font size for y-axis labels.
        y_num_major_ticks (int): Number of major ticks on y-axis.
        x_num_major_ticks (int): Number of major ticks on x-axis.
        x_tick_size (int): Font size for x-axis ticks.
        y_tick_size (int): Font size for y-axis ticks.
        title (str): Title of the plot.
        title_size (int): Font size for the plot title.
        y_max (int): Maximum limit for y-axis.
    """
    configure_plot()

    # Validate and convert dt based on tu
    if tu == 'ns':
        dt /= 1000  # Convert dt from ns to us if necessary

    # Initialize figure and axes with specified size
    fig, ax = plt.subplots(figsize=(width, height))

    # Define total_steps for progress bar based on plot type
    total_steps = 10  # Approximate number of steps

    with tqdm(total=total_steps, desc="Processing", unit="step") as pbar:

        def setup_legend_and_colors(has_H, has_E, has_C):
            """
            Sets up colors and legend elements based on structure presence.
            """
            colors = []
            legend_elements = create_legend_elements(has_H, has_E, has_C, H_col, E_col, C_col)
            if has_H:
                colors.append(H_col)
            if has_E:
                colors.append(E_col)
            if has_C:
                colors.append(C_col)
            return colors, legend_elements

        try:
            if plot_type == 'frame':
                # Read the file using pandas
                data = pd.read_csv(filename, sep='\s+', skiprows=2, names=['frame', 'H(%)', 'E(%)', 'C(%)'])
                pbar.update(1)

                # Verify that the columns are present and not empty
                if data.empty or data.isnull().any().any():
                    raise ValueError(f"The file '{filename}' is empty or contains invalid data.")

                # Convert frames to time using `dt`
                data['frame'] *= dt
                pbar.set_description("Converted frame to time")
                pbar.update(1)

                # Check the presence of H, E, C structures
                has_H = data['H(%)'].sum() > 0
                has_E = data['E(%)'].sum() > 0
                has_C = data['C(%)'].sum() > 0

                # Set up dynamic colors and legend
                colors, legend_elements = setup_legend_and_colors(has_H, has_E, has_C)
                pbar.set_description("Setting up colors and legend elements")
                pbar.update(1)

                # Plot the lines for H, E, C
                if has_H:
                    ax.plot(data['frame'], data['H(%)'], label='H', linestyle='-', lw=1.0, color=H_col)
                if has_E:
                    ax.plot(data['frame'], data['E(%)'], label='E', linestyle='-', lw=1.0, color=E_col)
                if has_C:
                    ax.plot(data['frame'], data['C(%)'], label='C', linestyle='-', lw=1.0, color=C_col)
                pbar.update(1)

                # Adjust axis limits
                ax.set_xlim(data['frame'].min(), data['frame'].max())
                ax.set_ylim(0, 100 if y_max is None else y_max)
                pbar.set_description("Adjusting axis limits")
                pbar.update(1)

                # Set labels
                ax.set_xlabel('Time (μs)', fontsize=x_label_fontsize)
                ax.set_ylabel('Percentage (%)', fontsize=y_label_fontsize)

            elif plot_type == 'res':
                # Read the file using pandas
                data = pd.read_csv(filename, sep='\s+', skiprows=2, names=['ResidueNumber', 'H(%)', 'E(%)', 'C(%)'])
                pbar.update(1)

                # Verify that the columns are present and not empty
                if data.empty or data.isnull().any().any():
                    raise ValueError(f"The file '{filename}' is empty or contains invalid data.")

                # Check the presence of H, E, C structures
                has_H = data['H(%)'].sum() > 0
                has_E = data['E(%)'].sum() > 0
                has_C = data['C(%)'].sum() > 0

                # Set up dynamic colors and legend
                colors, legend_elements = setup_legend_and_colors(has_H, has_E, has_C)
                pbar.set_description("Setting up colors and legend elements")
                pbar.update(1)

                # Plot stacked bars for H, E, C
                bottom = pd.Series([0] * len(data))
                if has_H:
                    ax.bar(data['ResidueNumber'], data['H(%)'], label='H', color=H_col, bottom=bottom)
                    bottom += data['H(%)']

                if has_E:
                    ax.bar(data['ResidueNumber'], data['E(%)'], label='E', color=E_col, bottom=bottom)
                    bottom += data['E(%)']

                if has_C:
                    ax.bar(data['ResidueNumber'], data['C(%)'], label='C', color=C_col, bottom=bottom)
                pbar.update(1)

                # Adjust axis limits
                ax.set_xlim(data['ResidueNumber'].min(), data['ResidueNumber'].max())
                ax.set_ylim(0, 100 if y_max is None else y_max)
                pbar.set_description("Adjusting axis limits")
                pbar.update(1)

                # Set labels
                ax.set_xlabel('Residue Number', fontsize=x_label_fontsize)
                ax.set_ylabel('Percentage (%)', fontsize=y_label_fontsize)

            elif plot_type == 'mtx':
                try:
                    pbar.set_description("Reading ss.mtx data")
                    data = pd.read_csv(filename, sep='\s+', skiprows=1, header=None)
                    pbar.update(1)

                    # Adjust frame numbers to start from 0
                    data.iloc[:, 0] -= data.iloc[:, 0].min()

                    # Convert frames to time based on dt
                    data.iloc[:, 0] *= dt
                    pbar.set_description("Converted frame to time")
                    pbar.update(1)

                    # Map 'H', 'E', 'C' to numerical values
                    structure_mapping = {'H': 1, 'E': 2, 'C': 3}
                    data.replace(structure_mapping, inplace=True)
                    pbar.set_description("Processing data")
                    pbar.update(1)

                    # Set the first column (time) as index
                    data.set_index(0, inplace=True)
                    pbar.update(1)

                    # Check presence of structures
                    structures_present = set(data.values.flatten())
                    colors = []
                    legend_elements = []

                    for struct, value in structure_mapping.items():
                        if value in structures_present:
                            color = {'H': H_col, 'E': E_col, 'C': C_col}[struct]
                            colors.append(color)
                            legend_elements.append(Line2D([0], [0], marker='s', color='w', label=struct,
                                                          markersize=12, markerfacecolor=color, markeredgecolor=color))

                    pbar.set_description("Setting up colors and legend elements")
                    pbar.update(1)

                    # Create the color map with correct mapping
                    cmap = mpl.colors.ListedColormap(colors)
                    bounds = [val - 0.5 for val in sorted(structure_mapping.values()) if val in structures_present]
                    bounds.append(max(structures_present) + 0.5)
                    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
                    pbar.update(1)

                    # Transpose the DataFrame for heatmap
                    data_transposed = data.transpose()
                    pbar.set_description("Transposing data for heatmap")
                    pbar.update(1)

                    # Plot the heatmap
                    pbar.set_description("Generating heatmap visualization")
                    sns.heatmap(data_transposed, cmap=cmap, norm=norm, cbar=False, ax=ax)
                    pbar.update(1)

                    # Set the time unit based on 'tu'
                    time_unit = 'μs' if tu == 'us' else 'ns'

                    # Set X-axis ticks and labels based on actual time data
                    time_values = data.index.values
                    x_tick_positions = np.linspace(0, len(time_values) - 1, x_num_major_ticks)
                    x_tick_labels = [f"{time_values[int(pos)]:.2f}" for pos in x_tick_positions]
                    ax.set_xticks(x_tick_positions)
                    ax.set_xticklabels(x_tick_labels, rotation=0)
                    pbar.set_description("Configuring X-axis ticks and labels")
                    pbar.update(1)

                    # Set Y-axis ticks and labels
                    num_residues = data_transposed.shape[0]
                    y_tick_positions = np.linspace(0, num_residues - 1, y_num_major_ticks)
                    y_tick_labels = [f"{int(y)}" for y in np.linspace(1, num_residues, y_num_major_ticks)]
                    ax.set_yticks(y_tick_positions)
                    ax.set_yticklabels(y_tick_labels)
                    ax.tick_params(axis='y', direction='out', labelsize=y_tick_size)
                    ax.tick_params(axis='x', direction='out', labelsize=x_tick_size)
                    pbar.set_description("Configuring Y-axis ticks and labels")
                    pbar.update(1)

                    ax.invert_yaxis()

                    # Set labels
                    ax.set_xlabel(f'Time ({time_unit})', fontsize=x_label_fontsize)
                    ax.set_ylabel('Residue', fontsize=y_label_fontsize)

                except Exception as e:
                    logging.error(f"Error processing 'mtx' plot: {e}")
                    sys.exit(1)

            else:
                logging.error(f"Error: Unsupported plot type '{plot_type}'.")
                sys.exit(1)

            # Configure tick parameters
            ax.tick_params(axis='x', labelsize=x_tick_size)
            ax.tick_params(axis='y', labelsize=y_tick_size, rotation=0)
            pbar.set_description("Configuring tick label sizes")
            pbar.update(1)

            # Set plot title if provided
            if title is not None:
                ax.set_title(title, fontsize=title_size)
                pbar.set_description("Adding plot title")
                pbar.update(1)

            # Configure major tick locators
            ax.locator_params(axis='y', nbins=y_num_major_ticks)
            ax.locator_params(axis='x', nbins=x_num_major_ticks)
            pbar.set_description("Configuring major tick locators")
            pbar.update(1)

            # Add legend
            if legend_elements:
                ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
            pbar.set_description("Adding legend")
            pbar.update(1)

            # Adjust layout to prevent overlaps
            fig.tight_layout()

            # Save the figure with specified DPI and adjusted layout
            fig.savefig(out, dpi=dpi, bbox_inches='tight')
            pbar.set_description(f"Saving the plot as {out}")
            pbar.update(1)

            # Display the figure
            plt.show()
            pbar.set_description("Displaying the plot")
            pbar.update(1)

        except Exception as e:
            logging.error(f"Error processing plot: {e}")
            sys.exit(1)


def main():
    """
    Main function to parse arguments and invoke the plotting function.
    """
    parser = argparse.ArgumentParser(
        description='Create a PNG image from an input file (ss.mtx, ss_by_frame.xvg, or ss_by_res.xvg).')
    parser.add_argument('-t', dest='plot_type', metavar='[type]', type=str, default=None,
                        help='Type of plot: frame, res, or mtx')
    parser.add_argument('-i', dest='filename', metavar='[input]', type=str, required=True, help='Input file name')
    parser.add_argument('-d', dest='dpi', metavar='[dpi]', type=int, default=300,
                        help='DPI for saving the figure (default: 300)')
    parser.add_argument('-tu', dest='tu', metavar='[tu]', type=str, choices=['us', 'ns'], default='us',
                        help='Time unit (us or ns) (default: us)')
    parser.add_argument('-dt', dest='dt', metavar='[dt]', type=float, default=1e-04,
                        help='Time between consecutive frames (default: 1e-04)')
    parser.add_argument('-H', dest='H_col', metavar='[helix-color]', type=str, default='darkviolet',
                        help='Alpha-helix color (default: darkviolet)')
    parser.add_argument('-E', dest='E_col', metavar='[beta-sheet color]', type=str, default='yellow',
                        help='Beta-sheet color (default: yellow)')
    parser.add_argument('-C', dest='C_col', metavar='[coil color]', type=str, default='aqua',
                        help='Coil color (default: aqua)')
    parser.add_argument('-o', dest='out', metavar='[out name]', type=str, default=None, help='Image output name')
    parser.add_argument('-wt', dest='width', metavar='[width]', type=float, default=10,
                        help='Image width (inches) (default: 10)')
    parser.add_argument('-ht', dest='height', metavar='[height]', type=float, default=8,
                        help='Image height (inches) (default: 8)')
    parser.add_argument('-xfs', dest='x_label_fontsize', metavar='[xlab fontsize]', type=int, default=14,
                        help='Font size for x-axis labels')
    parser.add_argument('-yfs', dest='y_label_fontsize', metavar='[ylab fontsize]', type=int, default=14,
                        help='Font size for y-axis labels')
    parser.add_argument('-yticks', dest='y_num_major_ticks', metavar='[y # ticks]', type=int, default=10,
                        help='Number of major tick locators on the y-axis')
    parser.add_argument('-xticks', dest='x_num_major_ticks', metavar='[x # ticks]', type=int, default=10,
                        help='Number of major tick locators on the x-axis')
    parser.add_argument('-xtsize', dest='x_tick_size', metavar='[xtsize]', type=int, default=12,
                        help='Font size for x-axis ticks')
    parser.add_argument('-ytsize', dest='y_tick_size', metavar='[ytsize]', type=int, default=12,
                        help='Font size for y-axis ticks')
    parser.add_argument('-title', dest='title', metavar='[title]', type=str, default=None, help='Title of the plot')
    parser.add_argument('-ttsize', dest='title_size', metavar='[title_size]', type=int, default=16,
                        help='Size of the plot title')
    parser.add_argument('--ymax', dest='y_max', metavar='[y_max]', type=int, help='Maximum limit for y-axis')
    parser.add_argument('--version', action='store_true', help='Print version and exit')

    args = parser.parse_args()

    if args.version:
        print("Version 1.2 [December 2024]")
        sys.exit(0)

    if args.out is None:
        input_filename = os.path.splitext(args.filename)[0]
        args.out = input_filename + '.png'

    # Determine plot type if not specified
    if args.plot_type is None:
        if args.filename == "ss_by_frame.xvg":
            args.plot_type = 'frame'
        elif args.filename == "ss_by_res.xvg":
            args.plot_type = 'res'
        elif args.filename == "ss.mtx":
            args.plot_type = 'mtx'
        else:
            logging.error("Error: Please provide a valid plot type (-t frame/res/mtx) or a supported input file.")
            sys.exit(1)
    else:
        if args.plot_type not in ['frame', 'res', 'mtx']:
            logging.error("Error: Plot type must be one of 'frame', 'res', or 'mtx'.")
            sys.exit(1)

    # Validate that the file exists
    if not os.path.isfile(args.filename):
        logging.error(f"Error: The file '{args.filename}' does not exist.")
        sys.exit(1)

    # Call the plotting function with provided arguments
    plot_ss_data(
        filename=args.filename,
        plot_type=args.plot_type,
        dpi=args.dpi,
        tu=args.tu,
        dt=args.dt,
        H_col=args.H_col,
        E_col=args.E_col,
        C_col=args.C_col,
        out=args.out,
        width=args.width,
        height=args.height,
        x_label_fontsize=args.x_label_fontsize,
        y_label_fontsize=args.y_label_fontsize,
        y_num_major_ticks=args.y_num_major_ticks,
        x_num_major_ticks=args.x_num_major_ticks,
        x_tick_size=args.x_tick_size,
        y_tick_size=args.y_tick_size,
        title=args.title,
        title_size=args.title_size,
        y_max=args.y_max
    )


if __name__ == '__main__':
    main()
