import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import webbrowser
from pathlib import Path
from typing import List, Tuple, Optional


class AboutTab:
    """
    A class to create and manage the 'About' tab in the SIRAH Tools GUI.
    This tab includes scrollable text content with hyperlinks and a resizable logo image.
    """

    # Configuration constants
    SCALING_FACTOR: float = 1.2
    MAIN_PADDING: int = 10
    TITLE_FONT: Tuple[str, int, str] = ("Segoe UI", 16, "bold")
    TITLE_COLOR: str = "#778899"
    CONTENT_FONT: Tuple[str, int] = ("Segoe UI", 12)
    HYPERLINK_COLOR: str = "#00BFFF"
    IMAGE_RELATIVE_PATH: str = "img/SIRAH-logo.png"
    IMAGE_DELAY_MS: int = 500  # Delay in milliseconds before initial image resize

    def __init__(self, parent: ttk.Frame, state: Optional[dict] = None):
        """
        Initializes the AboutTab instance.

        Args:
            parent (ttk.Frame): The parent tab where the content will be placed.
            state (Optional[dict]): The application state.
        """
        self.parent = parent
        self.state = state
        self.original_image: Optional[Image.Image] = None
        self.img_photo_resized: Optional[ImageTk.PhotoImage] = None

        # Initialize the 'About' tab UI components
        self.setup_scaling()
        self.create_main_frame()
        self.create_scrollable_content()
        self.create_title_label()
        self.create_text_widget()
        self.insert_content()
        self.add_hyperlinks()
        self.create_image_section()

    def setup_scaling(self) -> None:
        """
        Configures the scaling for high-DPI displays.
        """
        self.parent.master.tk.call('tk', 'scaling', self.SCALING_FACTOR)

    def create_main_frame(self) -> None:
        """
        Creates the main frame within the tab with padding.
        """
        self.main_frame = ttk.Frame(self.parent, padding=self.MAIN_PADDING)
        self.main_frame.pack(fill="both", expand=True)

    def create_scrollable_content(self) -> None:
        """
        Creates a scrollable canvas and scrollbar for the tab's content.
        """
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create scrollable frame inside the canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create a window inside the canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Adjust the size of the canvas to make the text area larger
        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        self.scrollbar.pack(side="right", fill="y")

    def create_title_label(self) -> None:
        """
        Creates and packs the title label.
        """
        self.title_label = ttk.Label(
            self.scrollable_frame,
            text="SIRAH TOOLS GUI",
            font=self.TITLE_FONT,
            foreground=self.TITLE_COLOR,
            anchor="center"
        )
        self.title_label.pack(pady=(10, 15), anchor="center")

    def create_text_widget(self) -> None:
        """
        Creates and packs the Text widget for main content.
        """
        # Create text widget inside the scrollable frame with larger height and width
        self.text_widget = tk.Text(
            self.scrollable_frame,
            wrap="word",
            font=self.CONTENT_FONT,
            bg="white",
            bd=0,
            relief="flat",
            fg="black",
            state="normal",
            height=30,  # Adjust the height to show more lines initially
            width=100  # Adjust the width to show more characters per line
        )
        self.text_widget.pack(fill="both", expand=True)

    def insert_content(self) -> None:
        """
        Inserts predefined content into the Text widget.
        """
        content = """Welcome to the SIRAH Tools GUI, an easy-to-use graphical user interface tool created to make it easier 
to fully analyze SIRAH coarse-grained molecular dynamics (MD) simulations. With this tool,
you can load topology and trajectory files from AMBER, GROMACS, or NAMD and perform both basic and advanced analyses, 
including RMSD, RMSF, native contacts, secondary structure analysis, and more.
Enjoy a streamlined experience with visualization and reporting features tailored to your MD analysis needs.

Visit our website: sirahff.com

This tool was developed by the SIRAH Developers Team to assist researchers in their MD simulations.
For support, suggestions, or further information, please visit our website or contact our support team.

You can review the SIRAH documentation at: https://sirahff.github.io/documentation/

And the SIRAH Tools documentation at: https://sirahff.github.io/documentation/Tutorials%20sirahtools.html


This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.  

"""
        self.text_widget.insert("1.0", content)
        self.text_widget.configure(state="disabled")  # Make the Text widget read-only

    def add_hyperlinks(self) -> None:
        """
        Searches for predefined hyperlinks in the Text widget and binds them to open in the web browser.
        """
        # Define hyperlinks as tuples of (display_text, url)
        self.hyperlinks: List[Tuple[str, str]] = [
            ("sirahff.com", "http://sirahff.com"),
            ("https://sirahff.github.io/documentation/", "https://sirahff.github.io/documentation/"),
            ("https://sirahff.github.io/documentation/Tutorials%20sirahtools.html", "https://sirahff.github.io/documentation/Tutorials%20sirahtools.html"),
            ("https://www.gnu.org/licenses/", "https://www.gnu.org/licenses/")
        ]

        # Enable Text widget to be editable temporarily for tagging
        self.text_widget.configure(state="normal")

        for link_text, url in self.hyperlinks:
            self.tag_hyperlink(link_text, url)

        # Re-disable the Text widget to make it read-only
        self.text_widget.configure(state="disabled")

    def tag_hyperlink(self, link_text: str, url: str) -> None:
        """
        Finds all occurrences of link_text in the Text widget and tags them as hyperlinks.

        Args:
            link_text (str): The text to be converted into a hyperlink.
            url (str): The URL that the hyperlink points to.
        """
        start_idx = "1.0"
        while True:
            pos = self.text_widget.search(link_text, start_idx, stopindex="end")
            if not pos:
                break
            end_pos = f"{pos}+{len(link_text)}c"

            # Create a unique tag name based on position to avoid conflicts
            tag_name = f"hyperlink_{pos}"
            self.text_widget.tag_add(tag_name, pos, end_pos)
            self.text_widget.tag_config(
                tag_name,
                foreground=self.HYPERLINK_COLOR,
                underline=True
            )
            self.text_widget.tag_bind(tag_name, "<Enter>", self.on_enter)
            self.text_widget.tag_bind(tag_name, "<Leave>", self.on_leave)
            self.text_widget.tag_bind(tag_name, "<Button-1>", lambda e, url=url: self.open_url(e, url))

            start_idx = end_pos  # Move past the current match

    def on_enter(self, event: tk.Event) -> None:
        """
        Changes the cursor to a pointing hand when hovering over a hyperlink.

        Args:
            event (tk.Event): The event that triggered the function.
        """
        self.text_widget.config(cursor="hand2")

    def on_leave(self, event: tk.Event) -> None:
        """
        Reverts the cursor back to default when not hovering over a hyperlink.

        Args:
            event (tk.Event): The event that triggered the function.
        """
        self.text_widget.config(cursor="")

    def open_url(self, event: tk.Event, url: str) -> None:
        """
        Opens the specified URL in the default web browser.

        Args:
            event (tk.Event): The event that triggered the function.
            url (str): The URL to be opened.
        """
        webbrowser.open_new(url)

    def create_image_section(self) -> None:
        """
        Creates the image/logo section with rescaling functionality.
        """
        self.img_frame = ttk.Frame(self.scrollable_frame)
        self.img_frame.pack(pady=(20, 10), fill="both", expand=True, anchor="center")

        img_path = Path(__file__).resolve().parent.parent / self.IMAGE_RELATIVE_PATH

        if not img_path.exists():
            messagebox.showerror("Image Error", f"Image not found at: {img_path}")
            return

        try:
            self.original_image = Image.open(img_path)
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            return

        self.img_canvas = tk.Canvas(self.img_frame, bg="white")
        self.img_canvas.pack(expand=True, fill="both")

        # Bind the resize event
        self.img_canvas.bind("<Configure>", self.resize_image)

        # Schedule the initial resize
        self.img_canvas.after(self.IMAGE_DELAY_MS, self.resize_image)

    def resize_image(self, event: Optional[tk.Event] = None) -> None:
        """
        Resizes the image to fit within the canvas while maintaining aspect ratio.

        Args:
            event (Optional[tk.Event]): The event that triggers resizing (usually window resize).
        """
        if not self.original_image:
            return

        canvas_width = event.width if event else self.img_canvas.winfo_width()
        canvas_height = event.height if event else self.img_canvas.winfo_height()

        if canvas_width <= 0 or canvas_height <= 0:
            return

        img_ratio = self.original_image.width / self.original_image.height
        canvas_ratio = canvas_width / canvas_height

        if canvas_ratio > img_ratio:
            new_height = canvas_height
            new_width = int(new_height * img_ratio)
        else:
            new_width = int(canvas_width * 0.7)  # Adjust as needed for better fit
            new_height = int(new_width / img_ratio)

        if new_width > 0 and new_height > 0:
            # Determine the appropriate resampling filter based on Pillow version
            resampling_filter = getattr(Image, 'Resampling', Image).LANCZOS

            resized_image = self.original_image.resize((new_width, new_height), resampling_filter)
            self.img_photo_resized = ImageTk.PhotoImage(resized_image)

            self.img_canvas.delete("all")
            self.img_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.img_photo_resized,
                anchor="center"
            )
            self.img_canvas.image = self.img_photo_resized  # Prevent garbage collection


def create_about_tab(tab: ttk.Frame, state: Optional[dict] = None) -> None:
    """
    Initializes the AboutTab class to create the 'About' tab.

    Args:
        tab (ttk.Frame): The parent tab where the content will be placed.
        state (Optional[dict]): The application state.

    Returns:
        None
    """
    AboutTab(parent=tab, state=state)
