
# SIRAH Tools Graphical User Interface (Beta Version)

<p align="center">
<img src="https://github.com/user-attachments/assets/5c78e580-1502-4fb7-9890-caa6a3ecf9a7" alt="SIRAH-Tools-logo" width="75%" />
</p>

<br><br>

**Status:** Beta  
**Supported OS:** Primarily Linux, likely compatible with macOS, and limited functionality on Windows

## Introduction

**SIRAH-Tools-GUI** is a graphical user interface designed to streamline multiple analysis steps for molecular simulations carried out with the SIRAH force field. It consolidates several functionalities—from secondary structure analysis to contact mapping and backmapping—into a single, user-friendly platform.

This application is still in **beta** testing, meaning that while many features are functional, you may encounter some limitations or bugs. Feedback and contributions are encouraged.

## Key Features

- **Loading and Managing Files:**  
  Easily load simulation trajectories.
  
- **Analysis of Secondary Structure (SS):**  
  Utilize built-in TCL scripts to classify and visualize secondary structure content. Generate SS profiles and time-series plots to understand conformational changes.
  
- **Contacts Analysis:**  
  Determine inter-residue and inter-molecular contacts during simulations via `contacts_distance.tcl`.  
  - **Contact Maps and Matrices:** Generate 2D matrices to visualize residue contacts over time.  
  - **Contacts by Frame:** Track how contacts evolve frame-by-frame.
  
- **Backmapping:**  
  Reconstruct all-atom structures from coarse-grained (CG) simulations. This feature simplifies the transition from CG to atomistic representations.
  
- **General Analysis Tools:**  
  A suite of utilities are available for quick access to common analysis methods (RMSD, RMSF, SASA, Rg, RDF).
  
- **Plots and Figures:**  
  Easily create a variety of plots (e.g., percentage of SS elements, native contacts, contact matrices).   
  Export high-quality figures (PNG, PDF) for publications or presentations.
  
- **Integration with VMD:**  
  The application leverages TCL scripts that work seamlessly with VMD, enabling advanced visualization and analysis.

## System Requirements

- **Operating System:**  
  - **Linux:** Fully supported.  
  - **macOS:** Expected to work normally.  
  - **Windows:** Some functionalities (especially AMBER-related tasks and ASCII-formatted trajectory processing) may be limited.

- **Dependencies:**  
  All Python dependencies are included in `env_sirah_tools.yml`. You will need Conda to create and manage the environment.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/SIRAHFF/SIRAH-Tools-GUI.git
   ```

   ```bash
    cd SIRAH-Tools-GUI/
    ```

   ```bash
   unzip SIRAH-Tools-GUI_v1.0.zip
    ```   
   
   ```bash
   cd SIRAH-Tools-GUI_v1.0/
   ```

1. **Create the Conda Environment:**
   ```bash
   conda env create -f env_sirah_tools.yml
   ```

2. **Activate the Environment:**
   ```bash
   conda activate sirah-gui

3. **Run the aplication:**
   ```bash
   python sirah-tools-gui.py
   ```

The GUI should launch, allowing you to access all the features.


## Optional (Advised): Create an Alias

To simplify usage, add an alias in your shell configuration file (e.g., `~/.bashrc` or `~/.zshrc`):

  ```bash
  alias sirah-gui="conda activate sirah-gui && python /path/to/SIRAH-Tools-GUI/sirah-tools-gui.py"
  ```
Be sure to change /path/to/SIRAH-Tools-GUI/sirah-tools-gui.py to the right path on your computer. 

After reloading your shell, simply run:

 ```bash
  sirah-gui
 ```

## Known Limitations

**AMBER Tools on Windows:**
Some analyses that rely on AMBER tools (e.g., LEaP or cpptraj) or ASCII-formatted (CRD) trajectories may not function as intended on Windows.

**Beta Status:**
As this is a beta release, stability is not fully guaranteed. Please report issues or bugs via GitHub Issues.

## Contributing

**Contributions are welcome!**
If you have suggestions, find bugs, or wish to contribute code, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
