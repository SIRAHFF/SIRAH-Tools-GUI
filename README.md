
# SIRAH Tools Graphical User Interface
<p align="center">
<img src="https://github.com/user-attachments/assets/5c78e580-1502-4fb7-9890-caa6a3ecf9a7" alt="SIRAH-Tools-logo" width="75%" />
</p>

<br><br>

**Supported OS:** Primarily Linux, likely compatible with macOS, and limited functionality on Windows

## Introduction

**SIRAH-Tools-GUI** is a graphical user interface designed to streamline multiple analysis steps for molecular simulations carried out with the SIRAH force field. It consolidates several functionalities—from secondary structure analysis to contact mapping and backmapping—into a single, user-friendly platform, see [SIRAH Tools GUI documentation](https://sirahff.github.io/documentation/Tutorials%20sirahgui.html) for details.

Feedback and contributions are encouraged.

## Key Features

- **Loading and Managing Files:**  
  Easily load simulation trajectories.
  
- **Analysis of Secondary Structure (SS):**  
  Utilize built-in TCL scripts to classify and visualize secondary structure content. Generate SS profiles and time-series plots to understand conformational changes.
  
- **Contacts Analysis:**  
  Determine inter-residue and inter-molecular contacts during simulations.  
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
  - **macOS:** Expected to work normally but no tested.  
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


### Optional (Advised): Create an Alias

To simplify usage, add an alias in your shell configuration file (e.g., `~/.bashrc` or `~/.zshrc`):

  ```bash
  alias sirah-gui="conda activate sirah-gui && python /path/to/SIRAH-Tools-GUI/sirah-tools-gui.py"
  ```
Be sure to change /path/to/SIRAH-Tools-GUI/sirah-tools-gui.py to the right path on your computer. 

After reloading your shell, simply run:

 ```bash
  sirah-gui
 ```

## ⚠️ Known Issues and Limitations

### 1. VMD Shell Compatibility Issue

**SIRAH-Tools-GUI** relies on Tcl scripts that are invoked via **VMD** in text mode. However, VMD can be installed using either the **Bourne shell (`sh`)** or **C shell (`csh`)**, depending on the system environment and installation method. This poses a compatibility issue:  

SIRAH-Tools-GUI expects VMD to be installed using **Bourne shell (`sh`)**, and may fail if the `vmd` executable points to a **C shell** installation.

#### 🐛 Symptom

If you encounter the error shown in the figure below, it may be due to this shell mismatch.

![image](https://github.com/user-attachments/assets/fe58aa1b-0e64-44e5-84b1-22678bb244de)



#### 🔍 Check your VMD installation shell

To identify which shell your VMD installation uses, run the following command:

```bash
head -1 $(which vmd)
```

- If the output is:
  ```bash
  #!/bin/csh
  ```
  then your VMD uses **C shell** — ❌ incompatible

- If the output is:
  ```bash
  #!/bin/sh
  ```
  then your VMD uses **Bourne shell** — ✅ compatible.


#### 🛠 Solution: Force VMD installation with Bourne shell

If your current VMD installation uses `csh`, you can force a reinstallation with `sh` by temporarily disabling `csh`-based alternatives:

1. Configure VMD as usual:
   ```bash
   ./configure
   ```

2. Temporarily disable `csh` alternatives (as root):
   ```bash
   sudo chmod -x /bin/csh /bin/tcsh 2>/dev/null 
   ```

3. Proceed with installation:
   ```bash
   sudo make install
   ```

4. Restore shell permissions (optional but recommended):
   ```bash
   sudo chmod +x /bin/csh /bin/tcsh 2>/dev/null
   ```

> ⚠️ Note: The exact paths to shells may vary by distribution. Adjust `/bin/csh` and `/bin/tcsh` accordingly if they are located elsewhere on your system.

---

If needed, you can contact the developers or open an issue with a screenshot of your terminal and error logs to help troubleshoot further.


### 2. AMBER Tools on Windows (limitation):

Some analyses that rely on AMBER tools (e.g., LEaP or cpptraj) or ASCII-formatted (CRD) trajectories may not function as intended on Windows.


## 📑🧑‍💻   Contributors Guide

### Contributing to SIRAH-Tools-GUI

Thank you for your interest in contributing to **SIRAH-Tools-GUI**, a Python-based GUI toolkit for analysing and visualising coarse-grained molecular-dynamics trajectories with the SIRAH force field. This guide explains how to contribute effectively while keeping the codebase clean and maintainable.

---

### 🐞 Issues & Feature Requests — Start Here  ✅

Whether you are reporting a bug, proposing an enhancement, or planning a large new feature, **always open a new issue first** in the [GitHub Issue Tracker](https://github.com/SIRAHFF/SIRAH-Tools-GUI/issues). This allows the community and developers to:

- Confirm that the issue has not already been addressed.  
- Discuss design choices and possible approaches.  
- Coordinate efforts so work is not duplicated.  

> **Best practice:** For major modifications, describe your proposal in an issue _before_ writing code. This collaborative design step reduces re-work and makes it easier to align with the project’s standards.  
> After implementing your solution, submit a Pull Request (PR) referencing that issue. Even if you have push rights, opening a PR lets automated checks run and gives reviewers a clear change history before merging.

Please include in every issue:

- Operating system, Python version, and environment details.  
- Steps to reproduce the problem (if applicable).  
- Screenshots or full error messages for GUI or traceback errors.

---

### 🚀 Prerequisites

Before contributing, ensure that:

- You have working knowledge of **Python 3.9+**.  
- You are comfortable with Git and GitHub workflows.  
- You have installed all project dependencies.

We recommend Conda for environment management:

```bash
git clone https://github.com/SIRAHFF/SIRAH-Tools-GUI.git
cd SIRAH-Tools-GUI
conda env create -f environment.yml
conda activate sirah-gui
```

---

### 📁 Project Structure Overview

Take a moment to familiarise yourself with this structure before contributing.

The main source code is located in the root directory and includes:

- **GUI logic** in `sirah-tools-gui.py`, which initializes the interface and layout.
- **Modular tabs and utilities** in `modules/`, including:
  - `analysis_tab.py`, `ss_analysis.py`, `contacts_tab.py`, `load_files_tab.py`, `backmapping_tab.py`
  - `about_tab.py`, `utilities.py`, `utils.py`
- **Plotting scripts** in `modules/plots/`:
  - `plot_percentage.py`, `contacts_by_frame.py`, `matrix_contacts.py`, `native_contacts.py`, `ss_plot.py`
- **TCL scripts** in `TCL/` used for advanced molecular analysis in VMD:
  - `sirah_analysis.tcl`, `sirah_vmdtk.tcl`, `sirah_ss.tcl`, `contacts_distance.tcl`, `backmapping.tcl`
- **Images** and visual assets in `img/`:
  - `SIRAH-logo.png`, `sirahtools-logo.png`

```bash

  │   sirah-tools-gui.py
  ├───modules
  │   └───py files modules
  │   └───plots
  │           └───py files for plotting
  │───TCL
  │    └───tcl files for VMD
  │    
  │───img
  │    └───png logos

```

---

### 🛠️ How to Contribute

1. **Fork** the repository and clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/SIRAH-Tools-GUI.git
   cd SIRAH-Tools-GUI
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature-add-export-option
   ```

3. **Implement your changes**, keeping commits focused and modular.  
4. **Test** your contribution locally.  
5. **Commit** with a descriptive message:
   ```bash
   git commit -m "Add: export DPI and format options to Ramachandran plot"
   ```

6. **Push** your branch and open a **Pull Request**:
   ```bash
   git push origin feature-add-export-option
   ```

7. Reference the related issue in your PR description and provide a clear summary of your changes.

---

### 🧼 Code Style & Quality

We adhere strictly to [PEP 8](https://peps.python.org/pep-0008/) and [PEP 257](https://peps.python.org/pep-0257/).

- **Docstrings** are required for all public functions and classes.  
- Inline comments must clarify any complex logic.  

---

🧪 **Testing & Validation**

Although a formal test suite is not yet in place, please:

- Manually validate GUI behaviour and output.  
- Provide minimal example scripts or sample data when possible.  
- Test on multiple platforms (Linux, macOS, Windows) if feasible.

If you fix a bug, document how you verified the fix or include a reproducible test case.

---

### 🤝 Code of Conduct

All contributors are expected to behave respectfully. **SIRAH-Tools-GUI** is a collaborative academic project—help us maintain a welcoming, inclusive environment for everyone.

## 📜 License

By submitting code to this repository you agree that it be released under the **MIT License**, consistent with the rest of the project.

---

