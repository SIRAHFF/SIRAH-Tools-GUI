# ss_analysis.tcl
#
# This TCL script Performs secondary structure (SS) analysis using VMD.
#                 Loads molecular topology and trajectory files,
#                 executes SS analysis, and optionally calculates Psi/Phi angles.
#
# Usage:

# vmd -dispdev text -e path/sirah_analysis.tcl -args topology_file
#                                                    trajectory_file
#                                                    first
#                                                    last
#                                                    selection
#                                                    each
#                                                    ramach
#                                                    sirah_tcl_path
#                                                    ss_dir
#                                                    byframe
#                                                    byres
#                                                    global_out
#                                                    mtx
#                                                    psi
#                                                    phi


# 1. topology         - Path to the topology file.
# 2. trajectory       - Path to the trajectory file. 
# 3. first            - Index of the first frame to analyze
# 4. last             - Index of the last frame to analyze (-1 for all frames)
# 5. selection        - Atom selection using VMD syntax
# 6. each             - Step size between frames to analyze
# 7. ramach           - Flag indicating whether to calculate Psi/Phi angles (1 for yes, 0 for no)
# 8. sirah_tcl_path   - Path to the sirah_vmdtk.tcl script
# 9. ss_dir           - Directory where secondary structure (SS) output files will be saved
# 10. byframe         - Output filename for per-frame SS data
# 11. byres           - Output filename for per-residue SS data
# 12. global_out      - Output filename for global SS data
# 13. mtx             - Output filename for the SS matrix
# 15. psi             - Output filename for Psi angles (used if ramach is 1)
# 16. phi             - Output filename for Phi angles (used if ramach is 1)

# Authors: Andres Ballesteros & Lucianna Silva Dos Santos
# =================================================================================================

puts ""
puts ""
puts "╔═════════════════════════════════════════════════════╗"
puts "║           SECONDARY STRUCTURE ANALYSIS              ║"
puts "╚═════════════════════════════════════════════════════╝"
puts ""
puts "Starting Secondary estructure analysis..."
puts ""

# Print the number of received arguments and their values for debugging
puts ""
puts "---------------------------------------------"
puts "Number of received arguments: [llength $argv]"
puts "---------------------------------------------"
puts ""


# Check if the number of arguments is less than 15
if {[llength $argv] < 15} {
    # Display usage instructions if insufficient arguments are provided
    puts "Usage: $argv0 topology trajectory First Last selection Each ramach script_dir output_dir byframe byres global mtx psi phi"
    exit 1
}

puts ""
puts "Received arguments: "
puts "-----------------------------------------------------------------------------------------------------------"
# Assign each command-line argument to a corresponding variable
set topology   [lindex $argv 0]   ;# Path to the molecular topology file (e.g., PDB file)
set trajectory [lindex $argv 1]   ;# Path to the molecular trajectory file (e.g., DCD or XTC file)
set first      [lindex $argv 2]   ;# Index of the first frame to analyze
set last       [lindex $argv 3]   ;# Index of the last frame to analyze (-1 for all frames)
set selection  [lindex $argv 4]   ;# Atom selection string defining which atoms to include in the analysis
set each       [lindex $argv 5]   ;# Step size between frames to analyze
set ramach     [lindex $argv 6]   ;# Flag indicating whether to calculate Psi/Phi angles (1 for yes, 0 for no)
set script_dir [lindex $argv 7]   ;# Directory path where the 'sirah_vmdtk.tcl' script is located
set output_dir [lindex $argv 8]   ;# Directory path where the analysis results will be saved
set byframe    [lindex $argv 9]   ;# Output filename for per-frame SS data
set byres      [lindex $argv 10]  ;# Output filename for per-residue SS data
set global_out [lindex $argv 11]  ;# Output filename for global SS data
set mtx        [lindex $argv 12]  ;# Output filename for the SS matrix
set psi        [lindex $argv 13]  ;# Output filename for Psi angles (used if ramach is 1)
set phi        [lindex $argv 14]  ;# Output filename for Phi angles (used if ramach is 1)
puts "-----------------------------------------------------------------------------------------------------------"
puts ""

# Display the script and output directories for confirmation
puts ""
puts "Script directory: "
puts "-----------------------------------------------------------------------------------------------------------"
puts "$script_dir"
puts "-----------------------------------------------------------------------------------------------------------"
puts ""
puts "Output directory: "
puts "-----------------------------------------------------------------------------------------------------------"
puts "$output_dir"
puts "-----------------------------------------------------------------------------------------------------------"
puts ""

# Construct the path to the 'sirah_vmdtk.tcl' script
set vmdtk_path [file join $script_dir "sirah_vmdtk.tcl"]
puts ""
puts "Loading sirah_vmdtk.tcl from: "
puts "-----------------------------------------------------------------------------------------------------------"
puts "$vmdtk_path"
puts "-----------------------------------------------------------------------------------------------------------"
puts ""

# Source (load) the 'sirah_vmdtk.tcl' script to make its procedures and commands available
source $vmdtk_path
puts "-----------------------------------------------------------------------------------------------------------"
puts ""

# Load the molecular topology file into VMD
puts ""
puts "Loading topology file:" 
puts "---------------------------------------------------------------------------------------------"
puts "$topology"
puts "---------------------------------------------------------------------------------------------"
puts ""
mol new $topology waitfor all

# Load the molecular trajectory file into VMD, specifying frame range and step size
puts "Loading trajectory file: "
puts "---------------------------------------------------------------------------------------------"
puts "$trajectory"
puts "---------------------------------------------------------------------------------------------"
puts ""
puts "This may take a few minutes.........."
puts "Loading.............................."
puts ""
puts ""
mol addfile $trajectory first 0 last -1 step $each waitfor all
puts ""
puts ""
puts "Trajectory loaded successfully"
puts "---------------------------------------------------------------------------------------------"
puts ""
puts ""

# If the 'last' parameter is set to -1, determine the total number of frames and set 'last' accordingly
if {$last == "-1"} {
    set num_frames [molinfo top get numframes]
    set last [expr {$num_frames}]
    puts ""
    puts "Last frame set to: $last"
    puts ""
}

# Initialize the list of output filenames for various SS data categories
set outname_list [list byframe $byframe byres $byres global $global_out mtx $mtx]

# If 'ramach' is enabled, append Psi and Phi output filenames to the output list
if {$ramach == "1"} {
    lappend outname_list psi $psi phi $phi
}

# Display the SS analysis command that will be executed
puts ""
puts "Executing: "
puts "sirah_ss sel \"$selection\" first $first last $last outname $outname_list"
puts ""

# Execute the SS analysis based on the value of 'ramach'
if {$ramach == "0"} {
    # Execute without Psi/Phi calculations
    sirah_ss sel "$selection" first $first last $last outname $outname_list
} elseif {$ramach == "1"} {
    # Execute with Psi/Phi calculations
    sirah_ss sel "$selection" first $first last $last ramach outname $outname_list
} else {
    # Handle invalid 'ramach' values
    puts "Error: Invalid value for ramach."
    exit 1
}


puts ""
puts ""
puts "╔═════════════════════════════════════════════════════╗"
puts "║          END SECONDARY STRUCTURE ANALYSIS           ║"
puts "╚═════════════════════════════════════════════════════╝"
puts ""
puts ""

exit 1
quit

