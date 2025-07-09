import tkinter as tk

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
